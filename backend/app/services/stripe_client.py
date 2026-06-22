"""
Stripe API Client
Handles all interactions with Stripe API
"""

import logging
from typing import Any, Dict, List, Optional

import stripe
from app.config import settings

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.stripe_secret_key


class StripeClient:
    """
    Client for Stripe API interactions.

    Handles both platform operations and connected account operations.
    """

    def __init__(self, connected_account_id: Optional[str] = None):
        """
        Initialize Stripe client.

        Args:
            connected_account_id: Optional Stripe connected account ID
                                  for making requests on behalf of a connected account
        """
        self.connected_account_id = connected_account_id

    def _get_stripe_kwargs(self) -> Dict[str, Any]:
        """Get kwargs for Stripe API calls."""
        kwargs = {}
        if self.connected_account_id:
            kwargs["stripe_account"] = self.connected_account_id
        return kwargs

    # ============== OAuth ==============

    @staticmethod
    def get_oauth_authorize_url(
        redirect_uri: str,
        state: str,
        scope: str = "read_write",
    ) -> str:
        """
        Get Stripe Connect OAuth authorization URL.

        Args:
            redirect_uri: OAuth callback URL
            state: CSRF state token
            scope: OAuth scope (read_only or read_write)

        Returns:
            Authorization URL
        """
        params = {
            "client_id": settings.stripe_client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
        }

        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"https://connect.stripe.com/oauth/authorize?{query}"

    @staticmethod
    async def exchange_oauth_code(
        code: str,
    ) -> Dict[str, Any]:
        """
        Exchange OAuth authorization code for tokens.

        Args:
            code: Authorization code from OAuth callback

        Returns:
            Token response with access_token, stripe_user_id, etc.
        """
        try:
            response = stripe.OAuth.token(
                grant_type="authorization_code",
                code=code,
            )
            return dict(response)
        except stripe.error.OAuthError as e:
            logger.error(f"OAuth token exchange failed: {e}")
            raise

    @staticmethod
    async def deauthorize_account(stripe_user_id: str) -> bool:
        """
        Deauthorize a connected account.

        Args:
            stripe_user_id: Stripe user ID to deauthorize

        Returns:
            True if successful
        """
        try:
            stripe.OAuth.deauthorize(
                client_id=settings.stripe_client_id,
                stripe_user_id=stripe_user_id,
            )
            return True
        except stripe.error.OAuthError as e:
            logger.error(f"Deauthorization failed: {e}")
            return False

    # ============== Accounts ==============

    async def get_account(self, account_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get Stripe account details.

        Args:
            account_id: Account ID (uses connected_account_id if not provided)

        Returns:
            Account object
        """
        target_id = account_id or self.connected_account_id
        if target_id:
            account = stripe.Account.retrieve(target_id)
        else:
            account = stripe.Account.retrieve()
        return dict(account)

    async def list_connected_accounts(
        self,
        limit: int = 10,
        starting_after: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List connected accounts.

        Args:
            limit: Number of accounts to return
            starting_after: Cursor for pagination

        Returns:
            List of account objects
        """
        params = {"limit": limit}
        if starting_after:
            params["starting_after"] = starting_after

        accounts = stripe.Account.list(**params)
        return [dict(a) for a in accounts.data]

    # ============== Charges ==============

    async def get_charge(self, charge_id: str) -> Dict[str, Any]:
        """
        Get a charge by ID.

        Args:
            charge_id: Stripe charge ID

        Returns:
            Charge object
        """
        charge = stripe.Charge.retrieve(charge_id, **self._get_stripe_kwargs())
        return dict(charge)

    async def list_charges(
        self,
        limit: int = 100,
        starting_after: Optional[str] = None,
        created: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """
        List charges.

        Args:
            limit: Number of charges to return
            starting_after: Cursor for pagination
            created: Filter by creation time (gte, lte, gt, lt)

        Returns:
            List of charge objects
        """
        params = {"limit": limit, **self._get_stripe_kwargs()}
        if starting_after:
            params["starting_after"] = starting_after
        if created:
            params["created"] = created

        charges = stripe.Charge.list(**params)
        return [dict(c) for c in charges.data]

    # ============== Payment Intents ==============

    async def get_payment_intent(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Get a payment intent by ID.

        Args:
            payment_intent_id: Stripe payment intent ID

        Returns:
            PaymentIntent object
        """
        pi = stripe.PaymentIntent.retrieve(
            payment_intent_id,
            **self._get_stripe_kwargs(),
        )
        return dict(pi)

    # ============== Invoices ==============

    async def get_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """
        Get an invoice by ID.

        Args:
            invoice_id: Stripe invoice ID

        Returns:
            Invoice object
        """
        invoice = stripe.Invoice.retrieve(invoice_id, **self._get_stripe_kwargs())
        return dict(invoice)

    async def list_invoices(
        self,
        customer: Optional[str] = None,
        subscription: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        List invoices.

        Args:
            customer: Filter by customer ID
            subscription: Filter by subscription ID
            limit: Number of invoices to return

        Returns:
            List of invoice objects
        """
        params = {"limit": limit, **self._get_stripe_kwargs()}
        if customer:
            params["customer"] = customer
        if subscription:
            params["subscription"] = subscription

        invoices = stripe.Invoice.list(**params)
        return [dict(i) for i in invoices.data]

    # ============== Subscriptions ==============

    async def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Get a subscription by ID.

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            Subscription object
        """
        sub = stripe.Subscription.retrieve(
            subscription_id,
            **self._get_stripe_kwargs(),
        )
        return dict(sub)

    async def list_subscriptions(
        self,
        customer: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        List subscriptions.

        Args:
            customer: Filter by customer ID
            status: Filter by status (active, past_due, etc.)
            limit: Number of subscriptions to return

        Returns:
            List of subscription objects
        """
        params = {"limit": limit, **self._get_stripe_kwargs()}
        if customer:
            params["customer"] = customer
        if status:
            params["status"] = status

        subs = stripe.Subscription.list(**params)
        return [dict(s) for s in subs.data]

    # ============== Customers ==============

    async def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """
        Get a customer by ID.

        Args:
            customer_id: Stripe customer ID

        Returns:
            Customer object
        """
        customer = stripe.Customer.retrieve(
            customer_id,
            **self._get_stripe_kwargs(),
        )
        return dict(customer)

    # ============== Balance ==============

    async def get_balance(self) -> Dict[str, Any]:
        """
        Get account balance.

        Returns:
            Balance object
        """
        balance = stripe.Balance.retrieve(**self._get_stripe_kwargs())
        return dict(balance)

    # ============== Webhooks ==============

    @staticmethod
    def verify_webhook_signature(
        payload: bytes,
        signature: str,
        secret: str = None,
    ) -> Dict[str, Any]:
        """
        Verify and parse webhook payload.

        Args:
            payload: Raw request body
            signature: Stripe-Signature header
            secret: Explicit webhook signing secret. When None, the configured
                platform secret is tried first, then the Connect secret (if set).

        Returns:
            Parsed event object

        Raises:
            stripe.error.SignatureVerificationError: On invalid signature
        """
        # Explicit secret (e.g. tests) bypasses the multi-secret logic.
        if secret:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                secret,
                tolerance=settings.webhook_tolerance,
            )
            return dict(event)

        # This single endpoint receives both platform events and Connect
        # (connected-account) events. Stripe signs each webhook endpoint with its
        # own secret, so try the platform secret first and, on a signature
        # mismatch, fall back to the Connect endpoint secret when one is
        # configured. If no Connect secret is set, behaviour is identical to
        # verifying against the platform secret alone.
        candidate_secrets = [settings.stripe_webhook_secret]
        if settings.stripe_connect_webhook_secret:
            candidate_secrets.append(settings.stripe_connect_webhook_secret)

        last_error: Optional[stripe.error.SignatureVerificationError] = None
        for candidate in candidate_secrets:
            try:
                event = stripe.Webhook.construct_event(
                    payload,
                    signature,
                    candidate,
                    tolerance=settings.webhook_tolerance,
                )
                return dict(event)
            except stripe.error.SignatureVerificationError as exc:
                last_error = exc

        # All candidate secrets rejected the signature — surface the failure.
        raise last_error
