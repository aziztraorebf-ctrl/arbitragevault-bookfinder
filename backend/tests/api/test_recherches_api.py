"""
API Integration Tests for Recherches Endpoints
===============================================
Tests for /api/v1/recherches endpoints validation and schemas.

Phase 11 - Mes Recherches feature.

Run: pytest tests/api/test_recherches_api.py -v
"""

import pytest
from app.schemas.search_result import (
    SearchResultCreate,
    SearchResultUpdate,
    SearchResultRead,
    SearchResultDetail,
    SearchResultListResponse,
    SearchSourceEnum
)


class TestRecherchesSchemas:
    """Tests for recherches Pydantic schemas."""

    def test_create_schema_valid_niche_discovery(self):
        """Test valid SearchResultCreate with niche_discovery source."""
        data = SearchResultCreate(
            name="Test Niche Discovery",
            source=SearchSourceEnum.NICHE_DISCOVERY,
            products=[{"asin": "B123", "title": "Test Product"}],
            search_params={"strategy": "textbook"},
            notes="Test notes"
        )
        assert data.name == "Test Niche Discovery"
        assert data.source == SearchSourceEnum.NICHE_DISCOVERY
        assert len(data.products) == 1
        assert data.notes == "Test notes"

    def test_create_schema_valid_autosourcing(self):
        """Test valid SearchResultCreate with autosourcing source."""
        data = SearchResultCreate(
            name="Test AutoSourcing",
            source=SearchSourceEnum.AUTOSOURCING,
            products=[{"asin": "B789", "title": "AutoSource Product"}]
        )
        assert data.source == SearchSourceEnum.AUTOSOURCING
        assert len(data.products) == 1
        assert data.notes is None

    def test_create_schema_valid_manual_analysis(self):
        """Test valid SearchResultCreate with manual_analysis source."""
        data = SearchResultCreate(
            name="Test Manual",
            source=SearchSourceEnum.MANUAL_ANALYSIS,
            products=[{"asin": "B456"}]
        )
        assert data.source == SearchSourceEnum.MANUAL_ANALYSIS

    def test_create_schema_strips_name_whitespace(self):
        """Test that name whitespace is stripped."""
        data = SearchResultCreate(
            name="  Padded Name  ",
            source=SearchSourceEnum.NICHE_DISCOVERY,
            products=[{"asin": "B123"}]
        )
        assert data.name == "Padded Name"

    def test_create_schema_empty_name_fails(self):
        """Test that whitespace-only name fails validation."""
        with pytest.raises(ValueError):
            SearchResultCreate(
                name="   ",
                source=SearchSourceEnum.NICHE_DISCOVERY,
                products=[{"asin": "B123"}]
            )

    def test_create_schema_missing_name_fails(self):
        """Test that missing name fails validation."""
        with pytest.raises(ValueError):
            SearchResultCreate(
                source=SearchSourceEnum.NICHE_DISCOVERY,
                products=[{"asin": "B123"}]
            )

    def test_create_schema_invalid_source_fails(self):
        """Test that invalid source fails validation."""
        with pytest.raises(ValueError):
            SearchResultCreate(
                name="Test",
                source="invalid_source",
                products=[{"asin": "B123"}]
            )

    def test_create_schema_empty_products_fails(self):
        """Test that empty products array fails validation."""
        with pytest.raises(ValueError, match="cannot be empty"):
            SearchResultCreate(
                name="No Products",
                source=SearchSourceEnum.NICHE_DISCOVERY,
                products=[]
            )

    def test_create_schema_product_without_asin_fails(self):
        """Test that product without ASIN field fails validation."""
        with pytest.raises(ValueError, match="must have an ASIN"):
            SearchResultCreate(
                name="Bad Product",
                source=SearchSourceEnum.NICHE_DISCOVERY,
                products=[{"title": "No ASIN here"}]
            )

    def test_create_schema_max_products_limit(self):
        """Test products array max limit (500)."""
        # 500 products should be OK
        products_500 = [{"asin": f"B{i:05d}"} for i in range(500)]
        data = SearchResultCreate(
            name="Max Products",
            source=SearchSourceEnum.NICHE_DISCOVERY,
            products=products_500
        )
        assert len(data.products) == 500

        # 501 products should fail (Pydantic checks max_length first)
        products_501 = [{"asin": f"B{i:05d}"} for i in range(501)]
        with pytest.raises(Exception):  # ValidationError from Pydantic
            SearchResultCreate(
                name="Too Many Products",
                source=SearchSourceEnum.NICHE_DISCOVERY,
                products=products_501
            )

    def test_update_schema_partial(self):
        """Test partial update schema."""
        data = SearchResultUpdate(name="New Name")
        assert data.name == "New Name"
        assert data.notes is None

        data2 = SearchResultUpdate(notes="New notes")
        assert data2.name is None
        assert data2.notes == "New notes"

    def test_update_schema_both_fields(self):
        """Test update schema with both fields."""
        data = SearchResultUpdate(name="Updated", notes="Updated notes")
        assert data.name == "Updated"
        assert data.notes == "Updated notes"

    def test_update_schema_empty_name_fails(self):
        """Test that empty name in update fails."""
        with pytest.raises(ValueError):
            SearchResultUpdate(name="   ")


class TestRecherchesSourceEnum:
    """Tests for SearchSourceEnum values."""

    def test_all_sources_exist(self):
        """Test all expected sources are defined."""
        assert SearchSourceEnum.NICHE_DISCOVERY.value == "niche_discovery"
        assert SearchSourceEnum.AUTOSOURCING.value == "autosourcing"
        assert SearchSourceEnum.MANUAL_ANALYSIS.value == "manual_analysis"

    def test_source_count(self):
        """Test there are exactly 3 sources."""
        assert len(SearchSourceEnum) == 3


class TestRecherchesListResponse:
    """Tests for list response schema."""

    def test_list_response_empty(self):
        """Test empty list response."""
        data = SearchResultListResponse(results=[], total_count=0)
        assert data.results == []
        assert data.total_count == 0

    def test_list_response_with_items(self):
        """Test list response with items."""
        # Create mock SearchResultRead objects (as dicts for simplicity)
        from datetime import datetime

        mock_result = {
            "id": "test-id",
            "name": "Test Search",
            "source": "niche_discovery",
            "product_count": 5,
            "search_params": {},
            "notes": None,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow()
        }

        data = SearchResultListResponse(
            results=[SearchResultRead(**mock_result)],
            total_count=1
        )
        assert len(data.results) == 1
        assert data.total_count == 1
