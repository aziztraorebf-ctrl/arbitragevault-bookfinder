"""Tests for the BookmarkService functionality."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.services.bookmark_service import BookmarkService
from app.models.bookmark import SavedNiche
from app.schemas.bookmark import NicheCreateSchema, NicheUpdateSchema


class TestBookmarkService:
    """Test cases for BookmarkService."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def bookmark_service(self, mock_db):
        """BookmarkService instance with mock database."""
        return BookmarkService(mock_db)

    @pytest.fixture
    def sample_niche_data(self):
        """Sample niche creation data."""
        return NicheCreateSchema(
            niche_name="Engineering Textbooks",
            category_id=13,
            category_name="Engineering & Transportation",
            filters={
                "min_price": 20.0,
                "max_price": 200.0,
                "max_bsr": 500000,
                "min_roi": 30.0
            },
            last_score=7.4,
            description="High-margin engineering textbooks"
        )

    @pytest.fixture
    def sample_saved_niche(self):
        """Sample SavedNiche model instance."""
        niche = SavedNiche(
            id="test-niche-id",
            user_id="test-user-id",
            niche_name="Engineering Textbooks",
            category_id=13,
            category_name="Engineering & Transportation",
            filters={
                "min_price": 20.0,
                "max_price": 200.0,
                "max_bsr": 500000,
                "min_roi": 30.0
            },
            last_score=7.4,
            description="High-margin engineering textbooks"
        )
        niche.created_at = datetime.now()
        niche.updated_at = datetime.now()
        return niche

    def test_create_niche_success(self, bookmark_service, mock_db, sample_niche_data):
        """Test successful niche creation."""
        user_id = "test-user-id"
        
        # Mock: no existing niche with same name
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Mock: successful database operations
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        # Execute
        result = bookmark_service.create_niche(user_id, sample_niche_data)

        # Verify
        assert isinstance(result, SavedNiche)
        assert result.user_id == user_id
        assert result.niche_name == sample_niche_data.niche_name
        assert result.category_id == sample_niche_data.category_id
        assert result.filters == sample_niche_data.filters

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_niche_duplicate_name(self, bookmark_service, mock_db, sample_niche_data, sample_saved_niche):
        """Test creating niche with duplicate name raises conflict."""
        user_id = "test-user-id"
        
        # Mock: existing niche with same name
        mock_db.query.return_value.filter.return_value.first.return_value = sample_saved_niche

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            bookmark_service.create_niche(user_id, sample_niche_data)
        
        assert exc_info.value.status_code == 409
        assert "already exists" in str(exc_info.value.detail)

    def test_get_niche_by_id_success(self, bookmark_service, mock_db, sample_saved_niche):
        """Test successful niche retrieval by ID."""
        user_id = "test-user-id"
        niche_id = "test-niche-id"
        
        # Mock: niche found
        mock_db.query.return_value.filter.return_value.first.return_value = sample_saved_niche

        # Execute
        result = bookmark_service.get_niche_by_id(user_id, niche_id)

        # Verify
        assert result == sample_saved_niche

    def test_get_niche_by_id_not_found(self, bookmark_service, mock_db):
        """Test niche retrieval returns None when not found."""
        user_id = "test-user-id"
        niche_id = "nonexistent-id"
        
        # Mock: niche not found
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Execute
        result = bookmark_service.get_niche_by_id(user_id, niche_id)

        # Verify
        assert result is None

    def test_list_niches_by_user_success(self, bookmark_service, mock_db, sample_saved_niche):
        """Test successful listing of user niches."""
        user_id = "test-user-id"
        
        # Mock: count query returns 1
        mock_db.query.return_value.filter.return_value.count.return_value = 1
        
        # Mock: paginated query returns list with one niche
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [sample_saved_niche]

        # Execute
        niches, total_count = bookmark_service.list_niches_by_user(user_id, skip=0, limit=100)

        # Verify
        assert len(niches) == 1
        assert niches[0] == sample_saved_niche
        assert total_count == 1

    def test_update_niche_success(self, bookmark_service, mock_db, sample_saved_niche):
        """Test successful niche update."""
        user_id = "test-user-id"
        niche_id = "test-niche-id"
        
        update_data = NicheUpdateSchema(
            niche_name="Updated Engineering Textbooks",
            description="Updated description"
        )

        # Mock the two database queries separately
        # First query: get_niche_by_id - should return the niche
        # Second query: check for name conflicts - should return None
        def mock_query_side_effect(*args):
            mock_query = Mock()
            mock_filter = Mock()
            mock_query.filter.return_value = mock_filter
            
            # Use a counter to differentiate calls
            if not hasattr(mock_query_side_effect, 'call_count'):
                mock_query_side_effect.call_count = 0
            mock_query_side_effect.call_count += 1
            
            if mock_query_side_effect.call_count == 1:
                # First call: get_niche_by_id
                mock_filter.first.return_value = sample_saved_niche
            else:
                # Second call: check for name conflicts
                mock_filter.first.return_value = None
                
            return mock_query

        mock_db.query.side_effect = mock_query_side_effect
        
        # Mock: successful commit
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        # Execute
        result = bookmark_service.update_niche(user_id, niche_id, update_data)

        # Verify
        assert result == sample_saved_niche
        mock_db.commit.assert_called_once()

    def test_update_niche_not_found(self, bookmark_service, mock_db):
        """Test updating nonexistent niche raises 404."""
        user_id = "test-user-id"
        niche_id = "nonexistent-id"
        
        update_data = NicheUpdateSchema(niche_name="Updated Name")

        # Mock: niche not found
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            bookmark_service.update_niche(user_id, niche_id, update_data)
        
        assert exc_info.value.status_code == 404

    def test_delete_niche_success(self, bookmark_service, mock_db, sample_saved_niche):
        """Test successful niche deletion."""
        user_id = "test-user-id"
        niche_id = "test-niche-id"

        # Mock: niche found
        mock_db.query.return_value.filter.return_value.first.return_value = sample_saved_niche
        
        # Mock: successful deletion
        mock_db.delete.return_value = None
        mock_db.commit.return_value = None

        # Execute
        result = bookmark_service.delete_niche(user_id, niche_id)

        # Verify
        assert result is True
        mock_db.delete.assert_called_once_with(sample_saved_niche)
        mock_db.commit.assert_called_once()

    def test_delete_niche_not_found(self, bookmark_service, mock_db):
        """Test deleting nonexistent niche returns False."""
        user_id = "test-user-id"
        niche_id = "nonexistent-id"

        # Mock: niche not found
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Execute
        result = bookmark_service.delete_niche(user_id, niche_id)

        # Verify
        assert result is False

    def test_get_niche_filters_for_analysis_success(self, bookmark_service, mock_db, sample_saved_niche):
        """Test successful retrieval of niche filters."""
        user_id = "test-user-id"
        niche_id = "test-niche-id"

        # Mock: niche found
        mock_db.query.return_value.filter.return_value.first.return_value = sample_saved_niche

        # Execute
        result = bookmark_service.get_niche_filters_for_analysis(user_id, niche_id)

        # Verify
        assert result == sample_saved_niche.filters

    def test_get_niche_filters_for_analysis_not_found(self, bookmark_service, mock_db):
        """Test filters retrieval returns None when niche not found."""
        user_id = "test-user-id"
        niche_id = "nonexistent-id"

        # Mock: niche not found
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Execute
        result = bookmark_service.get_niche_filters_for_analysis(user_id, niche_id)

        # Verify
        assert result is None