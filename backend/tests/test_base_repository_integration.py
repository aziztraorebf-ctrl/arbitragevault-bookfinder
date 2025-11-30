"""Integration tests for BaseRepository with real database operations."""

import pytest
from decimal import Decimal
from typing import List

from app.repositories.base_repository import BaseRepository, SortOrder, FilterOperator
from app.core.exceptions import InvalidFilterFieldError
from app.models.user import User
from app.models.batch import Batch
from app.models.analysis import Analysis


class UserRepositoryForTest(BaseRepository[User]):
    """Test repository for User model."""
    SORTABLE_FIELDS = ["id", "email", "created_at", "first_name", "last_name"]
    FILTERABLE_FIELDS = ["id", "email", "role", "first_name", "last_name"]


class BatchRepositoryForTest(BaseRepository[Batch]):
    """Test repository for Batch model."""
    SORTABLE_FIELDS = ["id", "name", "status", "created_at", "items_total", "items_processed"]
    FILTERABLE_FIELDS = ["id", "user_id", "name", "status"]


class AnalysisRepositoryForTest(BaseRepository[Analysis]):
    """Test repository for Analysis model."""
    SORTABLE_FIELDS = ["id", "roi_percent", "velocity_score", "profit", "created_at"]
    FILTERABLE_FIELDS = ["id", "batch_id", "roi_percent", "velocity_score", "profit"]


class TestBaseRepositoryIntegration:
    """Integration tests for BaseRepository with real database."""

    @pytest.fixture(autouse=True)
    async def setup_repositories(self, async_db_session, sample_users, sample_batches, sample_analyses):
        """Setup test repositories and sample data."""
        self.user_repo = UserRepositoryForTest(async_db_session, User)
        self.batch_repo = BatchRepositoryForTest(async_db_session, Batch)
        self.analysis_repo = AnalysisRepositoryForTest(async_db_session, Analysis)
        
        # Store sample data for reference
        self.users = sample_users
        self.batches = sample_batches
        self.analyses = sample_analyses

    async def test_basic_list_pagination(self):
        """Test basic pagination functionality."""
        # Test first page
        page1 = await self.user_repo.list(offset=0, limit=2)
        
        assert len(page1.items) == 2
        assert page1.total == 3  # From fixture: 3 users
        assert page1.offset == 0
        assert page1.limit == 2
        assert page1.has_next is True
        assert page1.has_prev is False
        
        # Test second page
        page2 = await self.user_repo.list(offset=2, limit=2)
        
        assert len(page2.items) == 1  # Only 1 remaining
        assert page2.total == 3
        assert page2.offset == 2
        assert page2.limit == 2
        assert page2.has_next is False
        assert page2.has_prev is True

    async def test_empty_result_pagination(self):
        """Test pagination with no results."""
        page = await self.user_repo.list(
            offset=0, 
            limit=10, 
            filters={"email": "nonexistent@example.com"}
        )
        
        assert len(page.items) == 0
        assert page.total == 0
        assert page.has_next is False
        assert page.has_prev is False

    async def test_single_column_sorting(self):
        """Test sorting by single column."""
        # Sort users by email ascending
        page = await self.user_repo.list(
            offset=0,
            limit=10,
            sort_by=["email"],
            sort_order=[SortOrder.ASC]
        )
        
        emails = [user.email for user in page.items]
        assert emails == sorted(emails)
        
        # Sort by email descending
        page_desc = await self.user_repo.list(
            offset=0,
            limit=10,
            sort_by=["email"],
            sort_order=[SortOrder.DESC]
        )
        
        emails_desc = [user.email for user in page_desc.items]
        assert emails_desc == sorted(emails, reverse=True)

    async def test_multi_column_sorting(self):
        """Test sorting by multiple columns."""
        # Sort batches by status ASC, then created_at DESC
        page = await self.batch_repo.list(
            offset=0,
            limit=10,
            sort_by=["status", "created_at"],
            sort_order=[SortOrder.ASC, SortOrder.DESC]
        )
        
        # Verify sort order - should be grouped by status, then by created_at desc within each status
        previous_status = None
        previous_created_at = None
        
        for batch in page.items:
            if previous_status is None:
                previous_status = batch.status
                previous_created_at = batch.created_at
            elif batch.status == previous_status:
                # Same status - created_at should be descending
                assert batch.created_at <= previous_created_at
                previous_created_at = batch.created_at
            else:
                # Different status - should be ascending (by enum value string)
                assert batch.status.value >= previous_status.value
                previous_status = batch.status
                previous_created_at = batch.created_at

    async def test_stable_sorting_tiebreak(self):
        """Test that sorting is stable with ID tiebreak."""
        # Create analyses with same ROI to test tiebreak
        batch = self.batches[0]
        
        # Get analyses for this batch, sorted by ROI
        page1 = await self.analysis_repo.list(
            filters={"batch_id": batch.id},
            sort_by=["roi_percent"],
            sort_order=[SortOrder.ASC]
        )
        
        page2 = await self.analysis_repo.list(
            filters={"batch_id": batch.id},
            sort_by=["roi_percent"],
            sort_order=[SortOrder.ASC]
        )
        
        # Results should be identical (stable sort)
        ids1 = [analysis.id for analysis in page1.items]
        ids2 = [analysis.id for analysis in page2.items]
        assert ids1 == ids2

    async def test_equality_filter(self):
        """Test simple equality filtering."""
        user = self.users[0]
        
        page = await self.user_repo.list(
            filters={"email": user.email}
        )
        
        assert len(page.items) == 1
        assert page.items[0].email == user.email
        assert page.total == 1

    async def test_range_filters(self):
        """Test range filtering with GTE/LTE operators."""
        # Filter analyses by ROI >= 50%
        page_gte = await self.analysis_repo.list(
            filters={
                "roi_percent": {"operator": "gte", "value": 50.0}
            }
        )
        
        for analysis in page_gte.items:
            assert analysis.roi_percent >= 50.0
        
        # Filter analyses by ROI <= 100%
        page_lte = await self.analysis_repo.list(
            filters={
                "roi_percent": {"operator": "lte", "value": 100.0}
            }
        )
        
        for analysis in page_lte.items:
            assert analysis.roi_percent <= 100.0
        
        # Range filter: 50% <= ROI <= 100%
        page_range = await self.analysis_repo.list(
            filters={
                "roi_percent": {"operator": "gte", "value": 50.0}
            }
        )
        
        # Apply second filter manually for this test
        # In production, you'd use multiple filters or a between operator
        range_items = [a for a in page_range.items if a.roi_percent <= 100.0]
        
        for analysis in range_items:
            assert 50.0 <= analysis.roi_percent <= 100.0

    async def test_in_filter(self):
        """Test IN filter for multiple values."""
        statuses = ["PENDING", "PROCESSING"]

        page = await self.batch_repo.list(
            filters={
                "status": {"operator": "in", "value": statuses}
            }
        )

        for batch in page.items:
            assert batch.status.value in statuses

    async def test_combined_filters_and_sorting(self):
        """Test combining filters with sorting."""
        batch = self.batches[0]
        
        page = await self.analysis_repo.list(
            filters={"batch_id": batch.id},
            sort_by=["roi_percent"],
            sort_order=[SortOrder.DESC],
            offset=0,
            limit=5
        )
        
        # All items should belong to the specified batch
        for analysis in page.items:
            assert analysis.batch_id == batch.id
        
        # Items should be sorted by ROI descending
        if len(page.items) > 1:
            for i in range(len(page.items) - 1):
                assert page.items[i].roi_percent >= page.items[i + 1].roi_percent

    async def test_invalid_sort_field_raises_error(self):
        """Test that invalid sort fields raise appropriate error."""
        with pytest.raises(InvalidFilterFieldError) as exc_info:
            await self.user_repo.list(sort_by=["invalid_field"])
        
        assert "invalid_field" in str(exc_info.value)
        assert "not allowed for filtering/sorting" in str(exc_info.value)

    async def test_invalid_filter_field_raises_error(self):
        """Test that invalid filter fields raise appropriate error."""
        with pytest.raises(InvalidFilterFieldError) as exc_info:
            await self.user_repo.list(filters={"invalid_field": "value"})
        
        assert "invalid_field" in str(exc_info.value)
        assert "not allowed for filtering/sorting" in str(exc_info.value)

    async def test_count_with_filters(self):
        """Test count method with filters."""
        # Count all users
        total_count = await self.user_repo.count()
        assert total_count == 3
        
        # Count users with specific role
        admin_count = await self.user_repo.count(filters={"role": "admin"})
        sourcer_count = await self.user_repo.count(filters={"role": "sourcer"})
        
        assert admin_count + sourcer_count == total_count

    async def test_large_offset_performance(self):
        """Test performance with large offset (simulates deep pagination)."""
        # This test would be more meaningful with 10k+ records
        # For now, just verify it doesn't crash
        page = await self.analysis_repo.list(
            offset=0,  # Would be large in real scenario
            limit=10,
            sort_by=["roi_percent"],
            sort_order=[SortOrder.DESC]
        )
        
        assert isinstance(page.total, int)
        assert len(page.items) <= 10

    async def test_create_and_list_consistency(self):
        """Test that created records appear in list results."""
        # Create new user
        new_user = await self.user_repo.create(
            email="integration_test@example.com",
            password_hash="hashed_password",
            first_name="Integration",
            last_name="Test",
            role="sourcer"
        )
        
        # Verify it appears in list
        page = await self.user_repo.list(
            filters={"email": "integration_test@example.com"}
        )
        
        assert len(page.items) == 1
        assert page.items[0].id == new_user.id
        assert page.items[0].email == new_user.email

    async def test_update_and_list_consistency(self):
        """Test that updated records reflect changes in list results."""
        user = self.users[0]
        
        # Update user
        updated_user = await self.user_repo.update(
            user.id,
            first_name="UpdatedName"
        )
        
        # Verify change appears in list
        page = await self.user_repo.list(
            filters={"id": user.id}
        )
        
        assert len(page.items) == 1
        assert page.items[0].first_name == "UpdatedName"

    async def test_delete_and_list_consistency(self):
        """Test that deleted records don't appear in list results."""
        # Create temporary user for deletion
        temp_user = await self.user_repo.create(
            email="temp_delete@example.com",
            password_hash="hashed_password",
            first_name="Temp",
            last_name="Delete",
            role="sourcer"
        )
        
        # Verify it exists
        page_before = await self.user_repo.list(
            filters={"email": "temp_delete@example.com"}
        )
        assert len(page_before.items) == 1
        
        # Delete it
        deleted = await self.user_repo.delete(temp_user.id)
        assert deleted is True
        
        # Verify it's gone
        page_after = await self.user_repo.list(
            filters={"email": "temp_delete@example.com"}
        )
        assert len(page_after.items) == 0

    async def test_exists_method(self):
        """Test exists method."""
        user = self.users[0]
        
        # Should exist
        exists = await self.user_repo.exists(user.id)
        assert exists is True
        
        # Should not exist
        fake_id = "00000000-0000-0000-0000-000000000000"
        not_exists = await self.user_repo.exists(fake_id)
        assert not_exists is False