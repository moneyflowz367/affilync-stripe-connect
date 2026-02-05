"""
OAuth Routes for Stripe Connect
Handles the OAuth flow for connecting Stripe accounts
"""

import logging
import secrets
from datetime import datetime, timedelta

import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.services.account_service import AccountService

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory state store (use Redis in production)
_oauth_states: dict = {}


@router.get("/connect")
async def start_connect():
    """
    Start Stripe Connect OAuth flow.

    Generates a state token and redirects to Stripe Connect authorization.
    """
    # Generate state token
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = {
        "created_at": datetime.utcnow(),
        "used": False,
    }

    # Clean up old states
    cutoff = datetime.utcnow() - timedelta(minutes=10)
    _oauth_states.clear()
    _oauth_states[state] = {"created_at": datetime.utcnow(), "used": False}

    # Build authorization URL
    account_service = AccountService(None)
    auth_url = account_service.get_oauth_url(state)

    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def oauth_callback(
    code: str = Query(None),
    state: str = Query(None),
    error: str = Query(None),
    error_description: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    OAuth callback handler.

    Stripe redirects here after the user authorizes (or denies) the connection.
    """
    # Handle errors
    if error:
        logger.error(f"OAuth error: {error} - {error_description}")
        return RedirectResponse(
            url=f"{settings.frontend_url}/connect?error={error}"
        )

    # Validate state
    if not state or state not in _oauth_states:
        logger.warning("Invalid OAuth state")
        return RedirectResponse(
            url=f"{settings.frontend_url}/connect?error=invalid_state"
        )

    state_data = _oauth_states.pop(state)
    if state_data.get("used"):
        return RedirectResponse(
            url=f"{settings.frontend_url}/connect?error=state_reused"
        )

    if not code:
        return RedirectResponse(
            url=f"{settings.frontend_url}/connect?error=no_code"
        )

    try:
        # Complete OAuth
        account_service = AccountService(db)
        account = await account_service.complete_oauth(code)

        # Generate JWT for frontend
        token = jwt.encode(
            {
                "account_id": str(account.id),
                "stripe_account_id": account.stripe_account_id,
                "exp": datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes),
            },
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

        # Redirect to dashboard with token
        return RedirectResponse(
            url=f"{settings.frontend_url}/dashboard?token={token}&account_id={account.id}"
        )

    except Exception as e:
        logger.exception(f"OAuth callback error: {e}")
        return RedirectResponse(
            url=f"{settings.frontend_url}/connect?error=connection_failed"
        )


@router.get("/deauthorize")
async def deauthorize(
    stripe_account_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle account deauthorization request from user.
    """
    # This would typically require authentication
    # For now, just log and acknowledge

    account_service = AccountService(db)
    await account_service.disconnect_account(stripe_account_id)

    return {"status": "deauthorized", "stripe_account_id": stripe_account_id}
