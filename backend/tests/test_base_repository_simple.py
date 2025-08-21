"""Simple focused tests for BaseRepository validation."""

import pytest
from decimal import Decimal

from app.repositories.base_repository import BaseRepository, SortOrder, FilterOperator
from app.core.exceptions import InvalidFilterFieldError
from app.models.user import User
from app.models.analysis import Analysis


class SimpleUserRepository(BaseRepository[User]):
    """Simple test repository for User model."""
    SORTABLE_FIELDS = ["id", "email", "created_at", "first_name"]
    FILTERABLE_FIELDS = ["id", "email", "role"]


class SimpleAnalysisRepository(BaseRepository[Analysis]):
    """Simple test repository for Analysis model."""
    SORTABLE_FIELDS = ["id", "roi_percent", "velocity_score", "profit"]
    FILTERABLE_FIELDS = ["id", "batch_id", "roi_percent", "velocity_score"]


class TestBaseRepositoryCore:
    """Core BaseRepository functionality tests."""

    @pytest.fixture(autouse=True)
    async def setup_simple_repos(self, async_db_session, sample_users, sample_analyses):
        """Setup simple repositories."""
        self.user_repo = SimpleUserRepository(async_db_session, User)
        self.analysis_repo = SimpleAnalysisRepository(async_db_session, Analysis)
        self.users = sample_users
        self.analyses = sample_analyses

    async def test_basic_list_functionality(self):
        """Test basic list functionality without complex filters."""
        page = await self.user_repo.list(offset=0, limit=10)
        
        assert len(page.items) == 3  # From fixture
        assert page.total == 3
        assert page.offset == 0
        assert page.limit == 10
        assert page.has_next is False
        assert page.has_prev is False

    async def test_pagination_with_offset(self):
        """Test pagination with offset."""
        # First page
        page1 = await self.user_repo.list(offset=0, limit=2)
        assert len(page1.items) == 2
        assert page1.has_next is True
        assert page1.has_prev is False
        
        # Second page
        page2 = await self.user_repo.list(offset=2, limit=2)
        assert len(page2.items) == 1  # Only 1 remaining
        assert page2.has_next is False
        assert page2.has_prev is True

    async def test_simple_sorting(self):
        """Test simple single-column sorting."""
        page_asc = await self.user_repo.list(
            sort_by=["email"],
            sort_order=[SortOrder.ASC]
        )
        
        emails_asc = [user.email for user in page_asc.items]
        assert emails_asc == sorted(emails_asc)
        
        page_desc = await self.user_repo.list(
            sort_by=["email"], 
            sort_order=[SortOrder.DESC]
        )
        
        emails_desc = [user.email for user in page_desc.items]
        assert emails_desc == sorted(emails_asc, reverse=True)

    async def test_simple_equality_filter(self):
        """Test simple equality filtering."""
        user = self.users[0]
        
        page = await self.user_repo.list(
            filters={"email": user.email}
        )
        
        assert len(page.items) == 1
        assert page.items[0].email == user.email

    async def test_range_filter_on_analysis(self):
        """Test range filtering on analysis ROI."""
        # Filter for ROI >= 50%
        page = await self.analysis_repo.list(
            filters={
                "roi_percent": {"operator": "gte", "value": 50.0}
            }
        )
        
        for analysis in page.items:
            assert analysis.roi_percent >= 50.0

    async def test_invalid_sort_field_error(self):
        """Test that invalid sort field raises error."""
        with pytest.raises(InvalidFilterFieldError) as exc_info:
            await self.user_repo.list(sort_by=["invalid_field"])
        
        assert "invalid_field" in str(exc_info.value)

    async def test_invalid_filter_field_error(self):
        """Test that invalid filter field raises error."""
        with pytest.raises(InvalidFilterFieldError) as exc_info:
            await self.user_repo.list(filters={"invalid_field": "value"})
        
        assert "invalid_field" in str(exc_info.value)

    async def test_count_functionality(self):
        """Test count method."""
        # Count all users
        total_count = await self.user_repo.count()
        assert total_count == 3
        
        # Count with filter
        admin_count = await self.user_repo.count(filters={"role": "admin"})
        sourcer_count = await self.user_repo.count(filters={"role": "sourcer"})
        
        assert admin_count + sourcer_count == total_count

    async def test_get_by_id(self):
        """Test get by ID functionality."""
        user = self.users[0]
        
        found_user = await self.user_repo.get_by_id(user.id)
        assert found_user is not None
        assert found_user.id == user.id
        assert found_user.email == user.email

    async def test_exists_functionality(self):
        """Test exists method."""
        user = self.users[0]
        
        # Should exist
        exists = await self.user_repo.exists(user.id)
        assert exists is True
        
        # Should not exist
        fake_id = "00000000-0000-0000-0000-000000000000"
        not_exists = await self.user_repo.exists(fake_id)
        assert not_exists is False