"""Stripe Connect OAuth tests — pinned to the REAL surface.

The old suite expected /oauth/connect to be public (it requires auth since
the 2026-05-18 audit — anonymous callers could flood Stripe's OAuth flow
and exhaust the Redis state store) and expected 4xx from /oauth/callback,
which deliberately REDIRECTS to the frontend with an error param instead
(the merchant is mid-browser-flow; a JSON 400 would strand them).
"""

from unittest.mock import AsyncMock, patch

from app.main import app
from app.middleware.auth import require_auth


class TestOAuthConnect:
    """GET /oauth/connect."""

    def test_connect_requires_auth(self, client):
        """Anonymous caller must not start an OAuth flow (2026-05-18 audit)."""
        response = client.get("/oauth/connect", follow_redirects=False)
        assert response.status_code in (401, 403)

    def test_connect_redirects_to_stripe(self, client):
        app.dependency_overrides[require_auth] = lambda: {"type": "jwt", "brand_id": "b1"}
        try:
            with patch(
                "app.routes.oauth._store_state", new=AsyncMock(return_value=None)
            ):
                response = client.get("/oauth/connect", follow_redirects=False)
        finally:
            app.dependency_overrides.pop(require_auth, None)
        assert response.status_code in (302, 307)
        location = response.headers["location"]
        assert "stripe.com" in location
        assert "state=" in location


class TestOAuthCallback:
    """GET /oauth/callback — browser flow: errors REDIRECT, never JSON-4xx."""

    def test_provider_error_redirects_with_error(self, client):
        response = client.get(
            "/oauth/callback",
            params={"error": "access_denied", "error_description": "denied"},
            follow_redirects=False,
        )
        assert response.status_code in (302, 307)
        assert "error=access_denied" in response.headers["location"]

    def test_missing_or_invalid_state_redirects_invalid_state(self, client):
        """CSRF posture: no state (or an unvalidatable one) never completes."""
        with patch(
            "app.routes.oauth._validate_state", new=AsyncMock(return_value=False)
        ):
            response = client.get(
                "/oauth/callback",
                params={"code": "ac_123", "state": "forged"},
                follow_redirects=False,
            )
        assert response.status_code in (302, 307)
        assert "error=invalid_state" in response.headers["location"]

    def test_valid_state_without_code_redirects_no_code(self, client):
        with patch(
            "app.routes.oauth._validate_state", new=AsyncMock(return_value=True)
        ):
            response = client.get(
                "/oauth/callback",
                params={"state": "valid"},
                follow_redirects=False,
            )
        assert response.status_code in (302, 307)
        assert "error=no_code" in response.headers["location"]

    def test_successful_callback_sets_httponly_cookie(self, client, db):
        """SEC-XI-08: the JWT travels as an HTTP-only cookie, never a URL
        param."""

        class _Account:
            id = "11111111-1111-1111-1111-111111111111"
            stripe_account_id = "acct_test123"

        with patch(
            "app.routes.oauth._validate_state", new=AsyncMock(return_value=True)
        ), patch("app.routes.oauth.AccountService") as MockSvc:
            MockSvc.return_value.complete_oauth = AsyncMock(return_value=_Account())
            response = client.get(
                "/oauth/callback",
                params={"code": "ac_123", "state": "valid"},
                follow_redirects=False,
            )
        assert response.status_code == 302
        assert response.headers["location"].endswith("/dashboard")
        cookie = response.headers.get("set-cookie", "")
        assert "auth_token=" in cookie
        assert "HttpOnly" in cookie
        # and the token must NOT leak into the redirect URL
        assert "token" not in response.headers["location"]
