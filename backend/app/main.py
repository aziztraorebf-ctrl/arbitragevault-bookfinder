"""ArbitrageVault FastAPI application main entry point.

IMPORTANT: This app uses FLAT settings structure (settings.app_name, NOT settings.app.app_name)
Compatible with Pydantic V2 - render deployment v52dd65d+
"""

# === CRITICAL: Windows Event Loop Configuration MUST be first ===
# ProactorEventLoop (Windows default) is incompatible with psycopg3
# This MUST execute BEFORE any other imports that might create event loops
import sys
if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# ===================================================================

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Optional MCP integration
try:
    from fastapi_mcp import FastApiMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

from app.api.v1.routers import auth, health, analyses, batches, keepa, config, autosourcing, autoscheduler, views
from app.api.v1.endpoints import products, niches
from app.routers import stock_estimate, strategic_views, niche_discovery, bookmarks
from app.core.cors import configure_cors
from app.core.db import lifespan
from app.core.logging import configure_logging, get_logger, log_request_middleware
from app.core.settings import get_settings

# Configure logging first - DISABLED FOR PHASE 1
# configure_logging()
# logger = get_logger("main")
import logging
logger = logging.getLogger("main")

# Get settings
settings = get_settings()

# Initialize Sentry SDK
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1,  # 10% des transactions pour performance monitoring
        profiles_sample_rate=0.1,  # 10% profiling
        environment=settings.environment,
        release=settings.version,
    )
    logger.info(f"Sentry initialized for environment: {settings.environment}")
else:
    logger.warning("SENTRY_DSN not configured - Sentry disabled")


# Create FastAPI application with lifespan
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="FastAPI backend for book arbitrage analysis with Keepa integration",
    lifespan=lifespan,
    docs_url="/docs" if settings.enable_docs else None,
    redoc_url="/redoc" if settings.enable_redoc else None,
    openapi_url="/openapi.json"
    if settings.enable_docs or settings.enable_redoc
    else None,
)

# Configure CORS
configure_cors(app)

# Add request logging middleware - DISABLED FOR PHASE 1
# app.middleware("http")(log_request_middleware)

# Include routers
app.include_router(health.router, prefix="/api/v1/health", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(analyses.router, prefix="/api/v1/analyses", tags=["Analyses"])
app.include_router(batches.router, prefix="/api/v1/batches", tags=["Batches"])
app.include_router(keepa.router, prefix="/api/v1/keepa", tags=["Keepa"])
app.include_router(products.router, prefix="/api/v1/products", tags=["Product Discovery"])
app.include_router(niches.router, prefix="/api/v1/niches", tags=["Niche Discovery"])
app.include_router(config.router, prefix="/api/v1", tags=["Configuration"])
app.include_router(views.router, prefix="/api/v1", tags=["Views"])
app.include_router(autosourcing.router, prefix="/api/v1", tags=["AutoSourcing"])
app.include_router(autoscheduler.router, prefix="/api/v1", tags=["AutoScheduler Control"])
app.include_router(stock_estimate.router, tags=["Stock Estimate"])
app.include_router(strategic_views.router, tags=["Strategic Views"])
app.include_router(niche_discovery.router, tags=["Niche Discovery"])
app.include_router(bookmarks.router, prefix="/api/v1", tags=["Bookmarks"])

# === MCP INTEGRATION ===
# Mount FastAPI-MCP server if available (optional for production)
print(f"[MCP DEBUG] MCP_AVAILABLE = {MCP_AVAILABLE}")
if MCP_AVAILABLE:
    try:
        print("[MCP DEBUG] Attempting to mount MCP server...")
        mcp_server = FastApiMCP(app)
        mcp_server.mount_sse()  # Using SSE transport for Claude Code compatibility
        print("[MCP SUCCESS] FastAPI-MCP server mounted at /mcp endpoint (SSE transport)")
    except Exception as e:
        print(f"[MCP ERROR] Failed to mount FastAPI-MCP server: {e}")
        import traceback
        traceback.print_exc()
else:
    print("[MCP INFO] FastAPI-MCP not installed - running without MCP support")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        method=request.method,
    )

    if settings.debug:
        # In debug mode, return detailed error information
        return JSONResponse(
            status_code=500,
            content={
                "code": "internal_server_error",
                "message": "Internal server error",
                "details": str(exc) if settings.debug else None,
                "error_type": type(exc).__name__,
            },
        )
    else:
        # In production, return generic error message
        return JSONResponse(
            status_code=500,
            content={
                "code": "internal_server_error",
                "message": "Internal server error",
            },
        )


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint redirect to docs."""
    return {
        "message": "ArbitrageVault API",
        "version": settings.version,
        "docs": "/docs" if settings.enable_docs else None,
        "redoc": "/redoc" if settings.enable_redoc else None,
    }


@app.get("/health", include_in_schema=False)
async def health():
    """Simple health check endpoint for Render deployment monitoring."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    import asyncio
    import sys

    # Fix for Windows: Use SelectorEventLoop for psycopg3 compatibility
    # ProactorEventLoop (default on Windows) is not compatible with psycopg3 async
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_config=None,  # Use our custom logging configuration
    )

