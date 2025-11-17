"""
ASIN Tracking Service (Phase 8.2)
Background job service for daily ASIN history tracking via Keepa API.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import structlog

from app.models.analytics import ASINHistory
from app.models.keepa_models import KeepaProduct
from app.services.keepa_service import KeepaService


logger = structlog.get_logger()


class ASINTrackingService:
    """Service for tracking ASIN historical metrics."""

    def __init__(self, keepa_service: KeepaService):
        self.keepa_service = keepa_service

    async def track_asin_daily(
        self,
        session: AsyncSession,
        asin: str,
        keepa_domain: int = 1
    ) -> Optional[ASINHistory]:
        """
        Track an ASIN's current metrics and store in history table.

        Args:
            session: Database session
            asin: ASIN to track
            keepa_domain: Keepa domain ID (1=.com, etc.)

        Returns:
            ASINHistory record created, or None if fetch failed
        """
        try:
            keepa_data = await self.keepa_service.get_product_data(
                asin=asin,
                domain=keepa_domain,
                include_history=False,
                include_offers=False
            )

            if not keepa_data:
                logger.warning(f"No Keepa data for {asin}")
                return None

            product_data = keepa_data.get('data', [{}])[0]

            price = self._extract_numeric(product_data.get('value'))
            lowest_fba = self._extract_numeric(product_data.get('fba_price'))
            bsr = product_data.get('sales_rank_drop_30', product_data.get('sales_rank'))
            seller_count = product_data.get('offers_count')
            amazon_on_listing = product_data.get('is_amazon', False)

            amazon_buybox_prices = product_data.get('amazon_buybox_prices')
            fba_seller_count = None
            if seller_count and amazon_buybox_prices:
                fba_offers = [
                    o for o in product_data.get('offers', [])
                    if o.get('isFBA')
                ]
                fba_seller_count = len(fba_offers)

            history = ASINHistory(
                asin=asin,
                tracked_at=datetime.utcnow(),
                price=price,
                lowest_fba_price=lowest_fba,
                bsr=bsr,
                seller_count=seller_count,
                amazon_on_listing=amazon_on_listing,
                fba_seller_count=fba_seller_count,
                extra_data={
                    'keepa_domain': keepa_domain,
                    'title': product_data.get('title'),
                    'category_id': product_data.get('category_id'),
                    'image_url': product_data.get('image')
                }
            )

            session.add(history)
            await session.flush()

            logger.info(
                f"tracked_asin",
                asin=asin,
                bsr=bsr,
                price=price,
                seller_count=seller_count
            )

            return history

        except Exception as e:
            logger.error(f"Error tracking ASIN {asin}: {str(e)}")
            return None

    async def track_multiple_asins(
        self,
        session: AsyncSession,
        asins: List[str],
        keepa_domain: int = 1
    ) -> Dict[str, Optional[ASINHistory]]:
        """
        Track multiple ASINs in batch.

        Args:
            session: Database session
            asins: List of ASINs to track
            keepa_domain: Keepa domain ID

        Returns:
            Dict mapping ASIN to ASINHistory record (or None if failed)
        """
        results = {}
        for asin in asins:
            result = await self.track_asin_daily(session, asin, keepa_domain)
            results[asin] = result

        await session.commit()
        return results

    async def get_asin_history(
        self,
        session: AsyncSession,
        asin: str,
        days: int = 90
    ) -> List[ASINHistory]:
        """
        Get historical records for an ASIN.

        Args:
            session: Database session
            asin: ASIN to fetch history for
            days: Number of days of history to return

        Returns:
            List of ASINHistory records
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        stmt = select(ASINHistory).where(
            and_(
                ASINHistory.asin == asin,
                ASINHistory.tracked_at >= cutoff_date
            )
        ).order_by(ASINHistory.tracked_at.asc())

        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_asin_trends(
        self,
        session: AsyncSession,
        asin: str,
        days: int = 90
    ) -> Dict[str, Any]:
        """
        Analyze trends from ASIN history.

        Args:
            session: Database session
            asin: ASIN to analyze
            days: Number of days of history to analyze

        Returns:
            Dict with trend analysis
        """
        history = await self.get_asin_history(session, asin, days)

        if not history:
            return {
                'asin': asin,
                'data_points': 0,
                'trend': 'NO_DATA'
            }

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
                'trend': 'improving' if bsr_values[-1] < bsr_values[0] else 'declining'
            }

        if price_values:
            trend_data['price'] = {
                'current': round(price_values[-1], 2),
                'average': round(sum(price_values) / len(price_values), 2),
                'min': round(min(price_values), 2),
                'max': round(max(price_values), 2)
            }

        if seller_counts:
            trend_data['sellers'] = {
                'current': seller_counts[-1],
                'average': int(sum(seller_counts) / len(seller_counts)),
                'min': min(seller_counts),
                'max': max(seller_counts)
            }

        return trend_data

    @staticmethod
    def _extract_numeric(value: Any) -> Optional[Decimal]:
        """Extract numeric value safely."""
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            return None
