"""Account API tests — pinned to the REAL surface.

The old suite patched app.routes.api.get_current_account (never existed —
the dependency chain is require_auth → authorize_account) and accepted
"200 or 401 or 403" so nothing could fail. These pins exercise the actual
per-account ownership gate: authorize_account was added because
require_auth alone let any merchant read another merchant's payments.
"""

import uuid

from app.main import app
from app.middleware.auth import require_auth

ACCOUNT_ID = "11111111-1111-1111-1111-111111111111"
OTHER_ID = "22222222-2222-2222-2222-222222222222"


def _as_jwt(account_id):
    return lambda: {"type": "jwt", "account_id": account_id}


def _as_service():
    return lambda: {"type": "api_key"}


class TestHealth:
    def test_health_check_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_includes_service_info(self, client):
        response = client.get("/health")
        data = response.json()
        assert "status" in data


class TestAccountOwnershipGate:
    """authorize_account: JWT must be bound to the path's account_id."""

    def test_get_account_requires_auth(self, client):
        response = client.get(f"/api/account/{ACCOUNT_ID}")
        assert response.status_code in (401, 403)

    def test_foreign_jwt_gets_403(self, client, db):
        """A valid JWT for a DIFFERENT account must not read this one."""
        app.dependency_overrides[require_auth] = _as_jwt(OTHER_ID)
        try:
            response = client.get(f"/api/account/{ACCOUNT_ID}")
        finally:
            app.dependency_overrides.pop(require_auth, None)
        assert response.status_code == 403

    def test_own_jwt_reaches_handler(self, client, db):
        """A JWT bound to the account passes the gate (404: no row yet —
        the gate ran, the lookup didn't find the account)."""
        app.dependency_overrides[require_auth] = _as_jwt(ACCOUNT_ID)
        try:
            response = client.get(f"/api/account/{ACCOUNT_ID}")
        finally:
            app.dependency_overrides.pop(require_auth, None)
        assert response.status_code == 404

    def test_trusted_service_reaches_handler(self, client, db):
        app.dependency_overrides[require_auth] = _as_service()
        try:
            response = client.get(f"/api/account/{ACCOUNT_ID}")
        finally:
            app.dependency_overrides.pop(require_auth, None)
        assert response.status_code == 404


class TestPaymentsAPI:
    def test_get_payments_requires_auth(self, client):
        response = client.get(f"/api/account/{ACCOUNT_ID}/payments")
        assert response.status_code in (401, 403)

    def test_foreign_jwt_cannot_list_payments(self, client, db):
        app.dependency_overrides[require_auth] = _as_jwt(OTHER_ID)
        try:
            response = client.get(f"/api/account/{ACCOUNT_ID}/payments")
        finally:
            app.dependency_overrides.pop(require_auth, None)
        assert response.status_code == 403

    def test_empty_account_lists_no_payments(self, client, db):
        app.dependency_overrides[require_auth] = _as_jwt(ACCOUNT_ID)
        try:
            response = client.get(f"/api/account/{ACCOUNT_ID}/payments")
        finally:
            app.dependency_overrides.pop(require_auth, None)
        assert response.status_code == 200
        data = response.json()
        payments = data.get("payments", data.get("items", []))
        assert payments == []

    def test_invalid_account_id_is_422(self, client):
        app.dependency_overrides[require_auth] = _as_service()
        try:
            response = client.get("/api/account/not-a-uuid/payments")
        finally:
            app.dependency_overrides.pop(require_auth, None)
        assert response.status_code == 422
