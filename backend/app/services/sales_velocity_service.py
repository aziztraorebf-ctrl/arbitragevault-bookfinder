"""
Sales Velocity Service
Estimation intelligente des ventes mensuelles basée sur les données Keepa
"""
from typing import Dict, Any, List
from datetime import datetime
import math
import logging

logger = logging.getLogger(__name__)


class SalesVelocityService:
    """Service for estimating sales velocity from Keepa data"""
    
    def __init__(self):
        # Configuration des seuils de classification
        self.tier_thresholds = {
            'PREMIUM': 100,   # 100+ ventes/mois - Cashflow machine
            'HIGH': 50,       # 50-99 ventes/mois - Strong velocity
            'MEDIUM': 20,     # 20-49 ventes/mois - Decent turnover
            'LOW': 5,         # 5-19 ventes/mois - Slow mover
            'DEAD': 0         # 0-4 ventes/mois - Avoid
        }
        
        # Multiplicateurs par catégorie (ajustements contextuels)
        self.category_multipliers = {
            'Books': 1.0,
            'Electronics': 1.2,
            'Health': 0.9,
            'Sports': 1.1,
            'Home': 0.8,
            'Unknown': 1.0
        }
        
        # Configuration scoring
        self.scoring_config = {
            'roi_weight': 1.0,
            'velocity_weight': 1.0,
            'profit_weight': 1.0
        }
    
    def estimate_monthly_sales(self, sales_drops_30: int, bsr: int, category: str = 'Unknown') -> int:
        """
        Estimer les ventes mensuelles à partir des données Keepa
        
        Args:
            sales_drops_30: Nombre de drops BSR sur 30 jours (de Keepa)
            bsr: Best Seller Rank actuel
            category: Catégorie du produit
            
        Returns:
            Estimation des ventes mensuelles
        """
        try:
            # Base estimation from sales drops
            base_estimate = sales_drops_30 * self._get_category_multiplier(category)
            
            # BSR adjustments (contextual)
            if bsr > 0:
                if bsr < 10000:
                    # Best-sellers: boost estimation
                    base_estimate *= 1.5
                elif bsr < 50000:
                    # Good performers: slight boost
                    base_estimate *= 1.2
                elif bsr > 500000:
                    # Long-tail: penalty
                    base_estimate *= 0.7
                elif bsr > 1000000:
                    # Very long-tail: significant penalty
                    base_estimate *= 0.4
            
            # Ensure reasonable bounds
            monthly_estimate = max(0, int(base_estimate))
            monthly_estimate = min(monthly_estimate, 1000)  # Cap at 1000/month for sanity
            
            logger.debug(f"Sales estimate: drops={sales_drops_30}, BSR={bsr}, category={category} → {monthly_estimate}/month")
            return monthly_estimate
            
        except Exception as e:
            logger.error(f"Error estimating monthly sales: {e}")
            return 0
    
    def estimate_quarterly_sales(self, sales_drops_90: int, bsr: int, category: str = 'Unknown') -> int:
        """Estimation des ventes sur 90 jours"""
        try:
            # Similar logic but for 90-day period
            base_estimate = sales_drops_90 * self._get_category_multiplier(category) * 0.9  # Slight discount for longer period
            
            # BSR adjustments
            if bsr > 0:
                if bsr < 10000: base_estimate *= 1.4
                elif bsr < 50000: base_estimate *= 1.1  
                elif bsr > 500000: base_estimate *= 0.8
                elif bsr > 1000000: base_estimate *= 0.5
            
            quarterly_estimate = max(0, int(base_estimate))
            quarterly_estimate = min(quarterly_estimate, 3000)  # Cap at 3000/quarter
            
            return quarterly_estimate
            
        except Exception as e:
            logger.error(f"Error estimating quarterly sales: {e}")
            return 0
    
    def classify_velocity_tier(self, monthly_sales: int) -> str:
        """
        Classifier la vélocité en tiers intelligents
        
        Returns:
            PREMIUM, HIGH, MEDIUM, LOW, or DEAD
        """
        try:
            for tier, threshold in self.tier_thresholds.items():
                if monthly_sales >= threshold:
                    return tier
            return 'DEAD'
            
        except Exception as e:
            logger.error(f"Error classifying velocity tier: {e}")
            return 'UNKNOWN'
    
    def get_tier_description(self, tier: str) -> Dict[str, str]:
        """Get user-friendly description of velocity tier"""
        descriptions = {
            'PREMIUM': {
                'label': 'Cashflow Machine',
                'description': '100+ sales/month - Aggressive buying recommended',
                'strategy': 'Buy 10-20 units if profitable',
                'icon': '[PREMIUM]'
            },
            'HIGH': {
                'label': 'Strong Velocity',
                'description': '50-99 sales/month - Excellent turnover',
                'strategy': 'Buy 5-10 units safely',
                'icon': '[HIGH]'
            },
            'MEDIUM': {
                'label': 'Decent Turnover',
                'description': '20-49 sales/month - Reliable movement',
                'strategy': 'Buy 2-5 units standard',
                'icon': '[MEDIUM]'
            },
            'LOW': {
                'label': 'Slow Mover',
                'description': '5-19 sales/month - Limited demand',
                'strategy': 'Buy 1-2 units maximum',
                'icon': '[LOW]'
            },
            'DEAD': {
                'label': 'Avoid',
                'description': '0-4 sales/month - Money trap',
                'strategy': 'Skip this opportunity',
                'icon': '[AVOID]'
            }
        }
        
        return descriptions.get(tier, {
            'label': 'Unknown',
            'description': 'Insufficient data',
            'strategy': 'Analyze manually',
            'icon': '❓'
        })
    
    def calculate_opportunity_score(self, roi_percent: float, profit_net: float, monthly_sales: int) -> float:
        """
        Calculer le score d'opportunité composite
        
        Formule: (ROI/100) × √Sales × Profit × Weights
        """
        try:
            if roi_percent <= 0 or profit_net <= 0:
                return 0.0
            
            # Base calculation
            roi_factor = (roi_percent / 100) * self.scoring_config['roi_weight']
            velocity_factor = math.sqrt(max(monthly_sales, 1)) * self.scoring_config['velocity_weight']
            profit_factor = profit_net * self.scoring_config['profit_weight']
            
            opportunity_score = roi_factor * velocity_factor * profit_factor
            
            # Round to 1 decimal
            return round(opportunity_score, 1)
            
        except Exception as e:
            logger.error(f"Error calculating opportunity score: {e}")
            return 0.0
    
    def get_opportunity_grade(self, score: float) -> str:
        """Convert opportunity score to letter grade"""
        if score >= 80: return 'A+'
        elif score >= 60: return 'A'
        elif score >= 45: return 'B+'
        elif score >= 30: return 'B'
        elif score >= 20: return 'C+'
        elif score >= 10: return 'C'
        else: return 'D'
    
    def analyze_product_velocity(self, velocity_data: Dict[str, Any], roi_percent: float = 0, profit_net: float = 0) -> Dict[str, Any]:
        """
        Analyse complète de la vélocité d'un produit
        
        Returns:
            Dictionnaire avec toutes les métriques velocity
        """
        try:
            # Extract data
            asin = velocity_data.get('asin', 'Unknown')
            sales_drops_30 = velocity_data.get('sales_drops_30', 0)
            sales_drops_90 = velocity_data.get('sales_drops_90', 0)
            bsr = velocity_data.get('current_bsr', 0)
            category = velocity_data.get('category', 'Unknown')
            
            # Calculate estimates
            monthly_sales = self.estimate_monthly_sales(sales_drops_30, bsr, category)
            quarterly_sales = self.estimate_quarterly_sales(sales_drops_90, bsr, category)
            
            # Classification
            velocity_tier = self.classify_velocity_tier(monthly_sales)
            tier_info = self.get_tier_description(velocity_tier)
            
            # Opportunity scoring
            opportunity_score = self.calculate_opportunity_score(roi_percent, profit_net, monthly_sales)
            opportunity_grade = self.get_opportunity_grade(opportunity_score)
            
            return {
                "asin": asin,
                "sales_estimate_30d": monthly_sales,
                "sales_estimate_90d": quarterly_sales,
                "velocity_tier": velocity_tier,
                "velocity_tier_info": tier_info,
                "opportunity_score": opportunity_score,
                "opportunity_grade": opportunity_grade,
                "cashflow_potential": monthly_sales * profit_net if profit_net > 0 else 0,
                "analysis_metadata": {
                    "sales_drops_30": sales_drops_30,
                    "sales_drops_90": sales_drops_90,
                    "current_bsr": bsr,
                    "category": category,
                    "analyzed_at": datetime.utcnow().isoformat() + "Z"
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing product velocity: {e}")
            return self._create_empty_velocity_analysis(velocity_data.get('asin', 'Unknown'))
    
    def _get_category_multiplier(self, category: str) -> float:
        """Get category-specific multiplier for sales estimation"""
        return self.category_multipliers.get(category, 1.0)
    
    def _create_empty_velocity_analysis(self, asin: str) -> Dict[str, Any]:
        """Create empty velocity analysis structure"""
        return {
            "asin": asin,
            "sales_estimate_30d": 0,
            "sales_estimate_90d": 0,
            "velocity_tier": "UNKNOWN",
            "velocity_tier_info": self.get_tier_description("DEAD"),
            "opportunity_score": 0.0,
            "opportunity_grade": "D",
            "cashflow_potential": 0,
            "analysis_metadata": {
                "error": "Insufficient data for analysis",
                "analyzed_at": datetime.utcnow().isoformat() + "Z"
            }
        }


    # === WRAPPER METHODS FOR BACKWARD COMPATIBILITY ===
    
    def calculate_velocity_score(self, keepa_data: Dict[str, Any]) -> float:
        """
        Wrapper method for backward compatibility.
        Returns normalized velocity score (0.0 to 1.0) based on Keepa data.
        """
        try:
            # Extract relevant data
            sales_drops_30 = keepa_data.get('salesRankDrops30', 0)
            current_bsr = keepa_data.get('current', {}).get('BUY_BOX', [0])
            bsr_value = current_bsr[0] if current_bsr else 999999
            
            # Estimate monthly sales
            monthly_sales = self.estimate_monthly_sales(sales_drops_30, bsr_value, 'Books')
            
            # Normalize to 0-1 scale based on tier thresholds
            if monthly_sales >= self.tier_thresholds['PREMIUM']:
                return 1.0
            elif monthly_sales >= self.tier_thresholds['HIGH']:
                return 0.8
            elif monthly_sales >= self.tier_thresholds['MEDIUM']:
                return 0.6
            elif monthly_sales >= self.tier_thresholds['LOW']:
                return 0.4
            else:
                return 0.2
                
        except Exception as e:
            logger.error(f"Error calculating velocity score: {e}")
            return 0.0


# FastAPI dependency
async def get_sales_velocity_service() -> SalesVelocityService:
    """FastAPI dependency to get SalesVelocityService instance"""
    return SalesVelocityService()