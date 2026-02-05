"""
Stripe Webhook Handlers
Process incoming webhooks from Stripe
"""

import logging
from datetime import datetime

import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import StripeConnectedAccount, StripeWebhookLog
from app.services.account_service import AccountService
from app.services.commission_service import CommissionService
from app.services.stripe_client import StripeClient

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/stripe")
async def handle_stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db),
):
    """
    Main webhook endpoint for Stripe events.

    Handles both platform events and Connect events.
    """
    start_time = datetime.utcnow()

    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe-Signature header",
        )

    # Get raw body
    body = await request.body()

    # Verify signature and parse event
    try:
        event = StripeClient.verify_webhook_signature(body, stripe_signature)
    except stripe.error.SignatureVerificationError as e:
        logger.warning(f"Webhook signature verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature",
        )

    event_id = event.get("id")
    event_type = event.get("type")
    api_version = event.get("api_version")

    # Check for Connect event (event.account is set for connected account events)
    connected_account_id = event.get("account")

    logger.info(f"Received webhook: {event_type} (account: {connected_account_id or 'platform'})")

    # Get account if this is a Connect event
    account = None
    account_id = None
    if connected_account_id:
        account_service = AccountService(db)
        account = await account_service.get_account_by_stripe_id(connected_account_id)
        account_id = account.id if account else None

    # Log webhook
    webhook_log = StripeWebhookLog(
        account_id=account_id,
        stripe_event_id=event_id,
        event_type=event_type,
        api_version=api_version,
        stripe_account_id=connected_account_id,
        object_id=event.get("data", {}).get("object", {}).get("id"),
        object_type=event.get("data", {}).get("object", {}).get("object"),
        payload=event,
    )
    db.add(webhook_log)
    await db.commit()

    # Route to handler
    try:
        result = await route_webhook(
            event_type=event_type,
            event=event,
            account=account,
            db=db,
        )

        webhook_log.mark_processed(result)
        webhook_log.set_processing_time(start_time)
        await db.commit()

        return {"status": "processed", "result": result}

    except Exception as e:
        logger.exception(f"Webhook processing error: {e}")
        webhook_log.mark_failed(str(e))
        await db.commit()

        # Return 200 to prevent Stripe from retrying
        return {"status": "error", "error": str(e)}


async def route_webhook(
    event_type: str,
    event: dict,
    account: StripeConnectedAccount,
    db: AsyncSession,
) -> dict:
    """
    Route webhook to appropriate handler.

    Args:
        event_type: Stripe event type
        event: Full event object
        account: Connected account (if applicable)
        db: Database session

    Returns:
        Handler result
    """
    data = event.get("data", {})
    obj = data.get("object", {})

    handlers = {
        # Charge events
        "charge.succeeded": handle_charge_succeeded,
        "charge.refunded": handle_charge_refunded,
        "charge.dispute.created": handle_dispute_created,
        # Payment Intent events
        "payment_intent.succeeded": handle_payment_intent_succeeded,
        # Invoice events
        "invoice.paid": handle_invoice_paid,
        "invoice.payment_failed": handle_invoice_failed,
        # Subscription events
        "customer.subscription.created": handle_subscription_created,
        "customer.subscription.updated": handle_subscription_updated,
        "customer.subscription.deleted": handle_subscription_deleted,
        # Account events
        "account.application.deauthorized": handle_account_deauthorized,
        "account.updated": handle_account_updated,
    }

    handler = handlers.get(event_type)
    if not handler:
        logger.debug(f"Unhandled event type: {event_type}")
        return {"status": "unhandled", "event_type": event_type}

    return await handler(obj, account, db)


# ============== Charge Handlers ==============


async def handle_charge_succeeded(
    charge: dict,
    account: StripeConnectedAccount,
    db: AsyncSession,
) -> dict:
    """Handle successful charge - main conversion tracking."""
    charge_id = charge.get("id")

    if not account:
        logger.info(f"Charge {charge_id} for unregistered account")
        return {"status": "no_account", "charge_id": charge_id}

    if not account.tracking_enabled:
        return {"status": "tracking_disabled", "charge_id": charge_id}

    commission_service = CommissionService(db)
    return await commission_service.process_charge(account, charge)


async def handle_charge_refunded(
    charge: dict,
    account: StripeConnectedAccount,
    db: AsyncSession,
) -> dict:
    """Handle charge refund - adjust commission."""
    charge_id = charge.get("id")

    if not account:
        return {"status": "no_account", "charge_id": charge_id}

    # Get refund details
    refunds = charge.get("refunds", {}).get("data", [])
    if not refunds:
        return {"status": "no_refund_data", "charge_id": charge_id}

    commission_service = CommissionService(db)
    return await commission_service.process_refund(account, charge, refunds[-1])


async def handle_dispute_created(
    dispute: dict,
    account: StripeConnectedAccount,
    db: AsyncSession,
) -> dict:
    """Handle dispute created - flag payment."""
    charge_id = dispute.get("charge")
    dispute_id = dispute.get("id")

    logger.warning(f"Dispute created: {dispute_id} for charge {charge_id}")

    # Mark payment as disputed
    from sqlalchemy import select
    from app.models import TrackedPayment

    result = await db.execute(
        select(TrackedPayment).where(TrackedPayment.stripe_charge_id == charge_id)
    )
    payment = result.scalar_one_or_none()

    if payment:
        payment.is_disputed = True
        payment.commission_status = "disputed"
        await db.commit()

    return {
        "status": "logged",
        "dispute_id": dispute_id,
        "charge_id": charge_id,
    }


# ============== Payment Intent Handlers ==============


async def handle_payment_intent_succeeded(
    payment_intent: dict,
    account: StripeConnectedAccount,
    db: AsyncSession,
) -> dict:
    """Handle payment intent succeeded."""
    # Most tracking happens on charge.succeeded
    # This is for cases where we need PI-level data
    pi_id = payment_intent.get("id")
    return {"status": "logged", "payment_intent_id": pi_id}


# ============== Invoice Handlers ==============


async def handle_invoice_paid(
    invoice: dict,
    account: StripeConnectedAccount,
    db: AsyncSession,
) -> dict:
    """Handle paid invoice - track subscription payments."""
    invoice_id = invoice.get("id")

    if not account:
        return {"status": "no_account", "invoice_id": invoice_id}

    if not account.tracking_enabled:
        return {"status": "tracking_disabled", "invoice_id": invoice_id}

    commission_service = CommissionService(db)
    return await commission_service.process_subscription_invoice(account, invoice)


async def handle_invoice_failed(
    invoice: dict,
    account: StripeConnectedAccount,
    db: AsyncSession,
) -> dict:
    """Handle failed invoice payment."""
    invoice_id = invoice.get("id")
    return {"status": "logged", "invoice_id": invoice_id, "action": "payment_failed"}


# ============== Subscription Handlers ==============


async def handle_subscription_created(
    subscription: dict,
    account: StripeConnectedAccount,
    db: AsyncSession,
) -> dict:
    """Handle subscription created."""
    sub_id = subscription.get("id")
    logger.info(f"Subscription created: {sub_id}")
    return {"status": "logged", "subscription_id": sub_id}


async def handle_subscription_updated(
    subscription: dict,
    account: StripeConnectedAccount,
    db: AsyncSession,
) -> dict:
    """Handle subscription updated."""
    sub_id = subscription.get("id")
    status = subscription.get("status")
    return {"status": "logged", "subscription_id": sub_id, "subscription_status": status}


async def handle_subscription_deleted(
    subscription: dict,
    account: StripeConnectedAccount,
    db: AsyncSession,
) -> dict:
    """Handle subscription cancelled/deleted."""
    sub_id = subscription.get("id")
    logger.info(f"Subscription deleted: {sub_id}")
    return {"status": "logged", "subscription_id": sub_id, "action": "cancelled"}


# ============== Account Handlers ==============


async def handle_account_deauthorized(
    application: dict,
    account: StripeConnectedAccount,
    db: AsyncSession,
) -> dict:
    """Handle account deauthorization (user disconnected)."""
    # The account might not be in our system if it's a new deauth
    # The event itself contains the account ID

    account_service = AccountService(db)

    # Try to find and deactivate
    if account:
        await account_service.disconnect_account(account.stripe_account_id)
        return {"status": "deauthorized", "stripe_account_id": account.stripe_account_id}

    return {"status": "no_account"}


async def handle_account_updated(
    stripe_account: dict,
    account: StripeConnectedAccount,
    db: AsyncSession,
) -> dict:
    """Handle account updated - sync capabilities."""
    account_id = stripe_account.get("id")

    if not account:
        return {"status": "no_account", "stripe_account_id": account_id}

    # Update account status
    account.charges_enabled = stripe_account.get("charges_enabled", False)
    account.payouts_enabled = stripe_account.get("payouts_enabled", False)
    account.business_name = stripe_account.get("business_profile", {}).get("name")
    account.updated_at = datetime.utcnow()

    await db.commit()

    return {
        "status": "updated",
        "stripe_account_id": account_id,
        "charges_enabled": account.charges_enabled,
    }
