"""
RED-GREEN Tests: Async Job Persistence (I4)
============================================
TDD tests for database persistence of async batch processing jobs.

These tests verify:
1. Job records are created in DB when async processing starts
2. Job status updates properly (PENDING -> RUNNING -> SUCCESS/ERROR)
3. Results are stored with job reference
4. Error handling persists error details

Run: pytest tests/api/test_async_job_persistence.py -v
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.models.autosourcing import AutoSourcingJob, JobStatus


class TestAsyncJobCreation:
    """RED tests - Job creation in database."""

    @pytest.mark.asyncio
    async def test_create_async_job_returns_job_with_id(self, async_db_session):
        """Creating an async job should return a job object with valid UUID."""
        from app.services.async_job_service import create_async_job

        job = await create_async_job(
            db=async_db_session,
            profile_name="test_profile",
            identifiers=["B001TEST", "B002TEST"],
            discovery_config={"test": True},
            scoring_config={"roi_min": 30}
        )

        assert job is not None
        assert job.id is not None
        assert isinstance(job.id, type(uuid4()))

    @pytest.mark.asyncio
    async def test_create_async_job_has_pending_status(self, async_db_session):
        """New async job should have PENDING status."""
        from app.services.async_job_service import create_async_job

        job = await create_async_job(
            db=async_db_session,
            profile_name="test_profile",
            identifiers=["B001TEST"],
            discovery_config={},
            scoring_config={}
        )

        assert job.status == JobStatus.PENDING

    @pytest.mark.asyncio
    async def test_create_async_job_stores_profile_name(self, async_db_session):
        """Job should store the profile name correctly."""
        from app.services.async_job_service import create_async_job

        job = await create_async_job(
            db=async_db_session,
            profile_name="My Custom Profile",
            identifiers=["B001TEST"],
            discovery_config={},
            scoring_config={}
        )

        assert job.profile_name == "My Custom Profile"

    @pytest.mark.asyncio
    async def test_create_async_job_stores_config(self, async_db_session):
        """Job should store discovery and scoring configs."""
        from app.services.async_job_service import create_async_job

        discovery = {"categories": ["Books"], "bsr_range": [1000, 50000]}
        scoring = {"roi_min": 30, "velocity_min": 70}

        job = await create_async_job(
            db=async_db_session,
            profile_name="test",
            identifiers=["B001TEST"],
            discovery_config=discovery,
            scoring_config=scoring
        )

        assert job.discovery_config == discovery
        assert job.scoring_config == scoring

    @pytest.mark.asyncio
    async def test_create_async_job_persisted_in_db(self, async_db_session):
        """Job should be retrievable from database after creation."""
        from app.services.async_job_service import create_async_job
        from sqlalchemy import select

        job = await create_async_job(
            db=async_db_session,
            profile_name="persistent_test",
            identifiers=["B001TEST"],
            discovery_config={},
            scoring_config={}
        )

        # Flush and query
        await async_db_session.flush()
        result = await async_db_session.execute(
            select(AutoSourcingJob).where(AutoSourcingJob.id == job.id)
        )
        retrieved_job = result.scalar_one_or_none()

        assert retrieved_job is not None
        assert retrieved_job.profile_name == "persistent_test"


class TestAsyncJobStatusUpdates:
    """RED tests - Job status transitions."""

    @pytest.mark.asyncio
    async def test_update_job_status_to_running(self, async_db_session):
        """Job status should update from PENDING to RUNNING."""
        from app.services.async_job_service import create_async_job, update_job_status

        job = await create_async_job(
            db=async_db_session,
            profile_name="status_test",
            identifiers=["B001TEST"],
            discovery_config={},
            scoring_config={}
        )

        await update_job_status(async_db_session, job.id, JobStatus.RUNNING)
        await async_db_session.refresh(job)

        assert job.status == JobStatus.RUNNING

    @pytest.mark.asyncio
    async def test_update_job_status_to_success(self, async_db_session):
        """Job status should update to SUCCESS on completion."""
        from app.services.async_job_service import create_async_job, update_job_status

        job = await create_async_job(
            db=async_db_session,
            profile_name="success_test",
            identifiers=["B001TEST"],
            discovery_config={},
            scoring_config={}
        )

        await update_job_status(async_db_session, job.id, JobStatus.SUCCESS)
        await async_db_session.refresh(job)

        assert job.status == JobStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_update_job_status_to_error_with_message(self, async_db_session):
        """Job should store error message when status is ERROR."""
        from app.services.async_job_service import (
            create_async_job,
            update_job_status,
            set_job_error
        )

        job = await create_async_job(
            db=async_db_session,
            profile_name="error_test",
            identifiers=["B001TEST"],
            discovery_config={},
            scoring_config={}
        )

        await set_job_error(async_db_session, job.id, "API rate limit exceeded")
        await async_db_session.refresh(job)

        assert job.status == JobStatus.ERROR
        assert job.error_message == "API rate limit exceeded"
        assert job.error_count >= 1

    @pytest.mark.asyncio
    async def test_update_job_sets_completed_at(self, async_db_session):
        """Completing a job should set completed_at timestamp."""
        from app.services.async_job_service import create_async_job, complete_job

        job = await create_async_job(
            db=async_db_session,
            profile_name="completion_test",
            identifiers=["B001TEST"],
            discovery_config={},
            scoring_config={}
        )

        await complete_job(async_db_session, job.id, total_tested=5, total_selected=2)
        await async_db_session.refresh(job)

        assert job.completed_at is not None
        assert job.total_tested == 5
        assert job.total_selected == 2


class TestAsyncJobResultStorage:
    """RED tests - Storing processing results."""

    @pytest.mark.asyncio
    async def test_job_tracks_total_tested(self, async_db_session):
        """Job should track total number of identifiers tested."""
        from app.services.async_job_service import create_async_job, complete_job

        job = await create_async_job(
            db=async_db_session,
            profile_name="tracking_test",
            identifiers=["B001", "B002", "B003"],
            discovery_config={},
            scoring_config={}
        )

        await complete_job(async_db_session, job.id, total_tested=3, total_selected=1)
        await async_db_session.refresh(job)

        assert job.total_tested == 3

    @pytest.mark.asyncio
    async def test_job_tracks_total_selected(self, async_db_session):
        """Job should track number of products selected."""
        from app.services.async_job_service import create_async_job, complete_job

        job = await create_async_job(
            db=async_db_session,
            profile_name="selection_test",
            identifiers=["B001", "B002", "B003"],
            discovery_config={},
            scoring_config={}
        )

        await complete_job(async_db_session, job.id, total_tested=3, total_selected=2)
        await async_db_session.refresh(job)

        assert job.total_selected == 2

    @pytest.mark.asyncio
    async def test_job_calculates_duration(self, async_db_session):
        """Job should calculate duration in milliseconds."""
        from app.services.async_job_service import create_async_job, complete_job
        import asyncio

        job = await create_async_job(
            db=async_db_session,
            profile_name="duration_test",
            identifiers=["B001TEST"],
            discovery_config={},
            scoring_config={}
        )

        # Small delay to ensure measurable duration
        await asyncio.sleep(0.05)

        await complete_job(async_db_session, job.id, total_tested=1, total_selected=0)
        await async_db_session.refresh(job)

        assert job.duration_ms is not None
        assert job.duration_ms >= 50  # At least 50ms


class TestAsyncJobEdgeCases:
    """RED tests - Edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_create_job_with_empty_identifiers(self, async_db_session):
        """Creating job with empty identifiers should work (validation elsewhere)."""
        from app.services.async_job_service import create_async_job

        job = await create_async_job(
            db=async_db_session,
            profile_name="empty_test",
            identifiers=[],
            discovery_config={},
            scoring_config={}
        )

        assert job is not None
        assert job.total_tested == 0

    @pytest.mark.asyncio
    async def test_update_nonexistent_job_raises_error(self, async_db_session):
        """Updating a non-existent job should raise an error."""
        from app.services.async_job_service import update_job_status

        fake_id = uuid4()

        with pytest.raises(ValueError, match="Job not found"):
            await update_job_status(async_db_session, fake_id, JobStatus.RUNNING)

    @pytest.mark.asyncio
    async def test_job_error_increments_error_count(self, async_db_session):
        """Multiple errors should increment error_count."""
        from app.services.async_job_service import create_async_job, set_job_error

        job = await create_async_job(
            db=async_db_session,
            profile_name="multi_error_test",
            identifiers=["B001TEST"],
            discovery_config={},
            scoring_config={}
        )

        await set_job_error(async_db_session, job.id, "Error 1")
        await set_job_error(async_db_session, job.id, "Error 2")
        await async_db_session.refresh(job)

        assert job.error_count == 2
        assert job.error_message == "Error 2"  # Last error


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
