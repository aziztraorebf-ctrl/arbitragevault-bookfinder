"""
Celery tasks for ASIN tracking (Phase 8.2)
Background jobs for daily ASIN history tracking.
"""
from typing import List, Dict, Any
import structlog
from celery import shared_task

from app.core.db import get_db_engine
from app.services.asin_tracking_service import ASINTrackingService
from app.services.keepa_service import KeepaService
from app.core.settings import get_settings


logger = structlog.get_logger()


@shared_task(name="track_asin_daily", bind=True, max_retries=3)
def track_asin_daily(self, asin: str, keepa_domain: int = 1) -> Dict[str, Any]:
    """
    Celery task to track a single ASIN's metrics daily.

    Args:
        asin: ASIN to track
        keepa_domain: Keepa domain ID (default 1 = Amazon.com)

    Returns:
        Dict with tracking result
    """
    try:
        settings = get_settings()
        keepa_service = KeepaService(api_key=settings.keepa_api_key)
        tracking_service = ASINTrackingService(keepa_service)

        import asyncio
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

        engine = create_async_engine(
            settings.database_url,
            echo=False,
            pool_pre_ping=True
        )
        SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async def _track():
            async with SessionLocal() as session:
                result = await tracking_service.track_asin_daily(
                    session=session,
                    asin=asin,
                    keepa_domain=keepa_domain
                )
                if result:
                    await session.commit()
                return {
                    'asin': asin,
                    'status': 'success',
                    'bsr': result.bsr if result else None,
                    'price': float(result.price) if result and result.price else None,
                    'seller_count': result.seller_count if result else None
                }

        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_track())

    except Exception as e:
        logger.error(f"Error tracking ASIN {asin}: {str(e)}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task(name="track_multiple_asins", bind=True, max_retries=2)
def track_multiple_asins(
    self,
    asins: List[str],
    keepa_domain: int = 1
) -> Dict[str, Any]:
    """
    Celery task to track multiple ASINs in batch.

    Args:
        asins: List of ASINs to track
        keepa_domain: Keepa domain ID

    Returns:
        Dict with batch tracking results
    """
    try:
        settings = get_settings()
        keepa_service = KeepaService(api_key=settings.keepa_api_key)
        tracking_service = ASINTrackingService(keepa_service)

        import asyncio
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

        engine = create_async_engine(
            settings.database_url,
            echo=False,
            pool_pre_ping=True
        )
        SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async def _track_batch():
            async with SessionLocal() as session:
                results = await tracking_service.track_multiple_asins(
                    session=session,
                    asins=asins,
                    keepa_domain=keepa_domain
                )

                summary = {
                    'total': len(asins),
                    'tracked': sum(1 for r in results.values() if r),
                    'failed': sum(1 for r in results.values() if not r),
                    'details': {}
                }

                for asin, result in results.items():
                    if result:
                        summary['details'][asin] = {
                            'status': 'success',
                            'bsr': result.bsr,
                            'price': float(result.price) if result.price else None,
                            'seller_count': result.seller_count
                        }
                    else:
                        summary['details'][asin] = {
                            'status': 'failed'
                        }

                return summary

        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_track_batch())

    except Exception as e:
        logger.error(f"Error batch tracking {len(asins)} ASINs: {str(e)}")
        raise self.retry(exc=e, countdown=120 * (2 ** self.request.retries))


@shared_task(name="track_autosourcing_picks", bind=True)
def track_autosourcing_picks(self, job_id: str) -> Dict[str, Any]:
    """
    Track ASINs from a completed AutoSourcing job.
    Extracts picks from job result and starts daily tracking.

    Args:
        job_id: AutoSourcing job ID

    Returns:
        Dict with tracking initiation result
    """
    try:
        from app.models.autosourcing import AutoSourcingJob
        from sqlalchemy import select

        import asyncio
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

        settings = get_settings()
        engine = create_async_engine(
            settings.database_url,
            echo=False,
            pool_pre_ping=True
        )
        SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async def _get_picks():
            async with SessionLocal() as session:
                stmt = select(AutoSourcingJob).where(AutoSourcingJob.id == job_id)
                result = await session.execute(stmt)
                job = result.scalar_one_or_none()

                if not job or not job.picks:
                    return {'status': 'no_picks_found', 'job_id': job_id}

                asins = [pick.asin for pick in job.picks]

                tracking_service = ASINTrackingService(
                    KeepaService(api_key=settings.keepa_api_key)
                )
                track_results = await tracking_service.track_multiple_asins(
                    session=session,
                    asins=asins,
                    keepa_domain=1
                )

                return {
                    'status': 'started',
                    'job_id': job_id,
                    'picks_count': len(asins),
                    'tracked': sum(1 for r in track_results.values() if r)
                }

        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_get_picks())

    except Exception as e:
        logger.error(f"Error tracking picks for job {job_id}: {str(e)}")
        return {'status': 'error', 'job_id': job_id, 'error': str(e)}
