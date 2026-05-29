"""
TrackedPayment Model - Stores tracked Stripe payments/subscriptions
"""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class TrackedPayment(Base):
    """
    Represents a tracked payment (charge or subscription) from a connected Stripe account.
    Used for affiliate attribution and commission calculation.
    """

    __tablename__ = "stripe_tracked_payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Account relationship
    account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("stripe_connected_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Stripe identifiers
    stripe_charge_id = Column(String(100), unique=True, nullable=False, index=True)
    stripe_payment_intent_id = Column(String(100), index=True)
    stripe_invoice_id = Column(String(100), index=True)
    stripe_subscription_id = Column(String(100), index=True)
    stripe_customer_id = Column(String(100), index=True)

    # Payment type
    payment_type = Column(String(50), default="charge")  # charge, subscription, invoice

    # Amount
    amount = Column(Integer, nullable=False)  # In cents
    amount_refunded = Column(Integer, default=0)
    currency = Column(String(3), default="usd")
    net_amount = Column(Integer)  # After fees

    # Attribution
    tracking_code = Column(String(100), index=True)
    affiliate_id = Column(String(100), index=True)  # Affilync affiliate ID

    # Commission
    commission_amount = Column(Numeric(12, 2))
    commission_rate = Column(Numeric(5, 4))
    commission_status = Column(String(50), default="pending")  # pending, approved, paid

    # Status
    status = Column(String(50), default="pending")  # pending, succeeded, failed, refunded
    is_captured = Column(Boolean, default=True)
    is_disputed = Column(Boolean, default=False)
    livemode = Column(Boolean, default=True)

    # Sync to Affilync
    affilync_conversion_id = Column(UUID(as_uuid=True), index=True)
    synced_at = Column(DateTime)
    sync_error = Column(Text)

    # Customer info (hashed for privacy)
    customer_email_hash = Column(String(64))
    customer_description = Column(String(255))

    # Metadata. NOTE: the Python attribute cannot be `metadata` — that name is
    # reserved by SQLAlchemy's declarative Base (raises InvalidRequestError at
    # class definition). Map to the existing "metadata" DB column explicitly.
    payment_metadata = Column("metadata", JSONB, default=dict)  # Stripe charge metadata
    receipt_url = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    stripe_created_at = Column(DateTime)

    # Relationships
    account = relationship("StripeConnectedAccount", back_populates="payments")

    def __repr__(self) -> str:
        return f"<TrackedPayment {self.stripe_charge_id}: ${self.amount / 100:.2f}>"

    @property
    def amount_dollars(self) -> Decimal:
        """Get amount in dollars."""
        from decimal import Decimal
        return Decimal(self.amount or 0) / Decimal("100")

    @property
    def net_amount_dollars(self) -> Decimal:
        """Get net amount in dollars."""
        from decimal import Decimal
        return Decimal(self.net_amount or self.amount or 0) / Decimal("100")

    @property
    def has_attribution(self) -> bool:
        """Check if payment has affiliate attribution."""
        return bool(self.tracking_code or self.affiliate_id)

    def mark_synced(self, conversion_id: str) -> None:
        """Mark payment as synced to Affilync."""
        self.affilync_conversion_id = conversion_id
        self.synced_at = datetime.now(UTC)
        self.sync_error = None

    def mark_sync_error(self, error: str) -> None:
        """Mark sync as failed."""
        self.sync_error = error
        self.synced_at = datetime.now(UTC)

    def calculate_commission(self, rate=None) -> "Decimal":
        """
        Calculate commission for this payment.

        Args:
            rate: Commission rate override (uses account rate if None)

        Returns:
            Commission amount in dollars (Decimal)
        """
        from decimal import Decimal, ROUND_HALF_UP

        if rate is None:
            rate = self.commission_rate or Decimal("0.10")

        rate = Decimal(str(rate))
        # Use net amount if available, otherwise amount (both in cents)
        base = Decimal(str(self.net_amount if self.net_amount else self.amount))
        return (base * rate / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @classmethod
    def from_stripe_charge(
        cls,
        account_id,
        charge: dict,
        tracking_code: str = None,
    ) -> "TrackedPayment":
        """
        Create a TrackedPayment from Stripe charge data.

        Args:
            account_id: StripeConnectedAccount UUID
            charge: Stripe charge object (dict)
            tracking_code: Extracted tracking code

        Returns:
            TrackedPayment instance
        """
        # Extract customer info
        customer_email = charge.get("billing_details", {}).get("email") or \
                        charge.get("receipt_email")

        # Hash email for privacy
        email_hash = None
        if customer_email:
            import hashlib
            email_hash = hashlib.sha256(customer_email.lower().encode()).hexdigest()

        # Determine payment type
        payment_type = "charge"
        if charge.get("invoice"):
            payment_type = "invoice"

        return cls(
            account_id=account_id,
            stripe_charge_id=charge.get("id"),
            stripe_payment_intent_id=charge.get("payment_intent"),
            stripe_invoice_id=charge.get("invoice"),
            stripe_customer_id=charge.get("customer"),
            payment_type=payment_type,
            amount=charge.get("amount", 0),
            amount_refunded=charge.get("amount_refunded", 0),
            currency=charge.get("currency", "usd"),
            status=charge.get("status", "pending"),
            is_captured=charge.get("captured", True),
            is_disputed=charge.get("disputed", False),
            livemode=charge.get("livemode", True),
            tracking_code=tracking_code,
            customer_email_hash=email_hash,
            customer_description=charge.get("description"),
            payment_metadata=charge.get("metadata", {}),
            receipt_url=charge.get("receipt_url"),
            stripe_created_at=datetime.utcfromtimestamp(charge.get("created", 0)),
        )
