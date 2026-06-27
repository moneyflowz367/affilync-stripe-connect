"""Add stripe_connect_subscriptions for merchant billing

Revision ID: 002_merchant_subscriptions
Revises: 001_initial
Create Date: 2026-06-27

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_merchant_subscriptions"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the merchant subscription table."""
    op.create_table(
        "stripe_connect_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("stripe_connected_accounts.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
            index=True,
        ),
        sa.Column("plan", sa.String(50), nullable=False, server_default="free"),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("previous_plan", sa.String(50), nullable=True),
        sa.Column("price_cents", sa.Integer(), server_default="0"),
        sa.Column("currency", sa.String(10), server_default="USD"),
        sa.Column("trial_days", sa.Integer(), server_default="0"),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("grace_period_ends", sa.DateTime(timezone=True), nullable=True),
        sa.Column("downgrade_reason", sa.String(100), nullable=True),
        sa.Column("conversions_used", sa.Integer(), server_default="0"),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    """Drop the merchant subscription table."""
    op.drop_table("stripe_connect_subscriptions")
