"""
Configuration settings for Stripe Connect integration
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App identification
    app_name: str = "Affilync Stripe Connect"
    app_version: str = "1.0.0"
    environment: str = "production"
    debug: bool = False

    # CORS
    cors_origins: list[str] = [
        "https://app.affilync.com",
        "https://connect.affilync.com",
    ]

    # Stripe Configuration
    stripe_client_id: str  # Stripe Connect platform client ID
    stripe_secret_key: str  # Stripe platform secret key
    stripe_webhook_secret: str  # Webhook endpoint signing secret
    stripe_publishable_key: str = ""

    # Affilync API
    affilync_api_url: str = "https://api.affilync.com"
    affilync_api_key: str

    # Database
    database_url: str

    # Redis (for sessions and rate limiting)
    redis_url: str = "redis://localhost:6379"

    # Security
    encryption_key: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60  # 1 hour (was 7 days — reduced per SEC-XI-08)

    # App URLs
    app_url: str = "https://connect.affilync.com"
    frontend_url: str = "https://connect.affilync.com"

    # Webhook tolerance (seconds)
    webhook_tolerance: int = 300

    # Rate limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
