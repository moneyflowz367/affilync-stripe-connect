"""
Billing Routes
API endpoints for MERCHANT subscription management in the Stripe Connect integration.

This is the merchant's subscription to USE the Stripe Connect integration
(ported from the TikTok Shop integration). It is separate from the
affiliate-commission / payout endpoints.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import require_auth
from app.services.billing_service import PLANS, BillingError, BillingPlan, BillingService

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(require_auth)])


# ============== Request/Response Models ==============


class SubscribeRequest(BaseModel):
    """Subscription request"""

    plan: str  # Plan ID: free, starter, pro, enterprise
    account_id: str  # Connected account UUID


class CancelRequest(BaseModel):
    """Cancel subscription request"""

    account_id: str  # Connected account UUID


class SubscriptionStatus(BaseModel):
    """Subscription status response"""

    plan: str
    status: str
    features: list[str]
    max_products: int
    max_creators: int
    conversion_limit: int
    current_period_end: Optional[str] = None


# ============== Endpoints ==============


@router.get("/plans")
async def get_plans() -> dict:
    """
    Get available subscription plans.

    Returns all plans with pricing and features.
    """
    plans = [
        {
            "id": plan.value,
            "name": details.name,
            "price": float(details.price),
            "price_display": f"${details.price}/month" if details.price > 0 else "Free",
            "trial_days": details.trial_days,
            "features": details.features,
            "max_products": details.max_products,
            "max_creators": details.max_creators,
            "conversion_limit": details.conversion_limit,
            "analytics_depth_days": details.analytics_depth_days,
            "export_enabled": details.export_enabled,
            "api_access": details.api_access,
            "priority_support": details.priority_support,
            "popular": plan == BillingPlan.PRO,
        }
        for plan, details in PLANS.items()
    ]

    return {"plans": plans}


@router.get("/subscription")
async def get_subscription_status(
    account_id: str,
    db: AsyncSession = Depends(get_db),
) -> SubscriptionStatus:
    """
    Get current subscription status for a connected merchant account.

    Returns plan details, limits, and status.
    """
    try:
        aid = UUID(account_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid account_id format",
        )

    billing_service = BillingService(db)
    plan, subscription = await billing_service.get_current_plan(aid)
    plan_details = PLANS[plan]

    return SubscriptionStatus(
        plan=plan.value,
        status=subscription.get("status", "active") if subscription else "active",
        features=plan_details.features,
        max_products=plan_details.max_products,
        max_creators=plan_details.max_creators,
        conversion_limit=plan_details.conversion_limit,
        current_period_end=subscription.get("current_period_end") if subscription else None,
    )


@router.post("/subscribe")
async def create_subscription(
    request: SubscribeRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Subscribe to a plan or change the current plan.

    Upgrades take effect immediately. Downgrades are scheduled for the
    end of the current billing period.
    """
    # Validate plan
    try:
        plan = BillingPlan(request.plan)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan: {request.plan}. Valid plans: {[p.value for p in BillingPlan]}",
        )

    try:
        aid = UUID(request.account_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid account_id format",
        )

    billing_service = BillingService(db)

    try:
        result = await billing_service.create_subscription(aid, plan)
        return result
    except BillingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/cancel")
async def cancel_subscription(
    request: CancelRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Cancel the current subscription.

    Downgrades to the free plan. Access continues until the end of the
    current billing period.
    """
    try:
        aid = UUID(request.account_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid account_id format",
        )

    billing_service = BillingService(db)

    try:
        result = await billing_service.cancel_subscription(aid)
        return result
    except BillingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/usage")
async def get_usage(
    account_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get current usage statistics against plan limits.

    Returns conversion count and remaining quota for the merchant.
    """
    try:
        aid = UUID(account_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid account_id format",
        )

    billing_service = BillingService(db)
    return await billing_service.get_usage(aid)
