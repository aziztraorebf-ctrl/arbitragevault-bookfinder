"""Cowork API - External agent endpoints for dashboard, fetch-and-score, and buy list."""
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Security, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.core.db import get_db_session, db_manager
from app.core.settings import get_settings
from app.core.exceptions import InsufficientTokensError
from app.models.autosourcing import AutoSourcingPick, AutoSourcingJob
from app.services.autosourcing_service import AutoSourcingService
from app.services.keepa_service import get_keepa_service
from app.services.daily_review_service import generate_daily_review, generate_actionable_review
from app.schemas.cowork import (
    CoworkBuyListItem,
    CoworkBuyListResponse,
    CoworkDashboardResponse,
    CoworkFetchAndScoreRequest,
    CoworkFetchAndScoreResponse,
    CoworkLastJobStatsResponse,
)

# DB stores naive datetimes (datetime.utcnow) — comparisons must use naive UTC too
def _utcnow_naive() -> datetime:
    return datetime.utcnow()

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

DEFAULT_PROFILE = {
    "profile_name": "cowork-on-demand",
    "categories": ["Books"],
    "max_results": 30,
    "roi_min": 20.0,
}


async def get_autosourcing_service(
    db: AsyncSession = Depends(get_db_session),
) -> AutoSourcingService:
    """Dependency to get AutoSourcing service."""
    keepa_service = await get_keepa_service()
    return AutoSourcingService(db, keepa_service)


@router.get(
    "/dashboard-summary",
    response_model=CoworkDashboardResponse,
    dependencies=[Depends(require_cowork_token)],
)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Return system health, Keepa status, and 24h job/pick statistics."""
    settings = get_settings()
    cutoff = _utcnow_naive() - timedelta(hours=24)

    # Track data quality across sections
    data_quality = "full"

    # DB health
    db_healthy = False
    try:
        db_healthy = await db_manager.health_check()
    except Exception as e:
        data_quality = "degraded"
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
        data_quality = "degraded"
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

        # Deduplicate by ASIN: keep the most recent pick per ASIN
        seen_asins: dict = {}
        for pick in picks_rows:
            if pick.asin not in seen_asins or (pick.created_at and pick.created_at > seen_asins[pick.asin].created_at):
                seen_asins[pick.asin] = pick

        picks_dicts = []
        for pick in seen_asins.values():
            picks_dicts.append({
                "asin": pick.asin,
                "title": pick.title or "",
                "roi_percentage": float(pick.roi_percentage or 0),
                "bsr": int(pick.bsr) if pick.bsr is not None else -1,
                "amazon_on_listing": bool(pick.amazon_on_listing) if pick.amazon_on_listing is not None else False,
                "current_price": float(pick.current_price) if pick.current_price else None,
                "buy_price": float(pick.estimated_buy_cost) if pick.estimated_buy_cost else None,
                "condition_signal": getattr(pick, "condition_signal", None),
                "stability_score": float(pick.stability_score) if getattr(pick, "stability_score", None) else 0.0,
            })

        # Build history_map for proper classification (not empty!)
        history_map: dict = defaultdict(list)
        if picks_dicts:
            asin_set = list({p["asin"] for p in picks_dicts})
            history_cutoff = _utcnow_naive() - timedelta(days=30)
            try:
                history_query = (
                    select(AutoSourcingPick)
                    .join(AutoSourcingJob)
                    .where(
                        and_(
                            AutoSourcingPick.asin.in_(asin_set),
                            AutoSourcingJob.created_at >= history_cutoff,
                            AutoSourcingPick.is_ignored == False,
                        )
                    )
                    .order_by(AutoSourcingPick.created_at.asc())
                )
                history_result = await db.execute(history_query)
                for h in history_result.scalars().all():
                    history_map[h.asin].append({
                        "tracked_at": h.created_at,
                        "bsr": int(h.bsr or -1),
                        "price": float(h.current_price) if h.current_price else None,
                    })
            except Exception as exc:
                logger.warning(
                    "cowork dashboard: history_map query failed, falling back to empty",
                    exc_info=True,
                    extra={"error": str(exc)},
                )

        if picks_dicts:
            review = generate_daily_review(picks=picks_dicts, history_map=dict(history_map))
            total_picks = review.get("total", 0)
            for item in review.get("classified_products", []):
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
        data_quality = "degraded"
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
        "data_quality": data_quality,
    }


@router.post(
    "/fetch-and-score",
    response_model=CoworkFetchAndScoreResponse,
    dependencies=[Depends(require_cowork_token)],
)
async def fetch_and_score(
    request: CoworkFetchAndScoreRequest,
    service: AutoSourcingService = Depends(get_autosourcing_service),
) -> CoworkFetchAndScoreResponse:
    """Trigger an on-demand AutoSourcing search, merging request with DEFAULT_PROFILE."""
    settings = get_settings()
    if not settings.keepa_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Keepa API not configured",
        )

    merged = {**DEFAULT_PROFILE}
    if request.profile_name is not None:
        merged["profile_name"] = request.profile_name
    if request.categories is not None:
        merged["categories"] = request.categories
    if request.max_results is not None:
        merged["max_results"] = request.max_results
    if request.roi_min is not None:
        merged["roi_min"] = request.roi_min

    discovery_config = {
        "categories": merged["categories"],
        "max_results": merged["max_results"],
    }
    scoring_config = {
        "roi_min": merged["roi_min"],
    }

    try:
        job = await service.run_custom_search(
            discovery_config=discovery_config,
            scoring_config=scoring_config,
            profile_name=merged["profile_name"],
        )
        return CoworkFetchAndScoreResponse(
            job_id=str(job.id),
            status=job.status.value if job.status else "unknown",
            picks_count=job.total_selected or 0,
            message="Search completed successfully",
        )
    except InsufficientTokensError:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Insufficient Keepa tokens to run search",
        )
    except Exception as e:
        logger.error(
            "cowork fetch-and-score failed",
            exc_info=True,
            extra={"error": str(e), "error_type": type(e).__name__},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fetch-and-score failed unexpectedly",
        )


@router.get(
    "/daily-buy-list",
    response_model=CoworkBuyListResponse,
    dependencies=[Depends(require_cowork_token)],
)
async def get_daily_buy_list(
    days_back: int = Query(default=1, ge=1, le=7, description="Days of picks to analyze"),
    db: AsyncSession = Depends(get_db_session),
) -> CoworkBuyListResponse:
    """Return actionable daily buy list for external agent consumption."""
    cutoff = _utcnow_naive() - timedelta(days=days_back)
    now_naive = _utcnow_naive()

    # Fetch picks from the requested window
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
    except Exception as e:
        logger.error(
            "cowork daily-buy-list: picks query failed",
            exc_info=True,
            extra={"error": str(e), "error_type": type(e).__name__},
        )
        return CoworkBuyListResponse(
            generated_at=now_naive.isoformat(),
            days_back=days_back,
            total_actionable=0,
            items=[],
            data_quality="unavailable",
        )

    if not picks_rows:
        return CoworkBuyListResponse(
            generated_at=now_naive.isoformat(),
            days_back=days_back,
            total_actionable=0,
            items=[],
        )

    # Build history_map: all past sightings for these ASINs over 30 days
    asins = list({pick.asin for pick in picks_rows})
    history_cutoff = _utcnow_naive() - timedelta(days=30)
    history_map: dict = defaultdict(list)
    try:
        history_query = (
            select(AutoSourcingPick)
            .join(AutoSourcingJob)
            .where(
                and_(
                    AutoSourcingPick.asin.in_(asins),
                    AutoSourcingJob.created_at >= history_cutoff,
                    AutoSourcingPick.is_ignored == False,
                )
            )
            .order_by(AutoSourcingPick.created_at.asc())
        )
        history_result = await db.execute(history_query)
        for h in history_result.scalars().all():
            history_map[h.asin].append({
                "tracked_at": h.created_at,
                "bsr": int(h.bsr or -1),
                "price": float(h.current_price) if h.current_price else None,
            })
    except Exception as e:
        logger.warning(
            "cowork daily-buy-list: history_map query failed, falling back to empty",
            exc_info=True,
            extra={"error": str(e), "error_type": type(e).__name__},
        )

    # Get source_price_factor from business config (seeded at 0.35)
    source_price_factor = 0.35
    try:
        from app.models.business_config import BusinessConfig
        config_result = await db.execute(
            select(BusinessConfig).where(BusinessConfig.scope == "global")
        )
        config = config_result.scalar_one_or_none()
        if config and config.data:
            source_price_factor = config.data.get("roi", {}).get("source_price_factor", 0.35)
    except Exception as e:
        logger.warning(
            "cowork daily-buy-list: failed to load source_price_factor from config, using default",
            exc_info=True,
            extra={"error": str(e), "error_type": type(e).__name__},
        )

    # Convert to dicts for classification
    picks = []
    for pick in picks_rows:
        picks.append({
            "asin": pick.asin,
            "title": pick.title or "",
            "roi_percentage": float(pick.roi_percentage or 0),
            "bsr": int(pick.bsr or -1),
            "amazon_on_listing": bool(pick.amazon_on_listing),
            "current_price": float(pick.current_price) if pick.current_price else None,
            "buy_price": float(pick.estimated_buy_cost) if pick.estimated_buy_cost else None,
            "condition_signal": getattr(pick, "condition_signal", None),
            "stability_score": float(pick.stability_score) if getattr(pick, "stability_score", None) else 0.0,
        })

    # Generate actionable review with real history and correct source_price_factor
    try:
        review = generate_actionable_review(
            picks=picks,
            history_map=dict(history_map),
            source_price_factor=source_price_factor,
        )
        items = [
            CoworkBuyListItem(
                asin=item.get("asin", ""),
                title=item.get("title"),
                classification=item.get("classification", ""),
                roi=item.get("roi_percentage"),
                bsr=item.get("bsr"),
                action=item.get("action_recommendation", ""),
                first_seen_at=None,
            )
            for item in review.get("items", [])
        ]
        return CoworkBuyListResponse(
            generated_at=review.get("generated_at", now_naive.isoformat()),
            days_back=days_back,
            total_actionable=len(items),
            items=items,
        )
    except Exception as e:
        logger.error(
            "cowork daily-buy-list: generate_actionable_review failed",
            exc_info=True,
            extra={"error": str(e), "error_type": type(e).__name__},
        )
        return CoworkBuyListResponse(
            generated_at=now_naive.isoformat(),
            days_back=days_back,
            total_actionable=0,
            items=[],
            data_quality="degraded",
        )


@router.get(
    "/last-job-stats",
    response_model=CoworkLastJobStatsResponse,
    dependencies=[Depends(require_cowork_token)],
)
async def get_last_job_stats(
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Return pipeline stats for the most recent AutoSourcing job."""
    try:
        result = await db.execute(
            select(AutoSourcingJob)
            .order_by(AutoSourcingJob.created_at.desc())
            .limit(1)
        )
        job = result.scalars().first()
        if not job:
            return {
                "job_id": None,
                "status": None,
                "total_tested": 0,
                "total_selected": 0,
                "created_at": None,
            }
        return {
            "job_id": str(job.id),
            "status": job.status.value if job.status else None,
            "total_tested": job.total_tested or 0,
            "total_selected": job.total_selected or 0,
            "created_at": job.created_at.isoformat() if job.created_at else None,
        }
    except Exception as e:
        logger.error(
            "cowork last-job-stats failed",
            exc_info=True,
            extra={"error": str(e), "error_type": type(e).__name__},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve last job stats",
        )
