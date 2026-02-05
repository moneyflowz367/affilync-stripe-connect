"""
Account Service
Manages connected Stripe accounts
"""

import logging
import secrets
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import StripeConnectedAccount
from app.services.stripe_client import StripeClient

logger = logging.getLogger(__name__)


class AccountService:
    """Service for managing connected Stripe accounts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_account_by_stripe_id(
        self,
        stripe_account_id: str,
    ) -> Optional[StripeConnectedAccount]:
        """Get account by Stripe account ID."""
        result = await self.db.execute(
            select(StripeConnectedAccount).where(
                StripeConnectedAccount.stripe_account_id == stripe_account_id
            )
        )
        return result.scalar_one_or_none()

    async def get_account_by_id(
        self,
        account_id: UUID,
    ) -> Optional[StripeConnectedAccount]:
        """Get account by internal ID."""
        result = await self.db.execute(
            select(StripeConnectedAccount).where(
                StripeConnectedAccount.id == account_id
            )
        )
        return result.scalar_one_or_none()

    async def get_active_accounts(self) -> list[StripeConnectedAccount]:
        """Get all active connected accounts."""
        result = await self.db.execute(
            select(StripeConnectedAccount).where(
                StripeConnectedAccount.is_active == True
            )
        )
        return result.scalars().all()

    async def get_accounts_by_brand(
        self,
        brand_id: UUID,
    ) -> list[StripeConnectedAccount]:
        """Get all accounts connected to a brand."""
        result = await self.db.execute(
            select(StripeConnectedAccount).where(
                StripeConnectedAccount.brand_id == brand_id,
                StripeConnectedAccount.is_active == True,
            )
        )
        return result.scalars().all()

    def generate_oauth_state(self) -> str:
        """Generate a secure state token for OAuth."""
        return secrets.token_urlsafe(32)

    def get_oauth_url(self, state: str) -> str:
        """
        Get Stripe Connect OAuth URL.

        Args:
            state: CSRF state token

        Returns:
            Authorization URL
        """
        return StripeClient.get_oauth_authorize_url(
            redirect_uri=f"{settings.app_url}/oauth/callback",
            state=state,
            scope="read_write",
        )

    async def complete_oauth(
        self,
        code: str,
    ) -> StripeConnectedAccount:
        """
        Complete OAuth flow and create/update account.

        Args:
            code: Authorization code from OAuth callback

        Returns:
            StripeConnectedAccount: Created or updated account
        """
        # Exchange code for tokens
        token_response = await StripeClient.exchange_oauth_code(code)

        stripe_account_id = token_response.get("stripe_user_id")
        access_token = token_response.get("access_token")
        refresh_token = token_response.get("refresh_token")
        token_type = token_response.get("token_type")
        scope = token_response.get("scope")
        livemode = token_response.get("livemode", True)

        if not stripe_account_id:
            raise ValueError("No stripe_user_id in token response")

        # Check for existing account
        existing = await self.get_account_by_stripe_id(stripe_account_id)

        # Fetch account details from Stripe
        client = StripeClient(stripe_account_id)
        account_info = await client.get_account(stripe_account_id)

        # Encrypt tokens
        from app.utils.encryption import encrypt_token

        encrypted_access = encrypt_token(access_token) if access_token else None
        encrypted_refresh = encrypt_token(refresh_token) if refresh_token else None

        if existing:
            # Update existing account
            existing.access_token = encrypted_access
            existing.refresh_token = encrypted_refresh
            existing.token_type = token_type
            existing.scope = scope
            existing.livemode = livemode
            existing.is_active = True
            existing.disconnected_at = None
            existing.business_name = account_info.get("business_profile", {}).get("name")
            existing.business_type = account_info.get("business_type")
            existing.charges_enabled = account_info.get("charges_enabled", False)
            existing.payouts_enabled = account_info.get("payouts_enabled", False)
            existing.country = account_info.get("country")
            existing.default_currency = account_info.get("default_currency", "usd")
            existing.updated_at = datetime.utcnow()

            logger.info(f"Reconnected Stripe account: {stripe_account_id}")
            await self.db.commit()
            return existing

        # Create new account
        account = StripeConnectedAccount(
            stripe_account_id=stripe_account_id,
            stripe_user_id=stripe_account_id,
            access_token=encrypted_access,
            refresh_token=encrypted_refresh,
            token_type=token_type,
            scope=scope,
            livemode=livemode,
            business_name=account_info.get("business_profile", {}).get("name"),
            business_type=account_info.get("business_type"),
            business_email=account_info.get("email"),
            charges_enabled=account_info.get("charges_enabled", False),
            payouts_enabled=account_info.get("payouts_enabled", False),
            country=account_info.get("country"),
            default_currency=account_info.get("default_currency", "usd"),
            is_active=True,
        )

        self.db.add(account)
        await self.db.commit()
        await self.db.refresh(account)

        logger.info(f"New Stripe account connected: {stripe_account_id}")
        return account

    async def disconnect_account(
        self,
        stripe_account_id: str,
    ) -> bool:
        """
        Handle account disconnection/deauthorization.

        Args:
            stripe_account_id: Stripe account ID

        Returns:
            bool: True if account was found and updated
        """
        account = await self.get_account_by_stripe_id(stripe_account_id)

        if not account:
            logger.warning(f"Disconnect for unknown account: {stripe_account_id}")
            return False

        account.is_active = False
        account.disconnected_at = datetime.utcnow()
        account.access_token = None
        account.refresh_token = None

        await self.db.commit()
        logger.info(f"Account disconnected: {stripe_account_id}")
        return True

    async def connect_brand(
        self,
        account_id: UUID,
        brand_id: UUID,
    ) -> StripeConnectedAccount:
        """
        Connect account to an Affilync brand.

        Args:
            account_id: Account ID
            brand_id: Affilync brand ID

        Returns:
            Updated account
        """
        account = await self.get_account_by_id(account_id)
        if not account:
            raise ValueError(f"Account not found: {account_id}")

        account.brand_id = brand_id
        account.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(account)

        logger.info(f"Account {account.stripe_account_id} connected to brand {brand_id}")
        return account

    async def disconnect_brand(
        self,
        account_id: UUID,
    ) -> StripeConnectedAccount:
        """
        Disconnect account from Affilync brand.

        Args:
            account_id: Account ID

        Returns:
            Updated account
        """
        account = await self.get_account_by_id(account_id)
        if not account:
            raise ValueError(f"Account not found: {account_id}")

        account.brand_id = None
        account.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(account)

        logger.info(f"Account {account.stripe_account_id} disconnected from brand")
        return account

    async def update_settings(
        self,
        account_id: UUID,
        **settings_update,
    ) -> StripeConnectedAccount:
        """
        Update account settings.

        Args:
            account_id: Account ID
            **settings_update: Settings to update

        Returns:
            Updated account
        """
        account = await self.get_account_by_id(account_id)
        if not account:
            raise ValueError(f"Account not found: {account_id}")

        # Update individual fields
        if "commission_rate" in settings_update:
            account.commission_rate = settings_update["commission_rate"]
        if "commission_type" in settings_update:
            account.commission_type = settings_update["commission_type"]
        if "tracking_enabled" in settings_update:
            account.tracking_enabled = settings_update["tracking_enabled"]

        # Update settings JSON
        if "settings" in settings_update:
            current = account.settings or {}
            current.update(settings_update["settings"])
            account.settings = current

        account.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(account)
        return account

    async def sync_account_status(
        self,
        account: StripeConnectedAccount,
    ) -> StripeConnectedAccount:
        """
        Sync account status from Stripe.

        Args:
            account: Account to sync

        Returns:
            Updated account
        """
        try:
            client = StripeClient(account.stripe_account_id)
            account_info = await client.get_account()

            account.charges_enabled = account_info.get("charges_enabled", False)
            account.payouts_enabled = account_info.get("payouts_enabled", False)
            account.business_name = account_info.get("business_profile", {}).get("name")
            account.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(account)

            return account

        except Exception as e:
            logger.error(f"Failed to sync account status: {e}")
            raise
