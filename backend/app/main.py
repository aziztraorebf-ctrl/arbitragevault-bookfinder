"""ArbitrageVault FastAPI application main entry point."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.routers import auth, health, analyses, batches, keepa, config, autosourcing, autoscheduler
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
app.include_router(config.router, prefix="/api/v1", tags=["Configuration"])
app.include_router(autosourcing.router, prefix="/api/v1", tags=["AutoSourcing"])
app.include_router(autoscheduler.router, prefix="/api/v1", tags=["AutoScheduler Control"])
app.include_router(stock_estimate.router, tags=["Stock Estimate"])
app.include_router(strategic_views.router, tags=["Strategic Views"])
app.include_router(niche_discovery.router, tags=["Niche Discovery"])
app.include_router(bookmarks.router, tags=["Bookmarks"])


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_config=None,  # Use our custom logging configuration
    )
