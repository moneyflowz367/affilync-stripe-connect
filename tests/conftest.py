"""
Pytest configuration and fixtures for Stripe Connect integration tests.
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment variables before importing app
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy_key")
os.environ.setdefault("STRIPE_CLIENT_ID", "ca_test_dummy_client_id")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test_secret")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key-32chars-long!")
os.environ.setdefault("AFFILYNC_API_URL", "https://api.affilync.com")
os.environ.setdefault("AFFILYNC_API_KEY", "test-api-key")

from backend.app.main import app
from backend.app.database import Base, get_db


# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_stripe():
    """Mock Stripe API calls."""
    with patch("stripe.Account") as mock_account:
        with patch("stripe.Charge") as mock_charge:
            with patch("stripe.Webhook") as mock_webhook:
                # Mock account retrieval
                mock_account.retrieve.return_value = MagicMock(
                    id="acct_test123",
                    business_profile=MagicMock(name="Test Business"),
                    email="test@example.com",
                    charges_enabled=True,
                    payouts_enabled=True
                )

                # Mock charge retrieval
                mock_charge.retrieve.return_value = MagicMock(
                    id="ch_test123",
                    amount=5000,
                    currency="usd",
                    status="succeeded",
                    metadata={"affiliate_code": "AFF123"}
                )

                # Mock webhook construction
                mock_webhook.construct_event.return_value = MagicMock(
                    id="evt_test123",
                    type="charge.succeeded",
                    data=MagicMock(object=MagicMock(
                        id="ch_test123",
                        amount=5000,
                        metadata={"affiliate_code": "AFF123"}
                    ))
                )

                yield {
                    "Account": mock_account,
                    "Charge": mock_charge,
                    "Webhook": mock_webhook
                }


@pytest.fixture
def mock_affilync_api():
    """Mock Affilync API calls."""
    with patch("backend.app.services.account_service.httpx.AsyncClient") as mock:
        client = AsyncMock()
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"brand_id": "brand-123", "verified": True}
        client.__aenter__.return_value.post.return_value = response
        client.__aenter__.return_value.get.return_value = response
        mock.return_value = client
        yield client


@pytest.fixture
def sample_charge_event():
    """Sample charge.succeeded webhook event."""
    return {
        "id": "evt_test123",
        "type": "charge.succeeded",
        "data": {
            "object": {
                "id": "ch_test123",
                "amount": 5000,
                "currency": "usd",
                "status": "succeeded",
                "metadata": {
                    "affiliate_code": "AFF123",
                    "campaign_id": "camp_456"
                },
                "customer": "cus_test789"
            }
        },
        "created": 1706723456
    }


@pytest.fixture
def sample_subscription_event():
    """Sample subscription webhook event."""
    return {
        "id": "evt_sub_test123",
        "type": "customer.subscription.created",
        "data": {
            "object": {
                "id": "sub_test123",
                "customer": "cus_test789",
                "status": "active",
                "items": {
                    "data": [{
                        "price": {
                            "unit_amount": 2999,
                            "recurring": {"interval": "month"}
                        }
                    }]
                },
                "metadata": {
                    "affiliate_code": "AFF123"
                }
            }
        },
        "created": 1706723456
    }


@pytest.fixture
def sample_account_data():
    """Sample connected account data."""
    return {
        "stripe_account_id": "acct_test123",
        "business_name": "Test Business",
        "email": "test@example.com",
        "brand_id": "brand-123",
        "default_commission_rate": 10.0
    }
