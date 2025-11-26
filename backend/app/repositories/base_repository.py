"""Enhanced base repository with advanced pagination and filtering."""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from enum import Enum

import structlog
from sqlalchemy import asc, desc, func, select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.models.base import Base
from app.core.pagination import Page
from app.core.exceptions import InvalidFilterFieldError

logger = structlog.get_logger()

ModelType = TypeVar("ModelType", bound=Base)


class SortOrder(str, Enum):
    """Sort order enumeration."""
    ASC = "asc"
    DESC = "desc"


class FilterOperator(str, Enum):
    """Filter operator enumeration."""
    EQ = "eq"        # Equal
    IN = "in"        # In list
    GTE = "gte"      # Greater than or equal
    LTE = "lte"      # Less than or equal
    GT = "gt"        # Greater than
    LT = "lt"        # Less than


class BaseRepository(Generic[ModelType]):
    """Enhanced base repository with advanced CRUD, pagination, and filtering."""

    # Subclasses should override these
    SORTABLE_FIELDS: List[str] = ["id", "created_at"]
    FILTERABLE_FIELDS: List[str] = ["id"]

    def __init__(self, db_session: AsyncSession, model: Type[ModelType]):
        self.db = db_session
        self.model = model

    def _validate_sort_fields(self, sort_by: List[str]) -> None:
        """Validate that sort fields are in whitelist."""
        invalid_fields = [field for field in sort_by if field not in self.SORTABLE_FIELDS]
        if invalid_fields:
            raise InvalidFilterFieldError(
                field=", ".join(invalid_fields), 
                allowed_fields=self.SORTABLE_FIELDS
            )

    def _validate_filter_fields(self, filters: Dict[str, Any]) -> None:
        """Validate that filter fields are in whitelist."""
        invalid_fields = [field for field in filters.keys() if field not in self.FILTERABLE_FIELDS]
        if invalid_fields:
            raise InvalidFilterFieldError(
                field=", ".join(invalid_fields), 
                allowed_fields=self.FILTERABLE_FIELDS
            )

    def _apply_sorting(self, query: Select, sort_by: List[str], sort_order: List[SortOrder]) -> Select:
        """Apply multi-column sorting with stable tiebreak."""
        if not sort_by:
            # Default stable sort
            return query.order_by(asc(self.model.id))

        self._validate_sort_fields(sort_by)
        
        # Apply requested sorts
        for field, order in zip(sort_by, sort_order):
            column = getattr(self.model, field)
            if order == SortOrder.DESC:
                query = query.order_by(desc(column))
            else:
                query = query.order_by(asc(column))
        
        # Always add stable tiebreak if id not already in sort
        if "id" not in sort_by:
            query = query.order_by(asc(self.model.id))
            
        return query

    def _apply_filters(self, query: Select, filters: Dict[str, Any]) -> Select:
        """Apply filters with various operators."""
        if not filters:
            return query

        self._validate_filter_fields(filters)

        for field_name, filter_value in filters.items():
            if filter_value is None:
                continue

            column = getattr(self.model, field_name)

            # Handle different filter formats
            if isinstance(filter_value, dict):
                # Complex filter: {"operator": "gte", "value": 100}
                operator = FilterOperator(filter_value.get("operator", "eq"))
                value = filter_value.get("value")

                if operator == FilterOperator.EQ:
                    query = query.where(column == value)
                elif operator == FilterOperator.IN:
                    query = query.where(column.in_(value))
                elif operator == FilterOperator.GTE:
                    query = query.where(column >= value)
                elif operator == FilterOperator.LTE:
                    query = query.where(column <= value)
                elif operator == FilterOperator.GT:
                    query = query.where(column > value)
                elif operator == FilterOperator.LT:
                    query = query.where(column < value)
            else:
                # Simple filter: direct equality
                query = query.where(column == filter_value)

        return query

    async def list(
        self,
        offset: int = 0,
        limit: int = 100,
        sort_by: Optional[List[str]] = None,
        sort_order: Optional[List[SortOrder]] = None,
        filters: Optional[Dict[str, Any]] = None,
        query_options: Optional[List[Any]] = None
    ) -> Page[ModelType]:
        """
        List records with advanced pagination, sorting, and filtering.
        
        Args:
            offset: Number of records to skip
            limit: Maximum number of records to return
            sort_by: List of fields to sort by
            sort_order: List of sort orders (asc/desc) corresponding to sort_by
            filters: Dictionary of filters to apply
            
        Returns:
            Page containing items and pagination metadata
        """
        try:
            sort_by = sort_by or []
            sort_order = sort_order or [SortOrder.ASC] * len(sort_by)
            filters = filters or {}

            # Ensure sort_order matches sort_by length
            if len(sort_order) < len(sort_by):
                sort_order.extend([SortOrder.ASC] * (len(sort_by) - len(sort_order)))

            # Build base query
            query = select(self.model)
            
            # Apply filters
            query = self._apply_filters(query, filters)
            
            # Get total count (before pagination)
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.db.execute(count_query)
            total = total_result.scalar()

            # Apply sorting and pagination
            query = self._apply_sorting(query, sort_by, sort_order)
            query = query.offset(offset).limit(limit)
            
            # Apply query options (like eager loading)
            if query_options:
                query = query.options(*query_options)

            # Execute query
            result = await self.db.execute(query)
            items = result.scalars().all()

            logger.info(
                "Listed records",
                model=self.model.__name__,
                total=total,
                returned=len(items),
                offset=offset,
                limit=limit,
                filters=filters
            )

            return Page.create(items=list(items), total=total, offset=offset, limit=limit)

        except Exception as e:
            logger.error(
                "Failed to list records",
                model=self.model.__name__,
                error=str(e),
                offset=offset,
                limit=limit
            )
            raise

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

    async def update(self, id: str, **kwargs) -> Optional[ModelType]:
        """Update record by ID."""
        try:
            from datetime import datetime, timezone

            # Remove None values and forbidden fields
            update_data = {
                k: v
                for k, v in kwargs.items()
                if v is not None and k not in ("id", "created_at", "updated_at")
            }

            # Automatically set updated_at (timezone-aware)
            update_data["updated_at"] = datetime.now(timezone.utc)

            if not update_data or (len(update_data) == 1 and "updated_at" in update_data):
                # Nothing to update besides updated_at
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

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filters."""
        try:
            filters = filters or {}
            query = select(func.count(self.model.id))
            query = self._apply_filters(query, filters)

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

    async def get_filtered(
        self, 
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        sort_field: str = "created_at",
        sort_order: SortOrder = SortOrder.DESC
    ) -> List[ModelType]:
        """Get filtered records with pagination and sorting."""
        try:
            filters = filters or {}
            self._validate_filter_fields(filters)
            self._validate_sort_fields([sort_field])

            query = select(self.model)
            query = self._apply_filters(query, filters)
            query = self._apply_sorting(query, [sort_field], [sort_order])

            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)

            # Context7 SQLAlchemy 2.0: Check session active before execute
            if not self.db.is_active:
                raise RuntimeError("Database session is not active")
            
            result = await self.db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(
                "Failed to get filtered records", 
                model=self.model.__name__, 
                error=str(e)
            )
            raise

    async def get_all(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        sort_field: str = "created_at",
        sort_order: SortOrder = SortOrder.DESC
    ) -> List[ModelType]:
        """Get all records with pagination and sorting."""
        try:
            self._validate_sort_fields([sort_field])

            query = select(self.model)
            query = self._apply_sorting(query, [sort_field], [sort_order])

            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)

            # Context7 SQLAlchemy 2.0: Check session active before execute
            if not self.db.is_active:
                raise RuntimeError("Database session is not active")
            
            result = await self.db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(
                "Failed to get all records", 
                model=self.model.__name__, 
                error=str(e)
            )
            raise

    async def count_filtered(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count filtered records."""
        try:
            filters = filters or {}
            self._validate_filter_fields(filters)

            query = select(func.count(self.model.id))
            query = self._apply_filters(query, filters)

            result = await self.db.execute(query)
            return result.scalar()

        except Exception as e:
            logger.error(
                "Failed to count filtered records", 
                model=self.model.__name__, 
                error=str(e)
            )
            raise