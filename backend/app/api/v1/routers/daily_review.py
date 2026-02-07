"""Daily Review API - Serves classified product reviews."""
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, text

from app.core.db import get_db_session
from app.core.auth import get_current_user, CurrentUser
from app.models.autosourcing import AutoSourcingPick, AutoSourcingJob
from app.schemas.daily_review import DailyReviewResponse
from app.services.daily_review_service import generate_daily_review

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/daily-review", tags=["daily-review"])


async def _table_exists(db: AsyncSession, table_name: str) -> bool:
    """Check if a table exists in the database."""
    try:
        result = await db.execute(
            text(
                "SELECT EXISTS ("
                "SELECT FROM information_schema.tables "
                "WHERE table_name = :tname"
                ")"
            ),
            {"tname": table_name},
        )
        return result.scalar() or False
    except Exception:
        return False


@router.get("/today", response_model=DailyReviewResponse)
async def get_daily_review(
    days_back: int = Query(default=1, ge=1, le=7, description="Days of picks to analyze"),
    db: AsyncSession = Depends(get_db_session),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Generate today's daily review from recent AutoSourcing picks."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)

    # Step 1: Fetch recent picks from AutoSourcing jobs
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
            "daily_review: picks query failed",
            exc_info=True,
            extra={"error": str(e), "error_type": type(e).__name__},
        )
        picks_rows = []

    # Step 2: Convert to dicts for classification
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

    # Step 3: Fetch ASIN history (graceful if table missing)
    history_map = {}
    if asin_set:
        try:
            has_history_table = await _table_exists(db, "asin_history")
            if has_history_table:
                from app.models.analytics import ASINHistory

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
            else:
                logger.warning("daily_review: asin_history table does not exist, skipping history")
        except Exception as e:
            logger.error(
                "daily_review: history query failed, continuing without history",
                exc_info=True,
                extra={"error": str(e), "error_type": type(e).__name__},
            )

    # Step 4: Generate and return review
    review = generate_daily_review(picks=picks, history_map=history_map)
    return DailyReviewResponse(**review)
