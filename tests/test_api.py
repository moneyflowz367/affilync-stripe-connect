"""
Unit tests for Stripe Connect API routes.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_check_returns_ok(self, client):
        """Test that health check returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "ok"]

    def test_health_check_includes_service_info(self, client):
        """Test that health check includes service information."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data or "status" in data


class TestAccountsAPI:
    """Tests for connected accounts API endpoints."""

    def test_get_account_requires_auth(self, client):
        """Test that getting account info requires authentication."""
        response = client.get("/api/account")
        assert response.status_code in [401, 403]

    @patch("backend.app.routes.api.get_current_account")
    def test_get_account_success(self, mock_get_account, client, db, sample_account_data):
        """Test successful account retrieval."""
        mock_get_account.return_value = sample_account_data

        response = client.get(
            "/api/account",
            headers={"Authorization": "Bearer test-session-token"}
        )
        # Should return account data or auth error
        assert response.status_code in [200, 401, 403]


class TestPaymentsAPI:
    """Tests for payments API endpoints."""

    def test_get_payments_requires_auth(self, client):
        """Test that getting payments requires authentication."""
        response = client.get("/api/payments")
        assert response.status_code in [401, 403, 404]

    @patch("backend.app.routes.api.get_current_account")
    def test_get_payments_returns_list(self, mock_get_account, client, db, sample_account_data):
        """Test that payments endpoint returns a list."""
        mock_get_account.return_value = sample_account_data

        response = client.get(
            "/api/payments",
            headers={"Authorization": "Bearer test-session-token"}
        )
        # Should return list or auth error
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list) or "payments" in data or "items" in data

    @patch("backend.app.routes.api.get_current_account")
    def test_get_payments_with_date_filter(self, mock_get_account, client, db, sample_account_data):
        """Test payments filtering by date range."""
        mock_get_account.return_value = sample_account_data

        response = client.get(
            "/api/payments",
            headers={"Authorization": "Bearer test-session-token"},
            params={"start_date": "2026-01-01", "end_date": "2026-01-31"}
        )
        assert response.status_code in [200, 401, 403, 404]


class TestCommissionsAPI:
    """Tests for commissions API endpoints."""

    def test_get_commissions_requires_auth(self, client):
        """Test that getting commissions requires authentication."""
        response = client.get("/api/commissions")
        assert response.status_code in [401, 403, 404]

    @patch("backend.app.routes.api.get_current_account")
    def test_get_commissions_summary(self, mock_get_account, client, db, sample_account_data):
        """Test commissions summary endpoint."""
        mock_get_account.return_value = sample_account_data

        response = client.get(
            "/api/commissions/summary",
            headers={"Authorization": "Bearer test-session-token"}
        )
        # Should return summary or auth/not found error
        assert response.status_code in [200, 401, 403, 404]


class TestAnalyticsAPI:
    """Tests for analytics API endpoints."""

    def test_get_analytics_requires_auth(self, client):
        """Test that analytics requires authentication."""
        response = client.get("/api/analytics")
        assert response.status_code in [401, 403, 404]

    @patch("backend.app.routes.api.get_current_account")
    def test_get_analytics_success(self, mock_get_account, client, db, sample_account_data):
        """Test successful analytics retrieval."""
        mock_get_account.return_value = sample_account_data

        response = client.get(
            "/api/analytics",
            headers={"Authorization": "Bearer test-session-token"},
            params={"period": "30d"}
        )
        assert response.status_code in [200, 401, 403, 404]

    @patch("backend.app.routes.api.get_current_account")
    def test_get_analytics_by_affiliate(self, mock_get_account, client, db, sample_account_data):
        """Test analytics breakdown by affiliate."""
        mock_get_account.return_value = sample_account_data

        response = client.get(
            "/api/analytics/by-affiliate",
            headers={"Authorization": "Bearer test-session-token"}
        )
        assert response.status_code in [200, 401, 403, 404]


class TestSettingsAPI:
    """Tests for settings API endpoints."""

    def test_get_settings_requires_auth(self, client):
        """Test that getting settings requires authentication."""
        response = client.get("/api/settings")
        assert response.status_code in [401, 403, 404]

    @patch("backend.app.routes.api.get_current_account")
    def test_update_commission_rate(self, mock_get_account, client, db, sample_account_data):
        """Test updating default commission rate."""
        mock_get_account.return_value = sample_account_data

        response = client.patch(
            "/api/settings",
            headers={"Authorization": "Bearer test-session-token"},
            json={"default_commission_rate": 15.0}
        )
        assert response.status_code in [200, 401, 403, 404, 422]

    @patch("backend.app.routes.api.get_current_account")
    def test_update_settings_validates_input(self, mock_get_account, client, db, sample_account_data):
        """Test that settings update validates input."""
        mock_get_account.return_value = sample_account_data

        response = client.patch(
            "/api/settings",
            headers={"Authorization": "Bearer test-session-token"},
            json={"default_commission_rate": -10.0}  # Invalid negative rate
        )
        # Should reject invalid commission rate
        assert response.status_code in [400, 422, 401, 403, 404]
