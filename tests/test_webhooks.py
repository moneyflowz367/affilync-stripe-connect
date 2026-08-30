"""Stripe webhook tests — pinned to the REAL surface.

POST /webhooks/stripe. Signature verification happens via
StripeClient.verify_webhook_signature; V58.6 added event-id idempotency
(Stripe retries for up to 3 days — without dedup every retry re-routed
through commission credits and account state changes).
"""

import json
from unittest.mock import patch

VALID_SIG = {"Stripe-Signature": "t=1,v1=sig"}


def _verified(event):
    """Patch signature verification to return the given event."""
    return patch(
        "app.routes.webhooks.StripeClient.verify_webhook_signature",
        return_value=event,
    )


class TestWebhookAuth:
    def test_missing_signature_is_400(self, client, sample_charge_event):
        response = client.post("/webhooks/stripe", json=sample_charge_event)
        assert response.status_code == 400
        assert "Stripe-Signature" in response.json()["detail"]

    def test_invalid_signature_is_401(self, client, sample_charge_event):
        import stripe as stripe_lib

        with patch(
            "app.routes.webhooks.StripeClient.verify_webhook_signature",
            side_effect=stripe_lib.error.SignatureVerificationError("bad", "sig"),
        ):
            response = client.post(
                "/webhooks/stripe",
                content=json.dumps(sample_charge_event),
                headers={**VALID_SIG, "Content-Type": "application/json"},
            )
        assert response.status_code == 401


class TestWebhookDelivery:
    def test_charge_succeeded_is_accepted(self, client, db, sample_charge_event):
        with _verified(sample_charge_event):
            response = client.post(
                "/webhooks/stripe",
                content=json.dumps(sample_charge_event),
                headers={**VALID_SIG, "Content-Type": "application/json"},
            )
        assert response.status_code == 200

    def test_duplicate_delivery_is_deduped(self, client, db, sample_charge_event):
        """V58.6 P0: the second delivery of the same event id must short-
        circuit as a duplicate, not re-route through the handlers."""
        with _verified(sample_charge_event):
            first = client.post(
                "/webhooks/stripe",
                content=json.dumps(sample_charge_event),
                headers={**VALID_SIG, "Content-Type": "application/json"},
            )
            second = client.post(
                "/webhooks/stripe",
                content=json.dumps(sample_charge_event),
                headers={**VALID_SIG, "Content-Type": "application/json"},
            )
        assert first.status_code == 200
        assert second.status_code == 200
        assert second.json() == {
            "status": "duplicate",
            "event_id": sample_charge_event["id"],
        }

    def test_subscription_event_is_accepted(
        self, client, db, sample_subscription_event
    ):
        with _verified(sample_subscription_event):
            response = client.post(
                "/webhooks/stripe",
                content=json.dumps(sample_subscription_event),
                headers={**VALID_SIG, "Content-Type": "application/json"},
            )
        assert response.status_code == 200
