"""
Tests for the Stripe Connect merchant billing ladder.

These cover the plan ladder (prices/tiers/trials/limits) and the pure
upgrade/downgrade detection logic — no database required. They lock in
parity with the platform-wide tier structure ported from the TikTok
integration.
"""

import os
from decimal import Decimal

# Provide the minimum env so `app.config.Settings` (which requires
# affilync_api_key / jwt_secret_key) can import cleanly under test.
os.environ.setdefault("AFFILYNC_API_KEY", "test-key")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test")
os.environ.setdefault("STRIPE_CLIENT_ID", "ca_test")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test")
os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key")

from app.services.billing_service import (  # noqa: E402
    PLAN_ORDER,
    PLANS,
    BillingPlan,
    BillingService,
)


def test_plan_ladder_prices_match_platform_tiers():
    """Free $0 / Starter $29 / Pro $99 / Enterprise $299."""
    assert PLANS[BillingPlan.FREE].price == Decimal("0")
    assert PLANS[BillingPlan.STARTER].price == Decimal("29")
    assert PLANS[BillingPlan.PRO].price == Decimal("99")
    assert PLANS[BillingPlan.ENTERPRISE].price == Decimal("299")


def test_plan_trial_days():
    assert PLANS[BillingPlan.FREE].trial_days == 0
    assert PLANS[BillingPlan.STARTER].trial_days == 7
    assert PLANS[BillingPlan.PRO].trial_days == 7
    assert PLANS[BillingPlan.ENTERPRISE].trial_days == 14


def test_conversion_limits_ladder():
    assert PLANS[BillingPlan.FREE].conversion_limit == 100
    assert PLANS[BillingPlan.STARTER].conversion_limit == 1000
    assert PLANS[BillingPlan.PRO].conversion_limit == 10000
    assert PLANS[BillingPlan.ENTERPRISE].conversion_limit == -1  # Unlimited


def test_plan_order_is_ascending():
    assert PLAN_ORDER == [
        BillingPlan.FREE,
        BillingPlan.STARTER,
        BillingPlan.PRO,
        BillingPlan.ENTERPRISE,
    ]


def test_is_upgrade_detection():
    service = BillingService(db=None)
    assert service._is_upgrade(BillingPlan.FREE, BillingPlan.PRO) is True
    assert service._is_upgrade(BillingPlan.PRO, BillingPlan.STARTER) is False
    assert service._is_upgrade(BillingPlan.STARTER, BillingPlan.STARTER) is False
    assert service._is_upgrade(BillingPlan.STARTER, BillingPlan.ENTERPRISE) is True


def test_all_plans_present():
    assert set(PLANS.keys()) == set(BillingPlan)
