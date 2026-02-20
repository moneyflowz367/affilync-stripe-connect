"""Initialize schema with StripeConnectedAccount, TrackedPayment, StripeWebhookLog

Revision ID: 001_initial
Revises: None
Create Date: 2026-02-20

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial tables."""
    # stripe_connected_accounts
    op.create_table(
        "stripe_connected_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("stripe_account_id", sa.String(50), unique=True, nullable=False, index=True),
        sa.Column("stripe_user_id", sa.String(50), index=True),
        sa.Column("business_name", sa.String(255)),
        sa.Column("business_type", sa.String(50)),
        sa.Column("business_email", sa.String(255)),
        sa.Column("country", sa.String(2)),
        sa.Column("default_currency", sa.String(3), server_default="usd"),
        sa.Column("access_token", sa.Text()),
        sa.Column("refresh_token", sa.Text()),
        sa.Column("token_type", sa.String(50)),
        sa.Column("scope", sa.Text()),
        sa.Column("livemode", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), index=True),
        sa.Column("tracking_enabled", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("commission_rate", sa.Numeric(5, 4), server_default="0.10"),
        sa.Column("commission_type", sa.String(20), server_default="percentage"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("charges_enabled", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("payouts_enabled", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("settings", postgresql.JSONB(), server_default="{}"),
        sa.Column("total_tracked_revenue", sa.Numeric(12, 2), server_default="0"),
        sa.Column("total_tracked_payments", sa.Integer(), server_default="0"),
        sa.Column("total_commissions", sa.Numeric(12, 2), server_default="0"),
        sa.Column("connected_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("disconnected_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    # stripe_tracked_payments
    op.create_table(
        "stripe_tracked_payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("stripe_connected_accounts.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("stripe_charge_id", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("stripe_payment_intent_id", sa.String(100), index=True),
        sa.Column("stripe_invoice_id", sa.String(100), index=True),
        sa.Column("stripe_subscription_id", sa.String(100), index=True),
        sa.Column("stripe_customer_id", sa.String(100), index=True),
        sa.Column("payment_type", sa.String(50), server_default="charge"),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("amount_refunded", sa.Integer(), server_default="0"),
        sa.Column("currency", sa.String(3), server_default="usd"),
        sa.Column("net_amount", sa.Integer()),
        sa.Column("tracking_code", sa.String(100), index=True),
        sa.Column("affiliate_id", sa.String(100), index=True),
        sa.Column("commission_amount", sa.Numeric(12, 2)),
        sa.Column("commission_rate", sa.Numeric(5, 4)),
        sa.Column("commission_status", sa.String(50), server_default="pending"),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("is_captured", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("is_disputed", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("livemode", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("affilync_conversion_id", postgresql.UUID(as_uuid=True), index=True),
        sa.Column("synced_at", sa.DateTime()),
        sa.Column("sync_error", sa.Text()),
        sa.Column("customer_email_hash", sa.String(64)),
        sa.Column("customer_description", sa.String(255)),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
        sa.Column("receipt_url", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("stripe_created_at", sa.DateTime()),
    )

    # stripe_webhook_logs
    op.create_table(
        "stripe_webhook_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("stripe_connected_accounts.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("stripe_event_id", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("event_type", sa.String(100), nullable=False, index=True),
        sa.Column("api_version", sa.String(50)),
        sa.Column("stripe_account_id", sa.String(50), index=True),
        sa.Column("object_id", sa.String(100), index=True),
        sa.Column("object_type", sa.String(50)),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(50), server_default="received", index=True),
        sa.Column("result", postgresql.JSONB()),
        sa.Column("error", sa.Text()),
        sa.Column("processing_time_ms", sa.Integer()),
        sa.Column("received_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("processed_at", sa.DateTime()),
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table("stripe_webhook_logs")
    op.drop_table("stripe_tracked_payments")
    op.drop_table("stripe_connected_accounts")
