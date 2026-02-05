"""
Encryption utilities for Stripe Connect integration.
Wraps the shared affilync-integrations-common library.
"""

from affilync_integrations.encryption import (
    TokenEncryption,
    mask_token,
)

from app.config import settings

# Configure encryption with Stripe-specific salt
_encryption = TokenEncryption(settings.encryption_key, salt_suffix="stripe-connect")


def encrypt_token(token: str) -> str:
    """
    Encrypt an access token for storage.

    Args:
        token: Plain text token

    Returns:
        Encrypted token string
    """
    return _encryption.encrypt(token)


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt an access token from storage.

    Args:
        encrypted_token: Encrypted token string

    Returns:
        Plain text token
    """
    return _encryption.decrypt(encrypted_token)


__all__ = [
    "encrypt_token",
    "decrypt_token",
    "mask_token",
]
