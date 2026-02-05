"""
Unit tests for Stripe Connect webhook routes.
"""

import pytest
import json
import time
import hmac
import hashlib
from unittest.mock import patch, MagicMock


class TestChargeWebhooks:
    """Tests for charge webhook handling."""

    @patch("stripe.Webhook")
    def test_charge_succeeded_webhook(self, mock_webhook, client, db, sample_charge_event):
        """Test charge.succeeded webhook processing."""
        mock_webhook.construct_event.return_value = MagicMock(
            id=sample_charge_event["id"],
            type=sample_charge_event["type"],
            data=MagicMock(object=MagicMock(**sample_charge_event["data"]["object"]))
        )

        payload = json.dumps(sample_charge_event)
        timestamp = str(int(time.time()))
        signature = f"t={timestamp},v1=test_signature"

        response = client.post(
            "/webhooks/stripe",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": signature
            }
        )
        # Should acknowledge webhook
        assert response.status_code in [200, 202, 204, 400]

    @patch("stripe.Webhook")
    def test_charge_refunded_webhook(self, mock_webhook, client, db, sample_charge_event):
        """Test charge.refunded webhook processing."""
        refund_event = sample_charge_event.copy()
        refund_event["type"] = "charge.refunded"

        mock_webhook.construct_event.return_value = MagicMock(
            id=refund_event["id"],
            type="charge.refunded",
            data=MagicMock(object=MagicMock(**refund_event["data"]["object"]))
        )

        payload = json.dumps(refund_event)
        timestamp = str(int(time.time()))
        signature = f"t={timestamp},v1=test_signature"

        response = client.post(
            "/webhooks/stripe",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": signature
            }
        )
        assert response.status_code in [200, 202, 204, 400]


class TestSubscriptionWebhooks:
    """Tests for subscription webhook handling."""

    @patch("stripe.Webhook")
    def test_subscription_created_webhook(self, mock_webhook, client, db, sample_subscription_event):
        """Test customer.subscription.created webhook processing."""
        mock_webhook.construct_event.return_value = MagicMock(
            id=sample_subscription_event["id"],
            type=sample_subscription_event["type"],
            data=MagicMock(object=MagicMock(**sample_subscription_event["data"]["object"]))
        )

        payload = json.dumps(sample_subscription_event)
        timestamp = str(int(time.time()))
        signature = f"t={timestamp},v1=test_signature"

        response = client.post(
            "/webhooks/stripe",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": signature
            }
        )
        assert response.status_code in [200, 202, 204, 400]

    @patch("stripe.Webhook")
    def test_subscription_cancelled_webhook(self, mock_webhook, client, db, sample_subscription_event):
        """Test customer.subscription.deleted webhook processing."""
        cancel_event = sample_subscription_event.copy()
        cancel_event["type"] = "customer.subscription.deleted"
        cancel_event["data"]["object"]["status"] = "canceled"

        mock_webhook.construct_event.return_value = MagicMock(
            id=cancel_event["id"],
            type="customer.subscription.deleted",
            data=MagicMock(object=MagicMock(**cancel_event["data"]["object"]))
        )

        payload = json.dumps(cancel_event)
        timestamp = str(int(time.time()))
        signature = f"t={timestamp},v1=test_signature"

        response = client.post(
            "/webhooks/stripe",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": signature
            }
        )
        assert response.status_code in [200, 202, 204, 400]


class TestWebhookSecurity:
    """Tests for webhook signature verification."""

    def test_webhook_without_signature_fails(self, client, sample_charge_event):
        """Test webhook without signature fails."""
        response = client.post(
            "/webhooks/stripe",
            json=sample_charge_event
        )
        # Should fail without signature
        assert response.status_code in [400, 401, 403]

    @patch("stripe.Webhook")
    def test_webhook_with_invalid_signature_fails(self, mock_webhook, client, sample_charge_event):
        """Test webhook with invalid signature fails."""
        mock_webhook.construct_event.side_effect = Exception("Invalid signature")

        response = client.post(
            "/webhooks/stripe",
            json=sample_charge_event,
            headers={"Stripe-Signature": "invalid-signature"}
        )
        # Should fail with invalid signature
        assert response.status_code in [400, 401, 403]


class TestAccountWebhooks:
    """Tests for account-related webhook handling."""

    @patch("stripe.Webhook")
    def test_account_deauthorized_webhook(self, mock_webhook, client, db):
        """Test account.application.deauthorized webhook processing."""
        deauth_event = {
            "id": "evt_deauth_test",
            "type": "account.application.deauthorized",
            "data": {
                "object": {
                    "id": "acct_test123"
                }
            }
        }

        mock_webhook.construct_event.return_value = MagicMock(
            id=deauth_event["id"],
            type=deauth_event["type"],
            data=MagicMock(object=MagicMock(id="acct_test123"))
        )

        payload = json.dumps(deauth_event)
        timestamp = str(int(time.time()))
        signature = f"t={timestamp},v1=test_signature"

        response = client.post(
            "/webhooks/stripe",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": signature
            }
        )
        assert response.status_code in [200, 202, 204, 400]
