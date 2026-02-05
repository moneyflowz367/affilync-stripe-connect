"""
StripeConnectedAccount Model - Stores connected Stripe accounts
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class StripeConnectedAccount(Base):
    """
    Represents a Stripe account connected via Stripe Connect.
    This is for businesses/merchants who connect their Stripe account to track affiliate conversions.
    """

    __tablename__ = "stripe_connected_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Stripe identifiers
    stripe_account_id = Column(String(50), unique=True, nullable=False, index=True)
    stripe_user_id = Column(String(50), index=True)  # Stripe user ID if available

    # Business information
    business_name = Column(String(255))
    business_type = Column(String(50))  # individual, company
    business_email = Column(String(255))
    country = Column(String(2))  # ISO country code
    default_currency = Column(String(3), default="usd")

    # Connection details
    access_token = Column(Text)  # Encrypted, for Standard accounts
    refresh_token = Column(Text)  # Encrypted, for Standard accounts
    token_type = Column(String(50))
    scope = Column(Text)
    livemode = Column(Boolean, default=True)

    # Link to Affilync brand account
    brand_id = Column(UUID(as_uuid=True), index=True)

    # Tracking settings
    tracking_enabled = Column(Boolean, default=True)
    commission_rate = Column(Float, default=0.10)  # Default 10%
    commission_type = Column(String(20), default="percentage")  # percentage or flat

    # Status
    is_active = Column(Boolean, default=True)
    charges_enabled = Column(Boolean, default=False)
    payouts_enabled = Column(Boolean, default=False)

    # Metadata
    settings = Column(JSONB, default=dict)

    # Statistics (cached)
    total_tracked_revenue = Column(Float, default=0)
    total_tracked_payments = Column(Integer, default=0)
    total_commissions = Column(Float, default=0)

    # Timestamps
    connected_at = Column(DateTime, default=datetime.utcnow)
    disconnected_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    payments = relationship(
        "TrackedPayment",
        back_populates="account",
        cascade="all, delete-orphan",
    )
    webhook_logs = relationship(
        "StripeWebhookLog",
        back_populates="account",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<StripeConnectedAccount {self.stripe_account_id}: {self.business_name}>"

    @property
    def is_connected_to_affilync(self) -> bool:
        """Check if account is connected to an Affilync brand."""
        return self.brand_id is not None

    @property
    def is_fully_active(self) -> bool:
        """Check if account can process payments."""
        return self.is_active and self.charges_enabled

    def update_stats(
        self,
        revenue: float = 0,
        payments: int = 0,
        commissions: float = 0,
    ) -> None:
        """Update cached statistics."""
        self.total_tracked_revenue = (self.total_tracked_revenue or 0) + revenue
        self.total_tracked_payments = (self.total_tracked_payments or 0) + payments
        self.total_commissions = (self.total_commissions or 0) + commissions
