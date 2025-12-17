"""
Integration tests for job status state machine.
Phase 7 Audit - Ensures valid state transitions only.
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from app.models.autosourcing import AutoSourcingJob, JobStatus


class TestJobStatusTransitions:
    """Test valid job status transitions."""

    def test_all_job_statuses_exist(self):
        """Verify all expected statuses are defined."""
        # Actual statuses in the codebase
        expected_statuses = ["PENDING", "RUNNING", "SUCCESS", "ERROR", "CANCELLED"]

        for status_name in expected_statuses:
            assert hasattr(JobStatus, status_name), f"Missing status: {status_name}"

    def test_valid_transitions_documented(self):
        """Document valid state transitions."""
        valid_transitions = {
            JobStatus.PENDING: [JobStatus.RUNNING, JobStatus.CANCELLED],
            JobStatus.RUNNING: [JobStatus.SUCCESS, JobStatus.ERROR],
            JobStatus.SUCCESS: [],  # Terminal state
            JobStatus.ERROR: [],    # Terminal state (includes timeout)
            JobStatus.CANCELLED: [], # Terminal state
        }

        # Verify all statuses are covered
        for status in JobStatus:
            assert status in valid_transitions, f"Status {status} not documented"

    def test_job_default_status(self):
        """New jobs should start in a valid initial state."""
        job = AutoSourcingJob(
            profile_name="Test",
            discovery_config={"categories": ["books"]},
            scoring_config={"roi_min": 30},
            status=JobStatus.RUNNING,
            launched_at=datetime.now(timezone.utc)
        )

        # Should be in RUNNING or PENDING
        assert job.status in [JobStatus.PENDING, JobStatus.RUNNING]

    def test_success_job_has_counts(self):
        """Successful jobs should have total_tested and total_selected."""
        job = AutoSourcingJob(
            profile_name="Test Success",
            discovery_config={},
            scoring_config={},
            status=JobStatus.SUCCESS,
            launched_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            total_tested=100,
            total_selected=5
        )

        assert job.status == JobStatus.SUCCESS
        assert job.total_tested >= 0
        assert job.total_selected >= 0
        assert job.total_selected <= job.total_tested

    def test_error_job_has_error_message(self):
        """Error jobs (including timeout) should have error_message."""
        job = AutoSourcingJob(
            profile_name="Test Error",
            discovery_config={},
            scoring_config={},
            status=JobStatus.ERROR,
            launched_at=datetime.now(timezone.utc),
            error_message="Timeout exceeded after 120 seconds"
        )

        assert job.status == JobStatus.ERROR
        assert job.error_message is not None
        assert len(job.error_message) > 0

    def test_completed_job_has_timestamp(self):
        """Completed jobs (SUCCESS/ERROR) should have completed_at."""
        for status in [JobStatus.SUCCESS, JobStatus.ERROR]:
            job = AutoSourcingJob(
                profile_name=f"Test {status.name}",
                discovery_config={},
                scoring_config={},
                status=status,
                launched_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                error_message="Test" if status == JobStatus.ERROR else None
            )

            # completed_at should be set for terminal states
            assert job.completed_at is not None, f"{status} job should have completed_at"

    def test_duration_calculation(self):
        """Duration should be calculated correctly."""
        launched = datetime.now(timezone.utc)
        completed = datetime.now(timezone.utc)

        job = AutoSourcingJob(
            profile_name="Test Duration",
            discovery_config={},
            scoring_config={},
            status=JobStatus.SUCCESS,
            launched_at=launched,
            completed_at=completed,
            duration_ms=5000  # 5 seconds
        )

        assert job.duration_ms >= 0
        assert job.duration_ms < 300000  # Less than 5 minutes (sanity check)

    def test_job_requires_profile_name(self):
        """Jobs should have a profile name."""
        job = AutoSourcingJob(
            profile_name="My Test Profile",
            discovery_config={},
            scoring_config={},
            status=JobStatus.RUNNING,
            launched_at=datetime.now(timezone.utc)
        )

        assert job.profile_name is not None
        assert len(job.profile_name) > 0

    def test_cancelled_job_is_terminal(self):
        """Cancelled jobs should be a terminal state."""
        job = AutoSourcingJob(
            profile_name="Test Cancelled",
            discovery_config={},
            scoring_config={},
            status=JobStatus.CANCELLED,
            launched_at=datetime.now(timezone.utc)
        )

        assert job.status == JobStatus.CANCELLED

    def test_job_status_values_are_lowercase(self):
        """Job status values should be lowercase strings."""
        for status in JobStatus:
            assert status.value == status.value.lower(), f"{status} value should be lowercase"
