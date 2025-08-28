"""
Strategic Views Service - Wrapper around strategic views logic
Provides service-level interface for strategic analysis configurations
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass

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