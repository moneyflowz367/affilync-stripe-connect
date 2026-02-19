"""
Stripe Connect Integration Service
FastAPI application for managing Stripe Connect accounts and tracking conversions
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine, Base
from app.middleware.rate_limit import RateLimitMiddleware, get_limiter
from app.routes import oauth, webhooks, api

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Stripe Connect service...")

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables created")
    logger.info(f"Environment: {settings.environment}")

    yield

    # Shutdown
    logger.info("Shutting down Stripe Connect service...")
    await engine.dispose()


# Create FastAPI application
app = FastAPI(
    title="Affilync Stripe Connect",
    description="Stripe Connect integration for affiliate conversion tracking",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept"],
    max_age=3600,
)

# Add rate limiting (shared library: Redis-backed with in-memory fallback)
app.add_middleware(RateLimitMiddleware, limiter=get_limiter())


# Health check endpoint
@app.get("/")
@app.get("/health")
@app.get("/healthz")
async def health_check():
    """Health check endpoint for load balancers."""
    return {
        "status": "healthy",
        "service": "affilync-stripe-connect",
        "version": "1.0.0",
    }


# Include routers
app.include_router(
    oauth.router,
    prefix="/oauth",
    tags=["OAuth"],
)

app.include_router(
    webhooks.router,
    prefix="/webhooks",
    tags=["Webhooks"],
)

app.include_router(
    api.router,
    prefix="/api",
    tags=["API"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle uncaught exceptions."""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
    )
