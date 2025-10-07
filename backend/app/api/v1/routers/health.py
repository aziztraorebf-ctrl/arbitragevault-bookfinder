"""Health check endpoints."""

import structlog
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sentry_sdk import capture_exception, capture_message

from app.core.db import db_manager
from app.core.settings import get_settings

logger = structlog.get_logger()
router = APIRouter()


@router.get("/live")
async def liveness_check():
    """
    Liveness probe - check if application is running.

    Returns:
        200: Application is alive
    """
    settings = get_settings()

    return {
        "status": "alive",
        "service": settings.app_name,
        "version": settings.version,
        "environment": settings.app_env,
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness probe - check if application is ready to serve traffic.

    Returns:
        200: Application is ready (database connected)
        503: Application is not ready (database issues)
    """
    settings = get_settings()

    # Check database connectivity
    db_healthy = await db_manager.health_check()

    if not db_healthy:
        logger.error("Readiness check failed - database unhealthy")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "service": settings.app_name,
                "version": settings.version,
                "environment": settings.app_env,
                "checks": {"database": "unhealthy"},
            },
        )

    return {
        "status": "ready",
        "service": settings.app_name,
        "version": settings.version,
        "environment": settings.app_env,
        "checks": {"database": "healthy"},
    }


@router.get("/sentry-test")
async def sentry_test():
    """
    Test endpoint to verify Sentry integration.

    This endpoint will intentionally:
    1. Send a test message to Sentry
    2. Raise an exception that will be captured

    Returns:
        200: Sentry test executed (check Sentry dashboard for events)
    """
    settings = get_settings()

    if not settings.sentry_dsn:
        return {
            "status": "disabled",
            "message": "Sentry is not configured (SENTRY_DSN missing)"
        }

    # Send a test message
    capture_message("Sentry test message from ArbitrageVault API", level="info")

    # Test exception capture
    try:
        # Intentional error for testing
        raise ValueError("Test exception from /health/sentry-test endpoint")
    except Exception as e:
        capture_exception(e)

    return {
        "status": "success",
        "message": "Sentry test events sent",
        "environment": settings.environment,
        "sentry_configured": True,
        "note": "Check your Sentry dashboard at https://aziz-traore.sentry.io"
    }
