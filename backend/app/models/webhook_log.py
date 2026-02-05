"""
StripeWebhookLog Model - Webhook event logging
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class StripeWebhookLog(Base):
    """
    Logs incoming webhooks from Stripe for debugging and auditing.
    """

    __tablename__ = "stripe_webhook_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Account relationship (nullable for platform-wide events)
    account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("stripe_connected_accounts.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Webhook details
    stripe_event_id = Column(String(100), unique=True, nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    api_version = Column(String(50))

    # Related objects
    stripe_account_id = Column(String(50), index=True)  # Connected account ID
    object_id = Column(String(100), index=True)  # ID of the object (charge, invoice, etc.)
    object_type = Column(String(50))  # Type of object

    # Payload
    payload = Column(JSONB, nullable=False)

    # Processing status
    status = Column(String(50), default="received", index=True)
    result = Column(JSONB)
    error = Column(Text)
    processing_time_ms = Column(Integer)

    # Timestamps
    received_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)

    # Relationships
    account = relationship("StripeConnectedAccount", back_populates="webhook_logs")

    def __repr__(self) -> str:
        return f"<StripeWebhookLog {self.event_type} - {self.status}>"

    def mark_processed(self, result: dict = None) -> None:
        """Mark webhook as successfully processed."""
        self.status = "success"
        self.result = result
        self.processed_at = datetime.utcnow()

    def mark_failed(self, error: str) -> None:
        """Mark webhook as failed."""
        self.status = "failed"
        self.error = error
        self.processed_at = datetime.utcnow()

    def set_processing_time(self, start_time: datetime) -> None:
        """Calculate and set processing time."""
        if start_time:
            delta = datetime.utcnow() - start_time
            self.processing_time_ms = int(delta.total_seconds() * 1000)
