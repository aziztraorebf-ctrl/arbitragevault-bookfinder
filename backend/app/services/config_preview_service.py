"""
Configuration Preview Service - Dry-run testing with demo ASINs.
"""

import asyncio
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

from app.services.business_config_service import get_business_config_service
from app.services.keepa_service import KeepaService
from app.core.calculations import calculate_roi_metrics, calculate_velocity_score, VelocityData
from app.services.keepa_parser_v2 import parse_keepa_product
from app.services.keepa_parser import create_velocity_data_from_keepa


logger = logging.getLogger(__name__)


class ConfigPreviewService:
    """
    Service for previewing configuration changes with demo ASINs.
    
    Provides dry-run functionality to test config changes before applying them.
    """
    
    def __init__(self, keepa_service: Optional[KeepaService] = None):
        self.config_service = get_business_config_service()
        self.keepa_service = keepa_service
        
        # Mock data for demo ASINs (fallback if Keepa unavailable)
        self._demo_data = {
            "B00FLIJJSA": {
                "title": "The Mirrored Heavens (Sample Book)",
                "current_price": Decimal("24.99"),
                "estimated_buy_cost": Decimal("15.00"),
                "category": "books",
                "weight_lbs": Decimal("1.2"),
                "mock_velocity_data": {
                    "current_bsr": 45000,
                    "velocity_score": 65.0,
                    "rank_improvements": 5
                }
            },
            "B08N5WRWNW": {
                "title": "Technical Manual Example",
                "current_price": Decimal("89.99"),
                "estimated_buy_cost": Decimal("45.00"),
                "category": "books",
                "weight_lbs": Decimal("2.1"),
                "mock_velocity_data": {
                    "current_bsr": 25000,
                    "velocity_score": 78.0,
                    "rank_improvements": 8
                }
            },
            "B07FNW9FGJ": {
                "title": "Popular Fiction Novel",
                "current_price": Decimal("16.99"),
                "estimated_buy_cost": Decimal("8.50"),
                "category": "books",
                "weight_lbs": Decimal("0.8"),
                "mock_velocity_data": {
                    "current_bsr": 15000,
                    "velocity_score": 85.0,
                    "rank_improvements": 12
                }
            }
        }
    
    async def preview_config_impact(
        self,
        config_patch: Dict[str, Any],
        domain_id: int = 1,
        category: str = "books"
    ) -> List[Dict[str, Any]]:
        """
        Preview the impact of configuration changes on demo ASINs.
        
        Args:
            config_patch: Configuration changes to preview
            domain_id: Domain context for preview
            category: Category context for preview
            
        Returns:
            List of preview results for each demo ASIN
        """
        logger.info(f"Starting config preview for domain={domain_id}, category={category}")
        
        try:
            # Get current effective config
            current_config = await self.config_service.get_effective_config(domain_id, category)
            
            # Simulate new config by merging patch
            new_config = self.config_service._deep_merge_configs([current_config, config_patch])
            
            # Get demo ASINs from current config
            demo_asins = current_config.get("demo_asins", ["B00FLIJJSA", "B08N5WRWNW", "B07FNW9FGJ"])
            
            # Preview each demo ASIN
            preview_results = []
            for asin in demo_asins:
                try:
                    result = await self._preview_single_asin(asin, current_config, new_config, domain_id, category)
                    preview_results.append(result)
                except Exception as e:
                    logger.warning(f"Preview failed for ASIN {asin}: {e}")
                    # Add error result
                    preview_results.append({
                        "asin": asin,
                        "title": f"Preview Error - {asin}",
                        "before": {},
                        "after": {},
                        "changes": {"error": str(e)},
                        "status": "error"
                    })
            
            logger.info(f"Config preview completed: {len(preview_results)} results")
            return preview_results
            
        except Exception as e:
            logger.error(f"Config preview failed: {e}")
            raise
    
    async def _preview_single_asin(
        self,
        asin: str,
        current_config: Dict[str, Any],
        new_config: Dict[str, Any],
        domain_id: int,
        category: str
    ) -> Dict[str, Any]:
        """Preview impact for a single ASIN."""
        
        # Get demo data (mock or real)
        demo_data = await self._get_demo_data(asin)
        
        # Calculate metrics with current config
        current_metrics = await self._calculate_metrics_with_config(demo_data, current_config)
        
        # Calculate metrics with new config
        new_metrics = await self._calculate_metrics_with_config(demo_data, new_config)
        
        # Generate change summary
        changes = self._generate_change_summary(current_metrics, new_metrics)
        
        return {
            "asin": asin,
            "title": demo_data.get("title", f"Product {asin}"),
            "before": current_metrics,
            "after": new_metrics,
            "changes": changes,
            "status": "success"
        }
    
    async def _get_demo_data(self, asin: str) -> Dict[str, Any]:
        """Get demo data for an ASIN (real or mock)."""
        
        # Try real Keepa data first if service available
        if self.keepa_service:
            try:
                async with self.keepa_service:
                    product_data = await self.keepa_service.get_product_data(asin)
                    if product_data:
                        parsed_data = parse_keepa_product(product_data)
                        
                        # Convert to format expected by calculations
                        return {
                            "title": parsed_data.get("title", f"Product {asin}"),
                            "current_price": Decimal(str(parsed_data.get("current_buybox_price", 25.0))),
                            "estimated_buy_cost": Decimal(str(float(parsed_data.get("current_buybox_price", 25.0)) * 0.6)),  # Estimate 60% of selling price
                            "category": parsed_data.get("category", "books"),
                            "weight_lbs": Decimal("1.0"),  # Default weight
                            "velocity_data": create_velocity_data_from_keepa(parsed_data)
                        }
            except Exception as e:
                logger.debug(f"Real data unavailable for {asin}: {e}")
        
        # Fallback to mock data
        mock_data = self._demo_data.get(asin)
        if not mock_data:
            # Generate default mock data
            mock_data = {
                "title": f"Demo Product {asin}",
                "current_price": Decimal("25.00"),
                "estimated_buy_cost": Decimal("15.00"),
                "category": "books",
                "weight_lbs": Decimal("1.0"),
                "mock_velocity_data": {
                    "current_bsr": 50000,
                    "velocity_score": 60.0,
                    "rank_improvements": 3
                }
            }
        
        return mock_data
    
    async def _calculate_metrics_with_config(
        self, 
        demo_data: Dict[str, Any], 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate metrics using specific configuration."""
        
        # Extract demo data
        current_price = demo_data["current_price"]
        buy_cost = demo_data["estimated_buy_cost"]
        category = demo_data.get("category", "books")
        weight_lbs = demo_data.get("weight_lbs", Decimal("1.0"))
        
        # Calculate ROI with config parameters
        roi_metrics = self._calculate_roi_with_config(
            current_price, buy_cost, weight_lbs, category, config
        )
        
        # Calculate velocity with config parameters
        velocity_metrics = self._calculate_velocity_with_config(demo_data, config)
        
        # Calculate combined score with config weights
        combined_score = self._calculate_combined_score_with_config(roi_metrics, velocity_metrics, config)
        
        # Generate recommendation with config rules
        recommendation = self._generate_recommendation_with_config(roi_metrics, velocity_metrics, config)
        
        return {
            "roi_percentage": float(roi_metrics.get("roi_percentage", 0)),
            "net_profit": float(roi_metrics.get("net_profit", 0)),
            "target_buy_price": float(roi_metrics.get("target_buy_price", 0)),
            "meets_target_roi": roi_metrics.get("meets_target_roi", False),
            "profit_tier": roi_metrics.get("profit_tier", "unknown"),
            
            "velocity_score": velocity_metrics.get("velocity_score", 0),
            "velocity_tier": velocity_metrics.get("velocity_tier", "unknown"),
            
            "combined_score": combined_score,
            "recommendation": recommendation,
            
            "config_audit": {
                "roi_target_pct": config.get("roi", {}).get("target_pct_default", 30.0),
                "roi_weight": config.get("combined_score", {}).get("roi_weight", 0.6),
                "velocity_weight": config.get("combined_score", {}).get("velocity_weight", 0.4),
                "buffer_pct": config.get("fees", {}).get("buffer_pct_default", 5.0)
            }
        }
    
    def _calculate_roi_with_config(
        self, 
        current_price: Decimal,
        buy_cost: Decimal,
        weight_lbs: Decimal,
        category: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate ROI metrics with specific config."""
        
        # Get config parameters
        roi_config = config.get("roi", {})
        fees_config = config.get("fees", {})
        
        target_roi = roi_config.get("target_pct_default", 30.0)
        buffer_pct = fees_config.get("buffer_pct_default", 5.0)
        
        # Use standard ROI calculation but apply config parameters
        from app.core.fees_config import calculate_profit_metrics
        
        metrics = calculate_profit_metrics(
            sell_price=current_price,
            buy_cost=buy_cost,
            weight_lbs=weight_lbs,
            category=category,
            buffer_pct=Decimal(str(buffer_pct))
        )
        
        # Apply config-specific business logic
        roi_pct = float(metrics.get("roi_percentage", 0))
        meets_target = roi_pct >= target_roi
        
        # Determine profit tier using config thresholds
        profit_tier = self._get_profit_tier_with_config(roi_pct, roi_config)
        
        metrics.update({
            "meets_target_roi": meets_target,
            "profit_tier": profit_tier,
            "target_roi_used": target_roi
        })
        
        return metrics
    
    def _calculate_velocity_with_config(self, demo_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate velocity metrics with specific config."""
        
        velocity_config = config.get("velocity", {})
        
        # Use mock velocity data for demo
        mock_velocity = demo_data.get("mock_velocity_data", {})
        velocity_score = mock_velocity.get("velocity_score", 60.0)
        
        # Apply config thresholds
        velocity_tier = self._get_velocity_tier_with_config(velocity_score, velocity_config)
        
        return {
            "velocity_score": velocity_score,
            "velocity_tier": velocity_tier,
            "rank_improvements": mock_velocity.get("rank_improvements", 3),
            "current_bsr": mock_velocity.get("current_bsr", 50000)
        }
    
    def _calculate_combined_score_with_config(
        self, 
        roi_metrics: Dict[str, Any], 
        velocity_metrics: Dict[str, Any],
        config: Dict[str, Any]
    ) -> float:
        """Calculate combined score with config weights."""
        
        combined_config = config.get("combined_score", {})
        roi_weight = combined_config.get("roi_weight", 0.6)
        velocity_weight = combined_config.get("velocity_weight", 0.4)
        
        roi_score = min(max(float(roi_metrics.get("roi_percentage", 0)), 0), 100)
        velocity_score = float(velocity_metrics.get("velocity_score", 0))
        
        combined_score = (roi_score * roi_weight) + (velocity_score * velocity_weight)
        return round(combined_score, 2)
    
    def _generate_recommendation_with_config(
        self,
        roi_metrics: Dict[str, Any],
        velocity_metrics: Dict[str, Any], 
        config: Dict[str, Any]
    ) -> str:
        """Generate recommendation using config rules."""
        
        roi_pct = float(roi_metrics.get("roi_percentage", 0))
        velocity_score = float(velocity_metrics.get("velocity_score", 0))
        is_profitable = roi_metrics.get("is_profitable", False)
        
        if not is_profitable:
            return "PASS - Not profitable"
        
        # Use config recommendation rules
        rules = config.get("recommendation_rules", [])
        
        for rule in rules:
            min_roi = rule.get("min_roi", 0)
            min_velocity = rule.get("min_velocity", 0)
            
            if roi_pct >= min_roi and velocity_score >= min_velocity:
                label = rule.get("label", "UNKNOWN")
                description = rule.get("description", "")
                return f"{label} - {description}" if description else label
        
        return "PASS - Below thresholds"
    
    def _get_profit_tier_with_config(self, roi_pct: float, roi_config: Dict[str, Any]) -> str:
        """Determine profit tier using config thresholds."""
        excellent = roi_config.get("excellent_threshold", 50.0)
        good = roi_config.get("good_threshold", 30.0)
        fair = roi_config.get("fair_threshold", 15.0)
        
        if roi_pct >= excellent:
            return "excellent"
        elif roi_pct >= good:
            return "good"
        elif roi_pct >= fair:
            return "fair"
        elif roi_pct > 0:
            return "poor"
        else:
            return "loss"
    
    def _get_velocity_tier_with_config(self, velocity_score: float, velocity_config: Dict[str, Any]) -> str:
        """Determine velocity tier using config thresholds."""
        fast = velocity_config.get("fast_threshold", 80.0)
        medium = velocity_config.get("medium_threshold", 60.0)
        slow = velocity_config.get("slow_threshold", 40.0)
        
        if velocity_score >= fast:
            return "fast"
        elif velocity_score >= medium:
            return "medium"
        elif velocity_score >= slow:
            return "slow"
        else:
            return "very_slow"
    
    def _generate_change_summary(self, before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of key changes between before/after metrics."""
        
        changes = {}
        
        # ROI changes
        roi_before = before.get("roi_percentage", 0)
        roi_after = after.get("roi_percentage", 0)
        if abs(roi_before - roi_after) > 0.01:
            changes["roi_percentage"] = {
                "before": roi_before,
                "after": roi_after,
                "change": round(roi_after - roi_before, 2)
            }
        
        # Recommendation changes
        rec_before = before.get("recommendation", "")
        rec_after = after.get("recommendation", "")
        if rec_before != rec_after:
            changes["recommendation"] = {
                "before": rec_before,
                "after": rec_after
            }
        
        # Combined score changes
        score_before = before.get("combined_score", 0)
        score_after = after.get("combined_score", 0)
        if abs(score_before - score_after) > 0.01:
            changes["combined_score"] = {
                "before": score_before,
                "after": score_after,
                "change": round(score_after - score_before, 2)
            }
        
        # Profit tier changes
        tier_before = before.get("profit_tier", "")
        tier_after = after.get("profit_tier", "")
        if tier_before != tier_after:
            changes["profit_tier"] = {
                "before": tier_before,
                "after": tier_after
            }
        
        return changes