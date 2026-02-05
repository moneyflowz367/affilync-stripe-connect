"""
Dashboard API Routes for Stripe Connect
Provides endpoints for the standalone dashboard UI
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import StripeConnectedAccount, TrackedPayment, StripeWebhookLog
from app.services.account_service import AccountService
from app.services.stripe_client import StripeClient

logger = logging.getLogger(__name__)

router = APIRouter()


# ============== Request/Response Models ==============


class AccountResponse(BaseModel):
    id: UUID
    stripe_account_id: str
    brand_id: Optional[UUID]
    business_name: Optional[str]
    email: Optional[str]
    charges_enabled: bool
    payouts_enabled: bool
    tracking_enabled: bool
    commission_rate: float
    total_revenue: int
    total_commission: int
    payment_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentResponse(BaseModel):
    id: UUID
    stripe_charge_id: str
    stripe_payment_intent_id: Optional[str]
    amount: int
    currency: str
    net_amount: Optional[int]
    commission_amount: int
    commission_status: str
    tracking_code: Optional[str]
    affiliate_id: Optional[UUID]
    customer_email: Optional[str]
    is_subscription: bool
    is_refunded: bool
    is_disputed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AnalyticsOverview(BaseModel):
    total_revenue: int
    total_commission: int
    payment_count: int
    average_order_value: float
    conversion_rate: float
    refund_rate: float
    revenue_change: float
    commission_change: float
    payment_change: float


class RevenueByDay(BaseModel):
    date: str
    revenue: int
    commission: int
    payments: int


class UpdateSettingsRequest(BaseModel):
    tracking_enabled: Optional[bool] = None
    commission_rate: Optional[float] = None
    webhook_url: Optional[str] = None


# ============== Account Endpoints ==============


@router.get("/account/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get account details by ID."""
    result = await db.execute(
        select(StripeConnectedAccount).where(StripeConnectedAccount.id == account_id)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    return account


@router.get("/account/stripe/{stripe_account_id}", response_model=AccountResponse)
async def get_account_by_stripe_id(
    stripe_account_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get account details by Stripe account ID."""
    account_service = AccountService(db)
    account = await account_service.get_account_by_stripe_id(stripe_account_id)

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    return account


@router.patch("/account/{account_id}/settings")
async def update_account_settings(
    account_id: UUID,
    settings: UpdateSettingsRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update account settings."""
    result = await db.execute(
        select(StripeConnectedAccount).where(StripeConnectedAccount.id == account_id)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    if settings.tracking_enabled is not None:
        account.tracking_enabled = settings.tracking_enabled

    if settings.commission_rate is not None:
        if not 0 <= settings.commission_rate <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Commission rate must be between 0 and 1",
            )
        account.commission_rate = settings.commission_rate

    if settings.webhook_url is not None:
        account.webhook_url = settings.webhook_url

    account.updated_at = datetime.utcnow()
    await db.commit()

    return {"status": "updated", "account_id": str(account_id)}


@router.post("/account/{account_id}/disconnect")
async def disconnect_account(
    account_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Disconnect a Stripe account."""
    result = await db.execute(
        select(StripeConnectedAccount).where(StripeConnectedAccount.id == account_id)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    account_service = AccountService(db)
    await account_service.disconnect_account(account.stripe_account_id)

    return {"status": "disconnected", "stripe_account_id": account.stripe_account_id}


# ============== Payment Endpoints ==============


@router.get("/account/{account_id}/payments")
async def get_payments(
    account_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated payments for an account."""
    # Build query
    query = select(TrackedPayment).where(TrackedPayment.account_id == account_id)

    if status_filter:
        query = query.where(TrackedPayment.commission_status == status_filter)

    if start_date:
        query = query.where(TrackedPayment.created_at >= start_date)

    if end_date:
        query = query.where(TrackedPayment.created_at <= end_date)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    query = query.order_by(TrackedPayment.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    payments = result.scalars().all()

    return {
        "payments": [PaymentResponse.model_validate(p) for p in payments],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/payment/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get payment details by ID."""
    result = await db.execute(
        select(TrackedPayment).where(TrackedPayment.id == payment_id)
    )
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    return payment


# ============== Analytics Endpoints ==============


@router.get("/account/{account_id}/analytics", response_model=AnalyticsOverview)
async def get_analytics_overview(
    account_id: UUID,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get analytics overview for an account."""
    # Current period
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Previous period for comparison
    prev_end_date = start_date
    prev_start_date = prev_end_date - timedelta(days=days)

    # Current period stats
    current_query = select(
        func.sum(TrackedPayment.amount).label("revenue"),
        func.sum(TrackedPayment.commission_amount).label("commission"),
        func.count(TrackedPayment.id).label("count"),
        func.sum(
            func.cast(TrackedPayment.is_refunded, type_=db.bind.dialect.type_descriptor(type(1)))
        ).label("refunds"),
    ).where(
        TrackedPayment.account_id == account_id,
        TrackedPayment.created_at >= start_date,
        TrackedPayment.created_at <= end_date,
    )

    current_result = await db.execute(current_query)
    current = current_result.first()

    # Previous period stats
    prev_query = select(
        func.sum(TrackedPayment.amount).label("revenue"),
        func.sum(TrackedPayment.commission_amount).label("commission"),
        func.count(TrackedPayment.id).label("count"),
    ).where(
        TrackedPayment.account_id == account_id,
        TrackedPayment.created_at >= prev_start_date,
        TrackedPayment.created_at <= prev_end_date,
    )

    prev_result = await db.execute(prev_query)
    prev = prev_result.first()

    # Calculate metrics
    total_revenue = current.revenue or 0
    total_commission = current.commission or 0
    payment_count = current.count or 0
    refund_count = current.refunds or 0

    average_order_value = total_revenue / payment_count if payment_count > 0 else 0
    refund_rate = refund_count / payment_count if payment_count > 0 else 0

    # Calculate changes
    prev_revenue = prev.revenue or 0
    prev_commission = prev.commission or 0
    prev_count = prev.count or 0

    revenue_change = (
        ((total_revenue - prev_revenue) / prev_revenue * 100)
        if prev_revenue > 0
        else 0
    )
    commission_change = (
        ((total_commission - prev_commission) / prev_commission * 100)
        if prev_commission > 0
        else 0
    )
    payment_change = (
        ((payment_count - prev_count) / prev_count * 100)
        if prev_count > 0
        else 0
    )

    return AnalyticsOverview(
        total_revenue=total_revenue,
        total_commission=total_commission,
        payment_count=payment_count,
        average_order_value=average_order_value,
        conversion_rate=0,  # Would need click data
        refund_rate=refund_rate,
        revenue_change=revenue_change,
        commission_change=commission_change,
        payment_change=payment_change,
    )


@router.get("/account/{account_id}/analytics/revenue")
async def get_revenue_by_day(
    account_id: UUID,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get daily revenue breakdown."""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    query = select(
        func.date(TrackedPayment.created_at).label("date"),
        func.sum(TrackedPayment.amount).label("revenue"),
        func.sum(TrackedPayment.commission_amount).label("commission"),
        func.count(TrackedPayment.id).label("payments"),
    ).where(
        TrackedPayment.account_id == account_id,
        TrackedPayment.created_at >= start_date,
        TrackedPayment.created_at <= end_date,
    ).group_by(
        func.date(TrackedPayment.created_at)
    ).order_by(
        func.date(TrackedPayment.created_at)
    )

    result = await db.execute(query)
    rows = result.all()

    return [
        RevenueByDay(
            date=str(row.date),
            revenue=row.revenue or 0,
            commission=row.commission or 0,
            payments=row.payments or 0,
        )
        for row in rows
    ]


@router.get("/account/{account_id}/analytics/top-affiliates")
async def get_top_affiliates(
    account_id: UUID,
    limit: int = Query(10, ge=1, le=50),
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get top performing affiliates by revenue."""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    query = select(
        TrackedPayment.affiliate_id,
        func.sum(TrackedPayment.amount).label("revenue"),
        func.sum(TrackedPayment.commission_amount).label("commission"),
        func.count(TrackedPayment.id).label("payments"),
    ).where(
        TrackedPayment.account_id == account_id,
        TrackedPayment.affiliate_id.isnot(None),
        TrackedPayment.created_at >= start_date,
        TrackedPayment.created_at <= end_date,
    ).group_by(
        TrackedPayment.affiliate_id
    ).order_by(
        func.sum(TrackedPayment.amount).desc()
    ).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "affiliate_id": str(row.affiliate_id),
            "revenue": row.revenue or 0,
            "commission": row.commission or 0,
            "payments": row.payments or 0,
        }
        for row in rows
    ]


# ============== Webhook Log Endpoints ==============


@router.get("/account/{account_id}/webhooks")
async def get_webhook_logs(
    account_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    event_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get webhook logs for an account."""
    query = select(StripeWebhookLog).where(StripeWebhookLog.account_id == account_id)

    if event_type:
        query = query.where(StripeWebhookLog.event_type == event_type)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    query = query.order_by(StripeWebhookLog.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "logs": [
            {
                "id": str(log.id),
                "stripe_event_id": log.stripe_event_id,
                "event_type": log.event_type,
                "status": log.status,
                "processing_time_ms": log.processing_time_ms,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ============== Stripe Account Info ==============


@router.get("/account/{account_id}/stripe-info")
async def get_stripe_account_info(
    account_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get live Stripe account information."""
    result = await db.execute(
        select(StripeConnectedAccount).where(StripeConnectedAccount.id == account_id)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    try:
        stripe_account = StripeClient.get_account(account.stripe_account_id)
        return {
            "stripe_account_id": stripe_account.id,
            "business_name": stripe_account.business_profile.name if stripe_account.business_profile else None,
            "email": stripe_account.email,
            "charges_enabled": stripe_account.charges_enabled,
            "payouts_enabled": stripe_account.payouts_enabled,
            "details_submitted": stripe_account.details_submitted,
            "country": stripe_account.country,
            "default_currency": stripe_account.default_currency,
        }
    except Exception as e:
        logger.error(f"Error fetching Stripe account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch Stripe account information",
        )
