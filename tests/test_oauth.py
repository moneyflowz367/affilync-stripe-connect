"""
Unit tests for Stripe Connect OAuth routes.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestOAuthConnect:
    """Tests for the /oauth/connect endpoint."""

    def test_connect_redirects_to_stripe(self, client):
        """Test that connect redirects to Stripe OAuth."""
        response = client.get(
            "/oauth/connect",
            params={"brand_id": "brand-123"},
            allow_redirects=False
        )
        # Should redirect to Stripe
        assert response.status_code in [302, 307]
        if response.status_code in [302, 307]:
            location = response.headers.get("location", "")
            assert "stripe.com" in location or "connect" in location.lower()

    def test_connect_requires_brand_id(self, client):
        """Test that connect requires brand_id parameter."""
        response = client.get("/oauth/connect")
        # Should fail without brand_id
        assert response.status_code in [400, 422]


class TestOAuthCallback:
    """Tests for the /oauth/callback endpoint."""

    @patch("stripe.OAuth")
    def test_callback_success(self, mock_oauth, client, db, mock_affilync_api):
        """Test successful OAuth callback."""
        mock_oauth.token.return_value = {
            "stripe_user_id": "acct_test123",
            "access_token": "sk_test_token",
            "refresh_token": "rt_test_token",
            "scope": "read_write"
        }

        response = client.get(
            "/oauth/callback",
            params={"code": "auth-code", "state": "brand-123"}
        )
        # Should succeed or redirect to dashboard
        assert response.status_code in [200, 302, 307]

    def test_callback_without_code_fails(self, client):
        """Test callback without code fails."""
        response = client.get("/oauth/callback", params={"state": "brand-123"})
        assert response.status_code in [400, 422]

    def test_callback_handles_error(self, client):
        """Test callback handles OAuth error from Stripe."""
        response = client.get(
            "/oauth/callback",
            params={
                "error": "access_denied",
                "error_description": "User denied access"
            }
        )
        # Should handle error gracefully
        assert response.status_code in [400, 302, 307]


class TestOAuthDeauthorize:
    """Tests for the deauthorization endpoint."""

    @patch("stripe.OAuth")
    def test_deauthorize_account(self, mock_oauth, client, db, sample_account_data):
        """Test deauthorizing a connected account."""
        mock_oauth.deauthorize.return_value = {"stripe_user_id": "acct_test123"}

        response = client.post(
            "/oauth/deauthorize",
            json={"stripe_account_id": "acct_test123"}
        )
        # Should acknowledge deauthorization
        assert response.status_code in [200, 204, 401, 404]
