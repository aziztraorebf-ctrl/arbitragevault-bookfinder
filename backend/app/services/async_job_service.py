"""
Async Job Service - Database persistence for batch processing jobs.

Provides functions to:
- Create async job records
- Update job status during processing
- Store results and error information
- Track job completion with metrics
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.autosourcing import AutoSourcingJob, JobStatus

import logging

logger = logging.getLogger(__name__)


async def create_async_job(
    db: AsyncSession,
    profile_name: str,
    identifiers: List[str],
    discovery_config: Dict[str, Any],
    scoring_config: Dict[str, Any],
    profile_id: Optional[UUID] = None
) -> AutoSourcingJob:
    """
    Create a new async job record in the database.

    Args:
        db: Async database session
        profile_name: Name of the search profile
        identifiers: List of ASINs/ISBNs to process
        discovery_config: Keepa search criteria
        scoring_config: Scoring thresholds
        profile_id: Optional link to SavedProfile

    Returns:
        AutoSourcingJob: The created job record with UUID
    """
    job = AutoSourcingJob(
        profile_name=profile_name,
        profile_id=profile_id,
        status=JobStatus.PENDING,
        total_tested=0,
        total_selected=0,
        discovery_config=discovery_config,
        scoring_config=scoring_config,
        error_count=0,
        launched_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc)
    )

    db.add(job)
    await db.flush()

    logger.info(
        f"Created async job {job.id} for profile '{profile_name}' "
        f"with {len(identifiers)} identifiers"
    )

    return job


async def update_job_status(
    db: AsyncSession,
    job_id: UUID,
    status: JobStatus
) -> AutoSourcingJob:
    """
    Update the status of an async job.

    Args:
        db: Async database session
        job_id: UUID of the job to update
        status: New JobStatus value

    Returns:
        AutoSourcingJob: Updated job record

    Raises:
        ValueError: If job_id does not exist
    """
    result = await db.execute(
        select(AutoSourcingJob).where(AutoSourcingJob.id == job_id)
    )
    job = result.scalar_one_or_none()

    if job is None:
        raise ValueError(f"Job not found: {job_id}")

    job.status = status
    await db.flush()

    logger.info(f"Updated job {job_id} status to {status.value}")

    return job


async def set_job_error(
    db: AsyncSession,
    job_id: UUID,
    error_message: str
) -> AutoSourcingJob:
    """
    Set job status to ERROR and store error details.

    Args:
        db: Async database session
        job_id: UUID of the job
        error_message: Description of the error

    Returns:
        AutoSourcingJob: Updated job record

    Raises:
        ValueError: If job_id does not exist
    """
    result = await db.execute(
        select(AutoSourcingJob).where(AutoSourcingJob.id == job_id)
    )
    job = result.scalar_one_or_none()

    if job is None:
        raise ValueError(f"Job not found: {job_id}")

    job.status = JobStatus.ERROR
    job.error_message = error_message
    job.error_count = (job.error_count or 0) + 1
    await db.flush()

    logger.warning(f"Job {job_id} error #{job.error_count}: {error_message}")

    return job


async def complete_job(
    db: AsyncSession,
    job_id: UUID,
    total_tested: int,
    total_selected: int
) -> AutoSourcingJob:
    """
    Mark job as completed with results summary.

    Args:
        db: Async database session
        job_id: UUID of the job
        total_tested: Number of identifiers processed
        total_selected: Number of products that passed filters

    Returns:
        AutoSourcingJob: Updated job record

    Raises:
        ValueError: If job_id does not exist
    """
    result = await db.execute(
        select(AutoSourcingJob).where(AutoSourcingJob.id == job_id)
    )
    job = result.scalar_one_or_none()

    if job is None:
        raise ValueError(f"Job not found: {job_id}")

    now = datetime.now(timezone.utc)
    job.status = JobStatus.SUCCESS
    job.completed_at = now
    job.total_tested = total_tested
    job.total_selected = total_selected

    # Calculate duration in milliseconds
    if job.launched_at:
        duration = now - job.launched_at
        job.duration_ms = int(duration.total_seconds() * 1000)

    await db.flush()

    logger.info(
        f"Completed job {job_id}: tested={total_tested}, "
        f"selected={total_selected}, duration={job.duration_ms}ms"
    )

    return job


async def get_job_by_id(
    db: AsyncSession,
    job_id: UUID
) -> Optional[AutoSourcingJob]:
    """
    Retrieve a job by its ID.

    Args:
        db: Async database session
        job_id: UUID of the job

    Returns:
        AutoSourcingJob or None if not found
    """
    result = await db.execute(
        select(AutoSourcingJob).where(AutoSourcingJob.id == job_id)
    )
    return result.scalar_one_or_none()


async def cancel_job(
    db: AsyncSession,
    job_id: UUID
) -> AutoSourcingJob:
    """
    Cancel a pending or running job.

    Args:
        db: Async database session
        job_id: UUID of the job to cancel

    Returns:
        AutoSourcingJob: Updated job record

    Raises:
        ValueError: If job_id does not exist
    """
    result = await db.execute(
        select(AutoSourcingJob).where(AutoSourcingJob.id == job_id)
    )
    job = result.scalar_one_or_none()

    if job is None:
        raise ValueError(f"Job not found: {job_id}")

    job.status = JobStatus.CANCELLED
    job.completed_at = datetime.now(timezone.utc)

    logger.info(f"Cancelled job {job_id}")

    return job
