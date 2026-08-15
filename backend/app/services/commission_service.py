"""
Commission Service
Handles tracking payments and calculating commissions
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from affilync_integrations import AffilyncAPIClient, ConversionData, AdjustmentData

from app.config import settings
from app.models import StripeConnectedAccount, TrackedPayment

logger = logging.getLogger(__name__)


class CommissionService:
    """Service for tracking payments and calculating commissions."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.api_client = AffilyncAPIClient(
            api_url=settings.affilync_api_url,
            api_key=settings.affilync_api_key,
            source="stripe-connect-app",
        )

    async def process_charge(
        self,
        account: StripeConnectedAccount,
        charge_data: dict,
    ) -> dict:
        """
        Process a charge for affiliate conversion tracking.

        Args:
            account: Connected account that received the charge
            charge_data: Stripe charge webhook data

        Returns:
            dict: Processing result
        """
        charge_id = charge_data.get("id")
        logger.info(f"Processing charge {charge_id} for {account.stripe_account_id}")

        # Check if already tracked
        existing = await self._get_payment_by_charge_id(charge_id)
        if existing:
            logger.info(f"Charge {charge_id} already tracked")
            return {
                "status": "already_tracked",
                "charge_id": charge_id,
                "payment_id": str(existing.id),
            }

        # Extract tracking code from metadata
        tracking_code = self._extract_tracking_code(charge_data)

        # Create tracked payment
        payment = TrackedPayment.from_stripe_charge(
            account_id=account.id,
            charge=charge_data,
            tracking_code=tracking_code,
        )

        # Set commission rate from account
        payment.commission_rate = account.commission_rate
        payment.commission_amount = payment.calculate_commission()

        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)

        # Update account stats
        account.update_stats(
            revenue=payment.amount_dollars,
            payments=1,
            commissions=payment.commission_amount or 0,
        )
        await self.db.commit()

        # If no attribution, just log
        if not tracking_code:
            logger.info(f"No affiliate attribution for charge {charge_id}")
            return {
                "status": "no_attribution",
                "charge_id": charge_id,
                "payment_id": str(payment.id),
            }

        # Check if account is connected to Affilync brand
        if not account.brand_id:
            logger.info(f"Account {account.stripe_account_id} not connected to Affilync brand")
            return {
                "status": "not_connected",
                "charge_id": charge_id,
                "tracking_code": tracking_code,
                "payment_id": str(payment.id),
            }

        # Sync to Affilync
        try:
            result = await self._sync_to_affilync(account, payment)
            return {
                "status": "tracked",
                "charge_id": charge_id,
                "tracking_code": tracking_code,
                "payment_id": str(payment.id),
                "conversion_id": result.get("conversion_id"),
            }
        except Exception as e:
            logger.error(f"Failed to sync charge {charge_id} to Affilync: {e}")
            payment.mark_sync_error(str(e))
            await self.db.commit()
            return {
                "status": "sync_error",
                "charge_id": charge_id,
                "tracking_code": tracking_code,
                "payment_id": str(payment.id),
                "error": str(e),
            }

    async def process_refund(
        self,
        account: StripeConnectedAccount,
        charge_data: dict,
        refund_data: dict,
    ) -> dict:
        """
        Process a refund for commission adjustment.

        Args:
            account: Connected account
            charge_data: Original charge data
            refund_data: Refund data

        Returns:
            dict: Processing result
        """
        charge_id = charge_data.get("id")
        refund_id = refund_data.get("id")
        refund_amount = refund_data.get("amount", 0)

        logger.info(f"Processing refund {refund_id} for charge {charge_id}")

        # Find tracked payment
        payment = await self._get_payment_by_charge_id(charge_id)
        if not payment:
            logger.info(f"No tracked payment for charge {charge_id}")
            return {
                "status": "no_payment",
                "charge_id": charge_id,
                "refund_id": refund_id,
            }

        # Update payment
        payment.amount_refunded = (payment.amount_refunded or 0) + refund_amount
        payment.status = "refunded" if payment.amount_refunded >= (payment.amount or 0) else "partial_refund"
        payment.updated_at = datetime.utcnow()

        await self.db.commit()

        # If not synced to Affilync, no adjustment needed
        if not payment.affilync_conversion_id:
            return {
                "status": "local_only",
                "charge_id": charge_id,
                "refund_id": refund_id,
                "refund_amount": refund_amount / 100,
            }

        # Send adjustment to Affilync
        if account.brand_id:
            try:
                adjustment_data = AdjustmentData(
                    brand_id=str(account.brand_id),
                    original_order_id=f"stripe_{charge_id}",
                    adjustment_type="refund",
                    adjustment_amount=float(Decimal(str(refund_amount)) / Decimal("100")),
                    refund_id=f"stripe_{refund_id}",
                    metadata={
                        "source": "stripe",
                        "stripe_account_id": account.stripe_account_id,
                        "stripe_refund_id": refund_id,
                    },
                )

                result = await self.api_client.track_adjustment(adjustment_data)
                return {
                    "status": "adjusted",
                    "charge_id": charge_id,
                    "refund_id": refund_id,
                    "adjustment_id": result.get("adjustment_id"),
                }
            except Exception as e:
                logger.error(f"Failed to send refund adjustment: {e}")
                return {
                    "status": "adjustment_error",
                    "charge_id": charge_id,
                    "refund_id": refund_id,
                    "error": str(e),
                }

        return {
            "status": "not_connected",
            "charge_id": charge_id,
            "refund_id": refund_id,
        }

    async def process_subscription_invoice(
        self,
        account: StripeConnectedAccount,
        invoice_data: dict,
    ) -> dict:
        """
        Process a subscription invoice for recurring commission.

        Args:
            account: Connected account
            invoice_data: Stripe invoice data

        Returns:
            dict: Processing result
        """
        invoice_id = invoice_data.get("id")
        charge_id = invoice_data.get("charge")

        if not charge_id:
            logger.info(f"Invoice {invoice_id} has no charge yet")
            return {
                "status": "no_charge",
                "invoice_id": invoice_id,
            }

        # Get the charge data
        from app.services.stripe_client import StripeClient

        client = StripeClient(account.stripe_account_id)
        charge_data = await client.get_charge(charge_id)

        # Process as regular charge
        result = await self.process_charge(account, charge_data)

        # Add subscription info
        result["invoice_id"] = invoice_id
        result["subscription_id"] = invoice_data.get("subscription")

        return result

    def _extract_tracking_code(self, charge_data: dict) -> Optional[str]:
        """
        Extract tracking code from charge metadata.

        Looks for tracking code in:
        1. charge.metadata.tracking_code
        2. charge.metadata.ref
        3. charge.metadata.affiliate
        4. payment_intent.metadata (if available)
        5. customer.metadata (if available)

        Args:
            charge_data: Stripe charge data

        Returns:
            Tracking code or None
        """
        metadata = charge_data.get("metadata", {})

        # Check common keys
        for key in ["tracking_code", "ref", "affiliate", "aff", "affiliate_code", "via"]:
            if key in metadata and metadata[key]:
                return str(metadata[key])

        # Check for utm_source as fallback
        if "utm_source" in metadata:
            return str(metadata["utm_source"])

        return None

    async def _get_payment_by_charge_id(
        self,
        charge_id: str,
    ) -> Optional[TrackedPayment]:
        """Get tracked payment by Stripe charge ID."""
        result = await self.db.execute(
            select(TrackedPayment).where(
                TrackedPayment.stripe_charge_id == charge_id
            )
        )
        return result.scalar_one_or_none()

    async def _sync_to_affilync(
        self,
        account: StripeConnectedAccount,
        payment: TrackedPayment,
    ) -> dict:
        """
        Sync a payment to Affilync as a conversion.

        Args:
            account: Connected account
            payment: Tracked payment

        Returns:
            API response with conversion_id
        """
        conversion_data = ConversionData(
            tracking_code=payment.tracking_code,
            brand_id=str(account.brand_id),
            order_id=f"stripe_{payment.stripe_charge_id}",
            order_value=payment.net_amount_dollars,
            total_value=payment.amount_dollars,
            currency=payment.currency,
            # conversion_type MUST be a ConversionCreate enum value
            # (sale/lead/signup/download/subscription/custom) — "purchase"
            # isn't valid (same fix applied to Shopify/BigCommerce).
            conversion_type="sale",
            metadata={
                "source": "stripe",
                "stripe_account_id": account.stripe_account_id,
                "stripe_charge_id": payment.stripe_charge_id,
                "payment_type": payment.payment_type,
                "livemode": payment.livemode,
            },
        )

        result = await self.api_client.track_conversion(conversion_data)
        payment.mark_synced(result.get("conversion_id"))
        await self.db.commit()

        return result

    async def get_payment_stats(
        self,
        account: StripeConnectedAccount,
        period: str = "month",
    ) -> dict:
        """
        Get payment statistics for an account.

        Args:
            account: Connected account
            period: Time period (day, week, month)

        Returns:
            Statistics dict
        """
        from sqlalchemy import func, and_
        from datetime import timedelta

        now = datetime.utcnow()
        if period == "day":
            start = now - timedelta(days=1)
        elif period == "week":
            start = now - timedelta(weeks=1)
        else:
            start = now - timedelta(days=30)

        # Query stats
        result = await self.db.execute(
            select(
                func.count(TrackedPayment.id).label("count"),
                func.sum(TrackedPayment.amount).label("total_amount"),
                func.sum(TrackedPayment.commission_amount).label("total_commission"),
            ).where(
                and_(
                    TrackedPayment.account_id == account.id,
                    TrackedPayment.created_at >= start,
                    TrackedPayment.status == "succeeded",
                )
            )
        )

        row = result.one()

        return {
            "period": period,
            "payment_count": row.count or 0,
            "total_amount": (row.total_amount or 0) / 100,
            "total_commission": row.total_commission or 0,
            "currency": account.default_currency,
        }
