"""Database configuration and session management."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
# from sqlalchemy.pool import QueuePool  # Not compatible with async

from .settings import get_settings

logger = structlog.get_logger()


class Base(DeclarativeBase):
    """Base class for all database models."""



class DatabaseManager:
    """Database connection manager."""

    def __init__(self):
        self._engine: AsyncEngine | None = None
        self._session_maker: async_sessionmaker[AsyncSession] | None = None

    async def initialize(self) -> None:
        """Initialize database engine and session maker."""
        settings = get_settings()

        # SSL configuration for Render PostgreSQL 
        connect_args = {}
        if "render.com" in settings.database_url:
            # asyncpg requires ssl='require' instead of sslmode=require
            connect_args = {"ssl": "require"}

        self._engine = create_async_engine(
            settings.database_url,
            # Connection pool optimized for Render Basic PostgreSQL (256MB)
            # FIXED: Increased pool for concurrent operations on /analyses /batches
            pool_size=5,           # Increased from 2 - more concurrent connections
            max_overflow=10,       # Increased from 5 - handle traffic spikes
            pool_timeout=60,       # Increased from 30 - longer timeout for DB ops
            pool_recycle=1800,     # Recycle connections after 30 minutes
            pool_pre_ping=True,    # Verify connection liveness
            echo=settings.debug,   # SQL logging in debug mode
            echo_pool=settings.debug,
            connect_args=connect_args,
        )

        self._session_maker = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        logger.info(
            "Database initialized",
            database_url=settings.database_url.split("@")[1]
            if "@" in settings.database_url
            else "***",
        )

    async def close(self) -> None:
        """Close database engine."""
        if self._engine:
            await self._engine.dispose()
            logger.info("Database engine closed")

    async def get_session(self) -> AsyncSession:
        """Get database session."""
        if not self._session_maker:
            raise RuntimeError("Database not initialized")
        return self._session_maker()

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Context manager for database sessions."""
        session = await self.get_session()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            if not self._engine:
                return False

            async with self._engine.begin() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return False


# Global database manager instance
db_manager = DatabaseManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get database session."""
    async with db_manager.session() as session:
        yield session


@asynccontextmanager
async def lifespan(app):
    """FastAPI lifespan context manager."""
    # Startup
    logger.info("Starting up application")
    await db_manager.initialize()

    yield

    # Shutdown
    logger.info("Shutting down application")
    await db_manager.close()
