"""
OAuth Routes for Stripe Connect
Handles the OAuth flow for connecting Stripe accounts
"""

import json
import logging
import secrets
from datetime import datetime, timedelta

import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.middleware.auth import require_auth
from app.services.account_service import AccountService

logger = logging.getLogger(__name__)

router = APIRouter()

# Redis-backed state store with in-memory fallback
_fallback_states: dict = {}
_redis_client = None


async def _get_redis():
    """Get or create Redis client for OAuth state."""
    global _redis_client
    if _redis_client is None:
        try:
            import redis.asyncio as aioredis

            _redis_client = aioredis.from_url(
                settings.redis_url, encoding="utf-8", decode_responses=True
            )
            await _redis_client.ping()
        except Exception as e:
            logger.warning(f"Redis unavailable for OAuth state: {e}")
            _redis_client = None
    return _redis_client


async def _store_state(state: str) -> None:
    """Store OAuth state in Redis (or fallback to memory)."""
    redis = await _get_redis()
    if redis:
        try:
            await redis.setex(f"oauth_state:sc:{state}", 600, json.dumps({"used": False}))
            return
        except Exception:
            pass
    # Fallback: clean expired + store in memory
    cutoff = datetime.utcnow() - timedelta(minutes=10)
    expired = [k for k, v in _fallback_states.items() if v["created_at"] < cutoff]
    for k in expired:
        del _fallback_states[k]
    _fallback_states[state] = {"created_at": datetime.utcnow(), "used": False}


async def _validate_state(state: str) -> bool:
    """Validate and consume OAuth state. Returns True if valid."""
    redis = await _get_redis()
    if redis:
        try:
            key = f"oauth_state:sc:{state}"
            data = await redis.get(key)
            if not data:
                return False
            parsed = json.loads(data)
            if parsed.get("used"):
                return False
            await redis.setex(key, 60, json.dumps({"used": True}))
            return True
        except Exception:
            pass
    # Fallback
    if state not in _fallback_states:
        return False
    data = _fallback_states.pop(state)
    return not data.get("used")


@router.get("/connect")
async def start_connect():
    """
    Start Stripe Connect OAuth flow.

    Generates a state token and redirects to Stripe Connect authorization.
    """
    # Generate state token and store in Redis
    state = secrets.token_urlsafe(32)
    await _store_state(state)

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

    # Validate state via Redis (or fallback)
    if not state or not await _validate_state(state):
        logger.warning("Invalid or expired OAuth state")
        return RedirectResponse(
            url=f"{settings.frontend_url}/connect?error=invalid_state"
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

        # Deliver JWT via HTTP-only cookie instead of URL parameter (SEC-XI-08)
        response = RedirectResponse(
            url=f"{settings.frontend_url}/dashboard",
            status_code=302,
        )
        response.set_cookie(
            key="auth_token",
            value=token,
            max_age=settings.jwt_expire_minutes * 60,
            secure=True,
            httponly=True,
            samesite="lax",
            path="/",
        )
        return response

    except Exception as e:
        logger.exception(f"OAuth callback error: {e}")
        return RedirectResponse(
            url=f"{settings.frontend_url}/connect?error=connection_failed"
        )


@router.post("/deauthorize")
async def deauthorize(
    stripe_account_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(require_auth),
):
    """
    Handle account deauthorization request from authenticated user.

    Requires the caller to be authenticated and own the account being
    deauthorized (verified via JWT stripe_account_id claim).
    """
    # Verify account ownership for JWT-authenticated users
    if auth.get("type") == "jwt":
        if auth.get("stripe_account_id") != stripe_account_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot deauthorize an account you do not own",
            )

    account_service = AccountService(db)
    await account_service.disconnect_account(stripe_account_id)

    return {"status": "deauthorized", "stripe_account_id": stripe_account_id}
