"""Daily Review API - Serves classified product reviews."""
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.db import get_db_session
from app.core.auth import get_current_user, CurrentUser
from app.models.autosourcing import AutoSourcingPick, AutoSourcingJob, ActionStatus
from app.models.analytics import ASINHistory
from app.schemas.daily_review import DailyReviewResponse
from app.services.daily_review_service import generate_daily_review

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/daily-review", tags=["daily-review"])


@router.get("/today", response_model=DailyReviewResponse)
async def get_daily_review(
    days_back: int = Query(default=1, ge=1, le=7, description="Days of picks to analyze"),
    db: AsyncSession = Depends(get_db_session),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Generate today's daily review from recent AutoSourcing picks."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)

    # Fetch recent picks (non-ignored) from AutoSourcing jobs
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

    # Convert to dicts for classification
    picks = []
    asin_set = set()
    for pick in picks_rows:
        asin_set.add(pick.asin)
        picks.append({
            "asin": pick.asin,
            "title": pick.title or "",
            "roi_percentage": float(pick.roi_percentage or 0),
            "bsr": int(pick.bsr or -1),
            "amazon_on_listing": bool(pick.amazon_on_listing),
            "current_price": float(pick.current_price) if pick.current_price else None,
            "buy_price": float(pick.estimated_buy_cost) if pick.estimated_buy_cost else None,
        })

    # Fetch history for all ASINs in one query
    history_map = {}
    if asin_set:
        history_cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        history_query = (
            select(ASINHistory)
            .where(
                and_(
                    ASINHistory.asin.in_(asin_set),
                    ASINHistory.tracked_at >= history_cutoff,
                )
            )
        )
        hist_result = await db.execute(history_query)
        for row in hist_result.scalars().all():
            history_map.setdefault(row.asin, []).append({
                "tracked_at": row.tracked_at,
                "bsr": row.bsr,
                "price": float(row.price) if row.price else None,
            })

    review = generate_daily_review(picks=picks, history_map=history_map)
    return DailyReviewResponse(**review)
