"""Health check endpoints."""

import structlog
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

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
