"""Cowork API - External agent endpoints for dashboard, fetch-and-score, and buy list."""
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Security, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.core.db import get_db_session, db_manager
from app.core.settings import get_settings
from app.models.autosourcing import AutoSourcingPick, AutoSourcingJob
from app.services.daily_review_service import generate_daily_review

logger = logging.getLogger(__name__)

cowork_bearer = HTTPBearer(auto_error=False)


async def require_cowork_token(
    credentials: HTTPAuthorizationCredentials = Security(cowork_bearer),
) -> None:
    """Validate the Cowork Bearer token from the Authorization header."""
    settings = get_settings()
    if not settings.cowork_api_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cowork API not configured -- set COWORK_API_TOKEN",
        )
    if not credentials or credentials.credentials != settings.cowork_api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Cowork token",
        )


router = APIRouter(prefix="/cowork", tags=["Cowork"])


@router.get("/dashboard-summary", dependencies=[Depends(require_cowork_token)])
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Return system health, Keepa status, and 24h job/pick statistics."""
    settings = get_settings()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

    # DB health
    db_healthy = False
    try:
        db_healthy = await db_manager.health_check()
    except Exception as e:
        logger.error(
            "cowork dashboard: health_check failed",
            exc_info=True,
            extra={"error": str(e), "error_type": type(e).__name__},
        )

    # AutoSourcing stats
    jobs_last_24h = 0
    picks_last_24h = 0
    last_run_at = None
    last_run_status = None
    try:
        job_count_result = await db.execute(
            select(func.count(AutoSourcingJob.id)).where(
                AutoSourcingJob.created_at >= cutoff,
            )
        )
        jobs_last_24h = job_count_result.scalar() or 0

        pick_count_result = await db.execute(
            select(func.count(AutoSourcingPick.id))
            .join(AutoSourcingJob)
            .where(
                and_(
                    AutoSourcingJob.created_at >= cutoff,
                    AutoSourcingPick.is_ignored == False,
                )
            )
        )
        picks_last_24h = pick_count_result.scalar() or 0

        latest_job_result = await db.execute(
            select(AutoSourcingJob)
            .order_by(AutoSourcingJob.created_at.desc())
            .limit(1)
        )
        latest_job = latest_job_result.scalars().first()
        if latest_job:
            last_run_at = latest_job.created_at.isoformat() if latest_job.created_at else None
            last_run_status = latest_job.status.value if latest_job.status else None
    except Exception as e:
        logger.error(
            "cowork dashboard: autosourcing stats query failed",
            exc_info=True,
            extra={"error": str(e), "error_type": type(e).__name__},
        )

    # Daily review classification stats
    total_picks = 0
    jackpot = 0
    stable = 0
    revenant = 0
    fluke = 0
    reject = 0
    try:
        picks_query = (
            select(AutoSourcingPick)
            .join(AutoSourcingJob)
            .where(
                and_(
                    AutoSourcingJob.created_at >= cutoff,
                    AutoSourcingPick.is_ignored == False,
                )
            )
        )
        result = await db.execute(picks_query)
        picks_rows = result.scalars().all()

        picks_dicts = []
        for pick in picks_rows:
            picks_dicts.append({
                "asin": pick.asin,
                "title": pick.title or "",
                "roi_percentage": float(pick.roi_percentage or 0),
                "bsr": int(pick.bsr or -1),
                "amazon_on_listing": bool(pick.amazon_on_listing),
                "current_price": float(pick.current_price) if pick.current_price else None,
                "buy_price": float(pick.estimated_buy_cost) if pick.estimated_buy_cost else None,
            })

        if picks_dicts:
            review = generate_daily_review(picks=picks_dicts, history_map={})
            total_picks = review.get("total_picks", 0)
            for item in review.get("picks", []):
                classification = item.get("classification", "").upper()
                if classification == "JACKPOT":
                    jackpot += 1
                elif classification == "STABLE":
                    stable += 1
                elif classification == "REVENANT":
                    revenant += 1
                elif classification == "FLUKE":
                    fluke += 1
                elif classification == "REJECT":
                    reject += 1
    except Exception as e:
        logger.error(
            "cowork dashboard: daily review stats failed",
            exc_info=True,
            extra={"error": str(e), "error_type": type(e).__name__},
        )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "app_version": "1.0.0",
        "environment": settings.environment if hasattr(settings, "environment") else "production",
        "db_healthy": db_healthy,
        "keepa_configured": bool(settings.keepa_api_key),
        "autosourcing": {
            "jobs_last_24h": jobs_last_24h,
            "picks_last_24h": picks_last_24h,
            "last_run_at": last_run_at,
            "last_run_status": last_run_status,
        },
        "daily_review": {
            "total_picks": total_picks,
            "jackpot": jackpot,
            "stable": stable,
            "revenant": revenant,
            "fluke": fluke,
            "reject": reject,
        },
    }
