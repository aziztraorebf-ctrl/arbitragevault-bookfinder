"""
ASIN History endpoints (Phase 8.2)
Endpoints for viewing and managing ASIN historical data.
"""
from typing import List
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from datetime import datetime, timedelta

from app.core.db import get_db_session
from app.models.analytics import ASINHistory
from app.schemas.analytics import AnalyticsHistorySchema


router = APIRouter(prefix="/asin-history", tags=["ASIN History"])


@router.get("/trends/{asin}", response_model=dict)
async def get_asin_trends(
    asin: str,
    days: int = Query(90, ge=1, le=365),
    db: AsyncSession = Depends(get_db_session)
) -> dict:
    """
    Get historical trends for an ASIN.

    Args:
        asin: ASIN to get trends for
        days: Number of days of history (default 90, max 365)

    Returns:
        Dict with trend analysis including BSR, price, seller changes
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        stmt = select(ASINHistory).where(
            and_(
                ASINHistory.asin == asin,
                ASINHistory.tracked_at >= cutoff_date
            )
        ).order_by(ASINHistory.tracked_at.asc())

        result = await db.execute(stmt)
        history = result.scalars().all()

        if not history:
            raise HTTPException(status_code=404, detail=f"No history found for ASIN {asin}")

        bsr_values = [h.bsr for h in history if h.bsr]
        price_values = [float(h.price) for h in history if h.price]
        seller_counts = [h.seller_count for h in history if h.seller_count]

        trend_data = {
            'asin': asin,
            'data_points': len(history),
            'date_range': {
                'start': history[0].tracked_at.isoformat() if history else None,
                'end': history[-1].tracked_at.isoformat() if history else None
            }
        }

        if bsr_values:
            trend_data['bsr'] = {
                'current': bsr_values[-1],
                'earliest': bsr_values[0],
                'lowest_rank': min(bsr_values),
                'highest_rank': max(bsr_values),
                'trend': 'improving' if bsr_values[-1] < bsr_values[0] else 'declining',
                'change': bsr_values[-1] - bsr_values[0]
            }

        if price_values:
            trend_data['price'] = {
                'current': round(price_values[-1], 2),
                'average': round(sum(price_values) / len(price_values), 2),
                'min': round(min(price_values), 2),
                'max': round(max(price_values), 2),
                'volatility': round(max(price_values) - min(price_values), 2)
            }

        if seller_counts:
            trend_data['sellers'] = {
                'current': seller_counts[-1],
                'average': int(sum(seller_counts) / len(seller_counts)),
                'min': min(seller_counts),
                'max': max(seller_counts),
                'trend': 'decreasing' if seller_counts[-1] < seller_counts[0] else 'increasing'
            }

        return trend_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trends: {str(e)}")


@router.get("/records/{asin}", response_model=List[AnalyticsHistorySchema])
async def get_asin_history_records(
    asin: str,
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db_session)
) -> List[AnalyticsHistorySchema]:
    """
    Get historical records for an ASIN.

    Args:
        asin: ASIN to get history for
        days: Number of days of history
        limit: Maximum number of records to return

    Returns:
        List of ASIN history records
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        stmt = select(ASINHistory).where(
            and_(
                ASINHistory.asin == asin,
                ASINHistory.tracked_at >= cutoff_date
            )
        ).order_by(desc(ASINHistory.tracked_at)).limit(limit)

        result = await db.execute(stmt)
        history_records = result.scalars().all()

        return [
            AnalyticsHistorySchema(
                id=h.id,
                asin=h.asin,
                tracked_at=h.tracked_at.isoformat(),
                price=float(h.price) if h.price else None,
                bsr=h.bsr,
                seller_count=h.seller_count,
                amazon_on_listing=h.amazon_on_listing,
                metadata=h.extra_data
            )
            for h in history_records
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching records: {str(e)}")


@router.get("/latest/{asin}", response_model=AnalyticsHistorySchema)
async def get_latest_asin_record(
    asin: str,
    db: AsyncSession = Depends(get_db_session)
) -> AnalyticsHistorySchema:
    """
    Get the latest tracking record for an ASIN.

    Args:
        asin: ASIN to get latest record for

    Returns:
        Latest ASIN history record
    """
    try:
        stmt = select(ASINHistory).where(
            ASINHistory.asin == asin
        ).order_by(desc(ASINHistory.tracked_at)).limit(1)

        result = await db.execute(stmt)
        record = result.scalar_one_or_none()

        if not record:
            raise HTTPException(status_code=404, detail=f"No records found for ASIN {asin}")

        return AnalyticsHistorySchema(
            id=record.id,
            asin=record.asin,
            tracked_at=record.tracked_at.isoformat(),
            price=float(record.price) if record.price else None,
            bsr=record.bsr,
            seller_count=record.seller_count,
            amazon_on_listing=record.amazon_on_listing,
            metadata=record.extra_data
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching record: {str(e)}")
