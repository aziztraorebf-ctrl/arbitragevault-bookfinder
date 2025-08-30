"""
Strategic Views Service - Wrapper around strategic views logic
Provides service-level interface for strategic analysis configurations
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pydantic import BaseModel
from .amazon_filter_service import AmazonFilterService

class TargetPriceResult(BaseModel):
    """Result of target price calculation."""
    target_price: float
    roi_target: float
    safety_buffer_used: float
    is_achievable: bool
    price_gap_percentage: float
    calculation_details: Dict[str, Any]

class TargetPriceCalculator:
    """Calculates target selling prices based on ROI targets and strategic views."""
    
    # ROI targets by strategic view (configurable in future)
    ROI_TARGETS = {
        "profit_hunter": 0.50,      # 50%
        "velocity": 0.25,           # 25%
        "cashflow_hunter": 0.35,    # 35%
        "balanced_score": 0.40,     # 40%
        "volume_player": 0.20       # 20%
    }
    
    # Default Amazon referral fees by category (fallback)
    DEFAULT_REFERRAL_RATES = {
        "Books": 0.15,              # 15%
        "Textbooks": 0.10,          # 10% 
        "default": 0.15             # 15% fallback
    }
    
    @classmethod
    def calculate_target_price(
        cls,
        buy_price: float,
        fba_fee: float,
        view_name: str,
        referral_fee_rate: Optional[float] = None,
        storage_fee: float = 0.0,
        safety_buffer: float = 0.06,  # 6% par défaut
        current_market_price: Optional[float] = None
    ) -> TargetPriceResult:
        """
        Calculate target selling price for given parameters.
        
        Args:
            buy_price: Cost to acquire the product
            fba_fee: Amazon FBA fulfillment fee
            view_name: Strategic view name (profit_hunter, velocity, etc.)
            referral_fee_rate: Amazon referral fee rate (optional, uses default if None)
            storage_fee: Amazon storage fee (optional)
            safety_buffer: Safety margin percentage (default 6%)
            current_market_price: Current market price for comparison
            
        Returns:
            TargetPriceResult with calculated target price and metadata
        """
        # Get ROI target for strategic view
        roi_target = cls.ROI_TARGETS.get(view_name, 0.30)  # 30% fallback
        
        # Use default referral fee if not provided
        if referral_fee_rate is None:
            referral_fee_rate = cls.DEFAULT_REFERRAL_RATES["default"]
        
        # Calculate total costs
        total_costs = buy_price + fba_fee + storage_fee
        
        # Calculate target price with safety buffer
        # Formula: target_price = total_costs / ((1 - referral_fee) × (1 - roi_target))
        net_rate = (1 - referral_fee_rate) * (1 - roi_target)
        base_target_price = total_costs / net_rate
        
        # Apply safety buffer
        target_price = base_target_price * (1 + safety_buffer)
        
        # Calculate if achievable (compared to current market price)
        is_achievable = True
        price_gap_percentage = 0.0
        
        if current_market_price:
            price_gap_percentage = ((target_price - current_market_price) / current_market_price) * 100
            is_achievable = target_price <= current_market_price * 1.05  # 5% tolerance
        
        # Calculation details for transparency
        calculation_details = {
            "buy_price": buy_price,
            "fba_fee": fba_fee,
            "storage_fee": storage_fee,
            "total_costs": total_costs,
            "referral_fee_rate": referral_fee_rate,
            "roi_target": roi_target,
            "net_rate": net_rate,
            "base_target_price": base_target_price,
            "safety_buffer_applied": safety_buffer,
            "current_market_price": current_market_price
        }
        
        return TargetPriceResult(
            target_price=round(target_price, 2),
            roi_target=roi_target,
            safety_buffer_used=safety_buffer,
            is_achievable=is_achievable,
            price_gap_percentage=round(price_gap_percentage, 2),
            calculation_details=calculation_details
        )

@dataclass
class ViewConfig:
    """Configuration for a strategic view."""
    view_name: str
    description: str
    roi_weight: float = 1.0
    velocity_weight: float = 1.0  
    profit_weight: float = 1.0
    competition_weight: float = 0.5
    risk_weight: float = 0.3

class StrategicViewsService:
    """Service for managing strategic analysis views and scoring."""
    
    def __init__(self):
        """Initialize with predefined strategic view configurations."""
        # Initialize Amazon Filter Service
        self.amazon_filter = AmazonFilterService()
        self.view_configs = {
            "profit_hunter": ViewConfig(
                view_name="profit_hunter",
                description="Maximize profit per transaction - Focus on high ROI opportunities",
                roi_weight=2.0,
                velocity_weight=0.5,
                profit_weight=2.0,
                competition_weight=0.3,
                risk_weight=0.4
            ),
            "velocity": ViewConfig(
                view_name="velocity",
                description="Maximize turnover speed - Focus on fast-moving inventory",
                roi_weight=0.7,
                velocity_weight=2.0,
                profit_weight=0.8,
                competition_weight=0.5,
                risk_weight=0.3
            ),
            "cashflow_hunter": ViewConfig(
                view_name="cashflow_hunter", 
                description="Balance profit and velocity - Steady cash generation",
                roi_weight=1.3,
                velocity_weight=1.3,
                profit_weight=1.2,
                competition_weight=0.4,
                risk_weight=0.5
            ),
            "balanced_score": ViewConfig(
                view_name="balanced_score",
                description="Equal weight approach - Balanced risk/reward",
                roi_weight=1.0,
                velocity_weight=1.0,
                profit_weight=1.0,
                competition_weight=1.0,
                risk_weight=1.0
            ),
            "volume_player": ViewConfig(
                view_name="volume_player",
                description="High volume, lower margins - Scale-focused approach",
                roi_weight=0.6,
                velocity_weight=1.8,
                profit_weight=0.4,
                competition_weight=0.2,
                risk_weight=0.2
            )
        }

    def get_view_config(self, view_name: str) -> Optional[ViewConfig]:
        """Get configuration for a specific strategic view."""
        return self.view_configs.get(view_name)

    def list_available_views(self) -> Dict[str, str]:
        """Get list of available strategic views with descriptions."""
        return {
            name: config.description 
            for name, config in self.view_configs.items()
        }

    def calculate_strategic_score(self, view_name: str, analysis_data: Dict[str, Any]) -> float:
        """
        Calculate strategic score for analysis data using specified view.
        
        Args:
            view_name: Name of strategic view to use
            analysis_data: Dictionary containing analysis metrics
            
        Returns:
            Strategic score (0.0 to 100.0)
        """
        config = self.get_view_config(view_name)
        if not config:
            raise ValueError(f"Unknown strategic view: {view_name}")
        
        # Extract metrics from analysis data
        roi = analysis_data.get("roi_percentage", 0.0)
        velocity = analysis_data.get("velocity_score", 0.0) 
        profit = analysis_data.get("profit_estimate", 0.0)
        competition = self._map_competition_level(analysis_data.get("competition_level", "UNKNOWN"))
        risk = self._calculate_risk_factor(analysis_data)
        
        # Normalize values to 0-1 scale
        roi_norm = min(roi / 100.0, 1.0)  # ROI as percentage
        velocity_norm = min(velocity, 1.0)  # Velocity score already 0-1
        profit_norm = min(profit / 50.0, 1.0)  # Normalize profit to $50 max
        competition_norm = competition
        risk_norm = 1.0 - risk  # Lower risk = higher score
        
        # Calculate weighted score
        weighted_score = (
            roi_norm * config.roi_weight +
            velocity_norm * config.velocity_weight +
            profit_norm * config.profit_weight +
            competition_norm * config.competition_weight +
            risk_norm * config.risk_weight
        )
        
        # Normalize to 0-100 scale
        total_weights = (
            config.roi_weight + config.velocity_weight + 
            config.profit_weight + config.competition_weight + config.risk_weight
        )
        
        strategic_score = (weighted_score / total_weights) * 100.0
        return min(strategic_score, 100.0)

    def _map_competition_level(self, competition_level: str) -> float:
        """Map competition level string to numeric score."""
        mapping = {
            "LOW": 0.8,
            "MEDIUM": 0.5, 
            "HIGH": 0.2,
            "UNKNOWN": 0.5
        }
        return mapping.get(competition_level.upper(), 0.5)

    def _calculate_risk_factor(self, analysis_data: Dict[str, Any]) -> float:
        """Calculate risk factor from analysis data."""
        # Simple risk calculation - can be enhanced
        price_volatility = analysis_data.get("price_volatility", 0.3)
        demand_consistency = analysis_data.get("demand_consistency", 0.7)
        data_confidence = analysis_data.get("data_confidence", 0.8)
        
        # Risk increases with volatility, decreases with consistency and confidence
        risk_factor = (price_volatility * 0.4 + (1 - demand_consistency) * 0.3 + (1 - data_confidence) * 0.3)
        return min(max(risk_factor, 0.0), 1.0)
    
    def calculate_target_price_for_view(self, view_name: str, product_data: Dict[str, Any]) -> Optional[TargetPriceResult]:
        """
        Calculate target price for a product using specific strategic view.
        
        Args:
            view_name: Strategic view name
            product_data: Product data dictionary with price and fee information
            
        Returns:
            TargetPriceResult or None if insufficient data
        """
        # Extract required data with fallbacks
        buy_price = product_data.get("buy_price") or product_data.get("current_price")
        fba_fee = product_data.get("fba_fee", 0.0)
        current_market_price = product_data.get("buybox_price")
        referral_fee_rate = product_data.get("referral_fee_rate")
        storage_fee = product_data.get("storage_fee", 0.0)
        
        if not buy_price:
            return None
        
        return TargetPriceCalculator.calculate_target_price(
            buy_price=buy_price,
            fba_fee=fba_fee,
            view_name=view_name,
            referral_fee_rate=referral_fee_rate,
            storage_fee=storage_fee,
            current_market_price=current_market_price
        )
    
    def enrich_analysis_with_target_price(self, view_name: str, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich analysis data with target price information.
        
        Args:
            view_name: Strategic view name  
            analysis_data: Analysis data to enrich
            
        Returns:
            Enriched analysis data with target_price_result
        """
        # Create a copy to avoid modifying original
        enriched_data = analysis_data.copy()
        
        # Calculate target price
        target_price_result = self.calculate_target_price_for_view(view_name, analysis_data)
        
        if target_price_result:
            enriched_data["target_price_result"] = target_price_result.dict()
            
            # Add convenience fields for UI
            enriched_data["target_price"] = target_price_result.target_price
            enriched_data["roi_target"] = target_price_result.roi_target
            enriched_data["price_achievable"] = target_price_result.is_achievable
        
        return enriched_data
    
    def get_strategic_view_with_target_prices(self, view_name: str, products_data: list[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get strategic view analysis enriched with target prices for all products.
        
        Args:
            view_name: Strategic view name
            products_data: List of product data dictionaries
            
        Returns:
            Strategic view results with target prices
        """
        # NOUVEAU : Filtrage Amazon avant analyse
        filter_result = self.amazon_filter.filter_amazon_products(products_data)
        filtered_products = filter_result['products']
        
        enriched_products = []
        
        for product_data in filtered_products:  # Utilisation des produits filtrés
            # Calculate strategic score
            strategic_score = self.calculate_strategic_score(view_name, product_data)
            
            # Enrich with target price
            enriched_product = self.enrich_analysis_with_target_price(view_name, product_data)
            enriched_product["strategic_score"] = strategic_score
            
            enriched_products.append(enriched_product)
        
        # Sort by strategic score (descending)
        enriched_products.sort(key=lambda x: x.get("strategic_score", 0), reverse=True)
        
        view_config = self.get_view_config(view_name)
        
        # Générer summary enrichi avec infos Amazon Filter
        summary = self._generate_view_summary(enriched_products)
        summary['amazon_filter'] = filter_result  # Transparence totale sur le filtrage
        
        return {
            "view_name": view_name,
            "description": view_config.description if view_config else "",
            "roi_target": TargetPriceCalculator.ROI_TARGETS.get(view_name, 0.30),
            "products_count": len(enriched_products),
            "products": enriched_products,
            "summary": summary
        }
    
    def _generate_view_summary(self, enriched_products: list[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics for a strategic view."""
        if not enriched_products:
            return {}
        
        # Calculate summary metrics
        achievable_count = sum(1 for p in enriched_products if p.get("price_achievable", False))
        avg_target_price = sum(p.get("target_price", 0) for p in enriched_products) / len(enriched_products)
        avg_strategic_score = sum(p.get("strategic_score", 0) for p in enriched_products) / len(enriched_products)
        
        total_potential_profit = sum(p.get("profit_estimate", 0) for p in enriched_products)
        
        return {
            "total_products": len(enriched_products),
            "achievable_opportunities": achievable_count,
            "achievable_percentage": (achievable_count / len(enriched_products)) * 100,
            "avg_target_price": round(avg_target_price, 2),
            "avg_strategic_score": round(avg_strategic_score, 2),
            "total_potential_profit": round(total_potential_profit, 2)
        }
        # Higher values = higher risk
        risk_factor = (
            price_volatility * 0.4 +
            (1.0 - demand_consistency) * 0.3 +
            (1.0 - data_confidence) * 0.3
        )
        
        return min(risk_factor, 1.0)

    def get_view_recommendation(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get view recommendation based on analysis characteristics."""
        scores = {}
        
        # Calculate scores for all views
        for view_name in self.view_configs.keys():
            scores[view_name] = self.calculate_strategic_score(view_name, analysis_data)
        
        # Find best view
        best_view = max(scores.keys(), key=lambda x: scores[x])
        best_score = scores[best_view]
        
        return {
            "recommended_view": best_view,
            "confidence_score": best_score,
            "all_scores": scores,
            "reasoning": self._generate_recommendation_reasoning(best_view, analysis_data)
        }

    def _generate_recommendation_reasoning(self, view_name: str, analysis_data: Dict[str, Any]) -> str:
        """Generate human-readable reasoning for view recommendation."""
        config = self.get_view_config(view_name)
        roi = analysis_data.get("roi_percentage", 0)
        velocity = analysis_data.get("velocity_score", 0)
        profit = analysis_data.get("profit_estimate", 0)
        
        if view_name == "profit_hunter":
            return f"High ROI ({roi:.1f}%) and profit (${profit:.2f}) make this ideal for profit-focused strategy."
        elif view_name == "velocity":
            return f"Strong velocity score ({velocity:.2f}) indicates fast turnover potential."
        elif view_name == "cashflow_hunter":
            return f"Balanced ROI ({roi:.1f}%) and velocity ({velocity:.2f}) provide steady cash flow."
        elif view_name == "balanced_score":
            return "Metrics are evenly distributed - balanced approach recommended."
        else:
            return f"Analysis suggests {config.description.lower()}"