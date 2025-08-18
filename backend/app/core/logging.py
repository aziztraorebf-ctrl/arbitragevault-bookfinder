"""Structured logging configuration."""

import uuid
from contextvars import ContextVar
from typing import Any, Dict

import structlog
import uvicorn.logging
from fastapi import Request

from .settings import get_settings

# Context variables for request tracing
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")
user_id_ctx: ContextVar[str] = ContextVar("user_id", default="")


def add_request_id(logger, method_name, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add request ID to log entries."""
    request_id = request_id_ctx.get("")
    if request_id:
        event_dict["request_id"] = request_id
    return event_dict


def add_user_id(logger, method_name, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add user ID to log entries."""
    user_id = user_id_ctx.get("")
    if user_id:
        event_dict["user_id"] = user_id
    return event_dict


def add_timestamp(logger, method_name, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add ISO timestamp to log entries."""
    import datetime

    event_dict["timestamp"] = datetime.datetime.utcnow().isoformat() + "Z"
    return event_dict


def configure_logging() -> None:
    """Configure structured logging for the application."""
    settings = get_settings()

    # Configure structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        add_request_id,
        add_user_id,
        add_timestamp,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.log_format.lower() == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.extend(
            [
                structlog.dev.ConsoleRenderer(colors=True),
            ]
        )

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure uvicorn logging to use structlog
    if settings.log_format.lower() == "json":

        class StructlogHandler:
            def __init__(self):
                self.logger = structlog.get_logger("uvicorn")

            def emit(self, record):
                level = record.levelname.lower()
                msg = record.getMessage()

                # Extract extra fields from record
                extra = {}
                for key, value in record.__dict__.items():
                    if key not in (
                        "name",
                        "msg",
                        "args",
                        "levelname",
                        "levelno",
                        "pathname",
                        "filename",
                        "module",
                        "lineno",
                        "funcName",
                        "created",
                        "msecs",
                        "relativeCreated",
                        "thread",
                        "threadName",
                        "processName",
                        "process",
                    ):
                        extra[key] = value

                getattr(self.logger, level)(msg, **extra)

        # Override uvicorn's logging
        for name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
            logger = uvicorn.logging.logging.getLogger(name)
            logger.handlers = [StructlogHandler()]


async def log_request_middleware(request: Request, call_next):
    """Middleware to log requests with timing and tracing."""
    import time

    # Generate request ID
    request_id = str(uuid.uuid4())
    request_id_ctx.set(request_id)

    # Add request ID to response headers
    start_time = time.time()

    logger = structlog.get_logger("request")
    logger.info(
        "Request started",
        method=request.method,
        path=request.url.path,
        query_params=str(request.query_params),
        client_host=request.client.host if request.client else None,
    )

    try:
        response = await call_next(request)

        # Calculate response time
        process_time = (time.time() - start_time) * 1000  # Convert to ms

        logger.info(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            latency_ms=round(process_time, 2),
        )

        # Add timing header
        response.headers["X-Process-Time"] = str(round(process_time, 2))
        response.headers["X-Request-ID"] = request_id

        return response

    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.error(
            "Request failed",
            method=request.method,
            path=request.url.path,
            latency_ms=round(process_time, 2),
            error=str(e),
            error_type=type(e).__name__,
        )
        raise
    finally:
        # Clear context variables
        request_id_ctx.set("")
        user_id_ctx.set("")


def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def set_user_context(user_id: str) -> None:
    """Set user ID in logging context."""
    user_id_ctx.set(user_id)
