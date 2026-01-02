"""Unit tests for SearchResultService."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.services.search_result_service import SearchResultService
from app.schemas.search_result import SearchResultCreate, SearchResultUpdate, SearchSourceEnum
from app.models.search_result import SearchResult


class TestSearchResultService:
    """Tests for SearchResultService."""

    @pytest.fixture
    def mock_db(self):
        """Create mock async session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.delete = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create service with mock db."""
        return SearchResultService(mock_db)

    @pytest.mark.asyncio
    async def test_create_search_result(self, service, mock_db):
        """Test creating a search result."""
        data = SearchResultCreate(
            name="Test Search",
            source=SearchSourceEnum.NICHE_DISCOVERY,
            products=[{"asin": "B123", "title": "Test"}],
            search_params={"strategy": "textbook"}
        )

        # Mock refresh to set attributes
        async def mock_refresh(obj):
            obj.id = "test-uuid"
            obj.created_at = datetime.utcnow()
            obj.expires_at = datetime.utcnow() + timedelta(days=30)

        mock_db.refresh = mock_refresh

        result = await service.create(data)

        assert result.name == "Test Search"
        assert result.source == "niche_discovery"
        assert result.product_count == 1
        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_sets_product_count(self, service, mock_db):
        """Test that product_count is set from products array length."""
        products = [
            {"asin": "B1", "title": "P1"},
            {"asin": "B2", "title": "P2"},
            {"asin": "B3", "title": "P3"}
        ]
        data = SearchResultCreate(
            name="Multi Product",
            source=SearchSourceEnum.MANUAL_ANALYSIS,
            products=products
        )

        async def mock_refresh(obj):
            pass
        mock_db.refresh = mock_refresh

        result = await service.create(data)
        assert result.product_count == 3

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, service, mock_db):
        """Test getting existing search result."""
        mock_result = SearchResult(
            name="Found",
            source="autosourcing",
            products=[],
            product_count=0
        )
        # Create a proper mock for the execute result
        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = mock_result
        mock_db.execute.return_value = execute_result

        result = await service.get_by_id("existing-id")

        assert result is not None
        assert result.name == "Found"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, service, mock_db):
        """Test getting non-existent search result."""
        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = execute_result

        result = await service.get_by_id("non-existent")

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_existing(self, service, mock_db):
        """Test deleting existing search result."""
        mock_result = SearchResult(name="ToDelete", source="niche_discovery", products=[])

        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = mock_result
        mock_db.execute.return_value = execute_result

        result = await service.delete("to-delete-id")

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_not_found(self, service, mock_db):
        """Test deleting non-existent search result."""
        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = execute_result

        result = await service.delete("non-existent")

        assert result is False

    @pytest.mark.asyncio
    async def test_update_name_and_notes(self, service, mock_db):
        """Test updating name and notes."""
        mock_result = SearchResult(name="Old Name", source="autosourcing", products=[])

        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = mock_result
        mock_db.execute.return_value = execute_result

        update_data = SearchResultUpdate(name="New Name", notes="Updated notes")

        async def mock_refresh(obj):
            pass
        mock_db.refresh = mock_refresh

        result = await service.update("some-id", update_data)

        assert result.name == "New Name"
        assert result.notes == "Updated notes"

    @pytest.mark.asyncio
    async def test_cleanup_expired(self, service, mock_db):
        """Test cleanup of expired results."""
        execute_result = MagicMock()
        execute_result.rowcount = 5
        mock_db.execute.return_value = execute_result

        deleted = await service.cleanup_expired()

        assert deleted == 5


class TestSearchResultValidation:
    """Tests for schema validation."""

    def test_create_schema_valid(self):
        """Test valid create schema."""
        data = SearchResultCreate(
            name="Valid Search",
            source=SearchSourceEnum.NICHE_DISCOVERY,
            products=[{"asin": "B123"}]
        )
        assert data.name == "Valid Search"
        assert data.source == SearchSourceEnum.NICHE_DISCOVERY

    def test_create_schema_strips_whitespace(self):
        """Test that name whitespace is stripped."""
        data = SearchResultCreate(
            name="  Padded Name  ",
            source=SearchSourceEnum.AUTOSOURCING,
            products=[]
        )
        assert data.name == "Padded Name"

    def test_create_schema_empty_name_fails(self):
        """Test that empty name fails validation."""
        with pytest.raises(ValueError):
            SearchResultCreate(
                name="   ",
                source=SearchSourceEnum.MANUAL_ANALYSIS,
                products=[]
            )

    def test_update_schema_optional_fields(self):
        """Test update schema with optional fields."""
        data = SearchResultUpdate(name="Only Name")
        assert data.name == "Only Name"
        assert data.notes is None
