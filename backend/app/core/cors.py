"""CORS configuration."""

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .settings import get_settings

logger = structlog.get_logger()


def configure_cors(app: FastAPI) -> None:
    """Configure CORS middleware for the FastAPI application."""
    settings = get_settings()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "X-Request-ID",
        ],
        expose_headers=[
            "X-Process-Time",
            "X-Request-ID",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
        ],
    )

    logger.info(
        "CORS configured",
        allowed_origins=settings.cors_allowed_origins,
        allow_credentials=True,
    )
