"""
Unit tests for BookmarkService.
"""
import pytest
from unittest.mock import MagicMock, Mock
from fastapi import HTTPException

from app.services.bookmark_service import BookmarkService
from app.models.bookmark import SavedNiche
from app.schemas.bookmark import NicheCreateSchema, NicheUpdateSchema


@pytest.fixture
def mock_db():
    """Mock database session."""
    return MagicMock()


@pytest.fixture
def service(mock_db):
    """Fixture for BookmarkService instance."""
    return BookmarkService(db=mock_db)


@pytest.fixture
def sample_niche_data():
    """Sample niche data for testing."""
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
def sample_saved_niche():
    """Sample SavedNiche model instance."""
    niche = SavedNiche(
        niche_name="Engineering Textbooks",
        user_id="user123",
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
    niche.id = "niche123"
    return niche


def test_create_niche_success(service, mock_db, sample_niche_data):
    """Test successful creation of a new niche."""
    mock_query = mock_db.query.return_value
    mock_query.filter.return_value.first.return_value = None

    created_niche = Mock(spec=SavedNiche)
    created_niche.id = "new_niche_id"
    created_niche.niche_name = sample_niche_data.niche_name

    result = service.create_niche(
        user_id="user123",
        niche_data=sample_niche_data
    )

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()
    assert result is not None


def test_create_niche_duplicate_name_raises_409(service, mock_db, sample_niche_data, sample_saved_niche):
    """Test creation fails with 409 when niche name already exists for user."""
    mock_query = mock_db.query.return_value
    mock_query.filter.return_value.first.return_value = sample_saved_niche

    with pytest.raises(HTTPException) as exc_info:
        service.create_niche(
            user_id="user123",
            niche_data=sample_niche_data
        )

    assert exc_info.value.status_code == 409
    assert "already exists" in str(exc_info.value.detail).lower()
    mock_db.rollback.assert_called_once()
    mock_db.add.assert_not_called()


def test_get_niche_by_id_found(service, mock_db, sample_saved_niche):
    """Test retrieving an existing niche by ID."""
    mock_query = mock_db.query.return_value
    mock_query.filter.return_value.first.return_value = sample_saved_niche

    result = service.get_niche_by_id(
        user_id="user123",
        niche_id="niche123"
    )

    assert result == sample_saved_niche
    mock_db.query.assert_called_once_with(SavedNiche)


def test_get_niche_by_id_not_found(service, mock_db):
    """Test retrieving a non-existent niche returns None."""
    mock_query = mock_db.query.return_value
    mock_query.filter.return_value.first.return_value = None

    result = service.get_niche_by_id(
        user_id="user123",
        niche_id="nonexistent"
    )

    assert result is None


def test_list_niches_returns_paginated(service, mock_db, sample_saved_niche):
    """Test listing niches returns paginated results with total count."""
    mock_query = mock_db.query.return_value
    mock_query.filter.return_value.count.return_value = 5

    mock_paginated = mock_query.filter.return_value.order_by.return_value
    mock_paginated.offset.return_value.limit.return_value.all.return_value = [
        sample_saved_niche
    ]

    niches, total_count = service.list_niches_by_user(
        user_id="user123",
        skip=0,
        limit=10
    )

    assert len(niches) == 1
    assert total_count == 5
    assert niches[0] == sample_saved_niche


def test_update_niche_success(service, mock_db, sample_saved_niche):
    """Test successful update of an existing niche."""
    mock_query = mock_db.query.return_value
    # First call: get_niche_by_id returns existing niche
    # Second call: check for name conflict returns None (no conflict)
    mock_query.filter.return_value.first.side_effect = [
        sample_saved_niche,  # get_niche_by_id
        None                 # No name conflict
    ]

    update_data = NicheUpdateSchema(
        niche_name="Updated Name",
        description="Updated description"
    )

    result = service.update_niche(
        user_id="user123",
        niche_id="niche123",
        niche_data=update_data
    )

    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()


def test_update_niche_not_found_raises_404(service, mock_db):
    """Test updating a non-existent niche raises 404."""
    mock_query = mock_db.query.return_value
    mock_query.filter.return_value.first.return_value = None

    update_data = NicheUpdateSchema(
        niche_name="Updated Name"
    )

    with pytest.raises(HTTPException) as exc_info:
        service.update_niche(
            user_id="user123",
            niche_id="nonexistent",
            niche_data=update_data
        )

    assert exc_info.value.status_code == 404
    assert "not found" in str(exc_info.value.detail).lower()
    mock_db.rollback.assert_called_once()


def test_update_niche_duplicate_name_raises_409(service, mock_db, sample_saved_niche):
    """Test updating niche name to existing name raises 409."""
    mock_query = mock_db.query.return_value

    # Setup existing duplicate niche
    existing_duplicate = Mock(spec=SavedNiche)
    existing_duplicate.id = "other_niche_id"
    existing_duplicate.niche_name = "Existing Name"

    # First call: get_niche_by_id returns the niche to update
    # Second call: check for duplicate returns another niche with same name
    mock_query.filter.return_value.first.side_effect = [
        sample_saved_niche,  # get_niche_by_id
        existing_duplicate    # name conflict detected
    ]

    update_data = NicheUpdateSchema(
        niche_name="Existing Name"
    )

    with pytest.raises(HTTPException) as exc_info:
        service.update_niche(
            user_id="user123",
            niche_id="niche123",
            niche_data=update_data
        )

    assert exc_info.value.status_code == 409
    assert "already exists" in str(exc_info.value.detail).lower()
    mock_db.rollback.assert_called_once()


def test_delete_niche_success(service, mock_db, sample_saved_niche):
    """Test successful deletion of an existing niche."""
    mock_query = mock_db.query.return_value
    mock_query.filter.return_value.first.return_value = sample_saved_niche

    result = service.delete_niche(
        user_id="user123",
        niche_id="niche123"
    )

    assert result is True
    mock_db.delete.assert_called_once_with(sample_saved_niche)
    mock_db.commit.assert_called_once()


def test_delete_niche_not_found_returns_false(service, mock_db):
    """Test deleting a non-existent niche returns False."""
    mock_query = mock_db.query.return_value
    mock_query.filter.return_value.first.return_value = None

    result = service.delete_niche(
        user_id="user123",
        niche_id="nonexistent"
    )

    assert result is False
    mock_db.delete.assert_not_called()


def test_get_filters_returns_dict(service, mock_db, sample_saved_niche):
    """Test get_niche_filters_for_analysis returns filters dict when niche exists."""
    mock_query = mock_db.query.return_value
    mock_query.filter.return_value.first.return_value = sample_saved_niche

    result = service.get_niche_filters_for_analysis(
        user_id="user123",
        niche_id="niche123"
    )

    assert result is not None
    assert isinstance(result, dict)
    assert "min_price" in result
    assert result["min_price"] == 20.0


def test_get_filters_returns_none_when_not_found(service, mock_db):
    """Test get_niche_filters_for_analysis returns None when niche not found."""
    mock_query = mock_db.query.return_value
    mock_query.filter.return_value.first.return_value = None

    result = service.get_niche_filters_for_analysis(
        user_id="user123",
        niche_id="nonexistent"
    )

    assert result is None
