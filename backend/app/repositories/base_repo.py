"""Base repository class with common database operations."""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

import structlog
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

logger = structlog.get_logger()

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations."""

    def __init__(self, db_session: AsyncSession, model: Type[ModelType]):
        self.db = db_session
        self.model = model

    async def create(self, **kwargs) -> ModelType:
        """Create a new record."""
        try:
            instance = self.model(**kwargs)
            self.db.add(instance)
            await self.db.commit()
            await self.db.refresh(instance)

            logger.info("Record created", model=self.model.__name__, id=instance.id)
            return instance

        except Exception as e:
            await self.db.rollback()
            logger.error(
                "Failed to create record", model=self.model.__name__, error=str(e)
            )
            raise

    async def get_by_id(self, id: str) -> Optional[ModelType]:
        """Get record by ID."""
        try:
            result = await self.db.execute(
                select(self.model).where(self.model.id == id)
            )
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(
                "Failed to get record by ID",
                model=self.model.__name__,
                id=id,
                error=str(e),
            )
            raise

    async def get_multi(
        self, skip: int = 0, limit: int = 100, **filters
    ) -> List[ModelType]:
        """Get multiple records with pagination and filters."""
        try:
            query = select(self.model)

            # Apply filters
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.where(getattr(self.model, key) == value)

            # Apply pagination
            query = query.offset(skip).limit(limit)

            result = await self.db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(
                "Failed to get multiple records",
                model=self.model.__name__,
                error=str(e),
            )
            raise

    async def update(self, id: str, **kwargs) -> Optional[ModelType]:
        """Update record by ID."""
        try:
            # Remove None values and forbidden fields
            update_data = {
                k: v
                for k, v in kwargs.items()
                if v is not None and k not in ("id", "created_at")
            }

            if not update_data:
                # Nothing to update
                return await self.get_by_id(id)

            stmt = (
                update(self.model)
                .where(self.model.id == id)
                .values(**update_data)
                .returning(self.model)
            )

            result = await self.db.execute(stmt)
            updated_instance = result.scalar_one_or_none()

            if updated_instance:
                await self.db.commit()
                logger.info(
                    "Record updated",
                    model=self.model.__name__,
                    id=id,
                    updated_fields=list(update_data.keys()),
                )

            return updated_instance

        except Exception as e:
            await self.db.rollback()
            logger.error(
                "Failed to update record",
                model=self.model.__name__,
                id=id,
                error=str(e),
            )
            raise

    async def delete(self, id: str) -> bool:
        """Delete record by ID."""
        try:
            stmt = delete(self.model).where(self.model.id == id)
            result = await self.db.execute(stmt)

            if result.rowcount > 0:
                await self.db.commit()
                logger.info("Record deleted", model=self.model.__name__, id=id)
                return True

            return False

        except Exception as e:
            await self.db.rollback()
            logger.error(
                "Failed to delete record",
                model=self.model.__name__,
                id=id,
                error=str(e),
            )
            raise

    async def count(self, **filters) -> int:
        """Count records with optional filters."""
        try:
            query = select(func.count(self.model.id))

            # Apply filters
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.where(getattr(self.model, key) == value)

            result = await self.db.execute(query)
            return result.scalar()

        except Exception as e:
            logger.error(
                "Failed to count records", model=self.model.__name__, error=str(e)
            )
            raise

    async def exists(self, id: str) -> bool:
        """Check if record exists by ID."""
        try:
            query = select(self.model.id).where(self.model.id == id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none() is not None

        except Exception as e:
            logger.error(
                "Failed to check record existence",
                model=self.model.__name__,
                id=id,
                error=str(e),
            )
            raise

    async def get_or_create(
        self, defaults: Dict[str, Any] = None, **kwargs
    ) -> tuple[ModelType, bool]:
        """Get existing record or create new one."""
        try:
            # Try to get existing record
            query = select(self.model)
            for key, value in kwargs.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)

            result = await self.db.execute(query)
            existing = result.scalar_one_or_none()

            if existing:
                return existing, False

            # Create new record
            create_data = kwargs.copy()
            if defaults:
                create_data.update(defaults)

            instance = await self.create(**create_data)
            return instance, True

        except Exception as e:
            logger.error(
                "Failed to get or create record",
                model=self.model.__name__,
                error=str(e),
            )
            raise
