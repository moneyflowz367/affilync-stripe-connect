"""Pytest configuration and fixtures for Stripe Connect integration tests.

Everything imports the service as ``app.*`` — the same module tree
``backend/app/main.py`` itself uses (``pythonpath = backend`` in pytest.ini).
The previous harness imported ``backend.app.*``, which built a PARALLEL copy
of every module: its ``get_db`` override keyed on a function object no route
depended on (routes silently hit the real engine), and every
``@patch("backend.app...")`` patched modules the running app never imported.
It also drove async routes through a sync SQLAlchemy session.
"""

import os

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from unittest.mock import AsyncMock, MagicMock, patch

# Set test environment variables before importing app
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_dummy_key")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy_key")
os.environ.setdefault("STRIPE_CLIENT_ID", "ca_test_dummy_client_id")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test_secret")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key-32chars-long!")
os.environ.setdefault("AFFILYNC_API_URL", "https://api.affilync.com")
os.environ.setdefault("AFFILYNC_API_KEY", "test-api-key")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret")

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

_test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestSession = async_sessionmaker(_test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="function")
async def db():
    """Create a fresh schema for each test and yield an AsyncSession."""
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with _TestSession() as session:
        yield session
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
def client(db):
    """Test client whose get_db override targets the REAL dependency object."""

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_affilync_api():
    """Mock the outbound Affilync API calls made by account_service."""
    with patch("app.services.account_service.httpx.AsyncClient") as mock:
        api_client = AsyncMock()
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"brand_id": "brand-123", "verified": True}
        api_client.__aenter__.return_value.post.return_value = response
        api_client.__aenter__.return_value.get.return_value = response
        mock.return_value = api_client
        yield api_client


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
                    "campaign_id": "camp_456",
                },
                "customer": "cus_test789",
            }
        },
        "created": 1706723456,
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
                    "data": [
                        {
                            "price": {
                                "unit_amount": 2999,
                                "recurring": {"interval": "month"},
                            }
                        }
                    ]
                },
                "metadata": {"affiliate_code": "AFF123"},
            }
        },
        "created": 1706723456,
    }


@pytest.fixture
def sample_account_data():
    """Sample connected account data."""
    return {
        "stripe_account_id": "acct_test123",
        "business_name": "Test Business",
        "email": "test@example.com",
        "brand_id": "brand-123",
        "default_commission_rate": 10.0,
    }
