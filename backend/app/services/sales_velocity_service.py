"""
Sales Velocity Service - Estimation des ventes et classification intelligente
Calcule les métriques de vélocité basées sur les données Keepa
"""
from typing import Dict, Any, Optional
import math
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SalesVelocityService:
    """Service for estimating sales velocity and classifying opportunities"""
    
    def __init__(self):
        """Initialize with smart tier thresholds"""
        self.tier_thresholds = {
            'PREMIUM': 100,   # 100+ ventes/mois - Cashflow machines
            'HIGH': 50,       # 50-99 ventes/mois - Strong velocity  
            'MEDIUM': 20,     # 20-49 ventes/mois - Decent turnover
            'LOW': 5,         # 5-19 ventes/mois - Slow movers
            'DEAD': 0         # 0-4 ventes/mois - Avoid
        }
        
        # Category multipliers for more accurate estimates
        self.category_multipliers = {
            'Books': 1.0,
            'Textbooks': 0.8,     # Seasonal patterns
            'Electronics': 1.2,   # Higher velocity
            'Home & Kitchen': 1.1,
            'Health': 0.9,
            'default': 1.0
        }
    
    def estimate_monthly_sales(self, sales_drops_30: int, bsr: int, category: str = "Books") -> int:
        """
        Smart estimation of monthly sales based on Keepa data
        
        Args:
            sales_drops_30: Number of BSR drops in last 30 days from Keepa
            bsr: Current Best Seller Rank
            category: Product category for context
            
        Returns:
            Estimated monthly sales count
        """
        try:
            # Base estimation from sales rank drops
            base_estimate = sales_drops_30 * self._get_category_multiplier(category)
            
            # BSR adjustment for context
            bsr_multiplier = self._get_bsr_multiplier(bsr)
            adjusted_estimate = base_estimate * bsr_multiplier
            
            # Ensure reasonable bounds
            return max(0, int(adjusted_estimate))
            
        except Exception as e:
            logger.error(f"Error estimating monthly sales: {e}")
            return 0
    
    def estimate_quarterly_sales(self, sales_drops_90: int, bsr: int, category: str = "Books") -> int:
        """Estimate quarterly sales from 90-day data"""
        try:
            # Similar logic but for 90 days
            base_estimate = sales_drops_90 * self._get_category_multiplier(category)
            bsr_multiplier = self._get_bsr_multiplier(bsr)
            
            return max(0, int(base_estimate * bsr_multiplier))
            
        except Exception as e:
            logger.error(f"Error estimating quarterly sales: {e}")
            return 0
    
    def classify_velocity_tier(self, monthly_sales: int) -> str:
        """
        Classify monthly sales into smart velocity tiers
        
        Args:
            monthly_sales: Estimated monthly sales
            
        Returns:
            Velocity tier: PREMIUM, HIGH, MEDIUM, LOW, or DEAD
        """
        for tier, threshold in self.tier_thresholds.items():
            if monthly_sales >= threshold:
                return tier
        return 'DEAD'
    
    def calculate_opportunity_score(self, roi_percent: float, profit_net: float, monthly_sales: int) -> float:
        """
        Calculate composite opportunity score
        Formula: (ROI/100) × √Monthly_Sales × Profit_Net
        
        Args:
            roi_percent: ROI percentage (e.g., 45 for 45%)
            profit_net: Net profit in dollars
            monthly_sales: Estimated monthly sales
            
        Returns:
            Composite opportunity score
        """
        try:
            if roi_percent <= 0 or profit_net <= 0 or monthly_sales < 0:
                return 0.0
            
            # Composite formula balancing all factors
            roi_factor = roi_percent / 100
            velocity_factor = math.sqrt(max(monthly_sales, 1))
            profit_factor = profit_net
            
            score = roi_factor * velocity_factor * profit_factor
            
            # Round to 2 decimals for cleaner display
            return round(score, 2)
            
        except Exception as e:
            logger.error(f"Error calculating opportunity score: {e}")
            return 0.0
    
    def get_velocity_metadata(self, tier: str) -> Dict[str, Any]:
        """Get metadata for velocity tier"""
        tier_metadata = {
            'PREMIUM': {
                'icon': '🚀',
                'description': 'Cashflow machine - 100+ sales/month',
                'strategy': 'Buy aggressively (10-20 units)',
                'risk_level': 'Low',
                'recommended_for': 'High-volume cashflow focus'
            },
            'HIGH': {
                'icon': '⚡',
                'description': 'Strong velocity - 50-99 sales/month',
                'strategy': 'Bulk purchase OK (5-10 units)',
                'risk_level': 'Low-Medium',
                'recommended_for': 'Balanced growth strategy'
            },
            'MEDIUM': {
                'icon': '🎯',
                'description': 'Decent turnover - 20-49 sales/month',
                'strategy': 'Standard quantity (2-5 units)',
                'risk_level': 'Medium',
                'recommended_for': 'Safe, steady profits'
            },
            'LOW': {
                'icon': '🐌',
                'description': 'Slow mover - 5-19 sales/month',
                'strategy': 'Minimal buy (1-2 units max)',
                'risk_level': 'Medium-High',
                'recommended_for': 'High-margin focus only'
            },
            'DEAD': {
                'icon': '💀',
                'description': 'Stagnant - Under 5 sales/month',
                'strategy': 'Avoid - Money trap',
                'risk_level': 'High',
                'recommended_for': 'Not recommended'
            }
        }
        
        return tier_metadata.get(tier, tier_metadata['DEAD'])
    
    def _get_category_multiplier(self, category: str) -> float:
        """Get category-specific multiplier for sales estimation"""
        return self.category_multipliers.get(category, self.category_multipliers['default'])
    
    def _get_bsr_multiplier(self, bsr: int) -> float:
        """Get BSR-based multiplier for sales estimation"""
        if bsr <= 0:
            return 1.0
        elif bsr < 10000:
            return 1.5      # Best-sellers get boost
        elif bsr < 50000:
            return 1.2      # Popular products
        elif bsr < 100000:
            return 1.0      # Average
        elif bsr < 500000:
            return 0.8      # Lower velocity
        else:
            return 0.6      # Long-tail penalty
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics and configuration"""
        return {
            "service": "sales_velocity",
            "version": "1.0.0",
            "tier_thresholds": self.tier_thresholds,
            "category_multipliers": self.category_multipliers,
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }


# Dependency injection for FastAPI
sales_velocity_service_instance = SalesVelocityService()


def get_sales_velocity_service() -> SalesVelocityService:
    """FastAPI dependency to get Sales Velocity service instance"""
    return sales_velocity_service_instance