"""
AutoSourcing cost estimation service.
Calculates Keepa API token costs before job execution.
"""
from typing import Dict, Any
from app.core.settings import Settings

class AutoSourcingCostEstimator:
    """Estimates token costs for AutoSourcing jobs."""

    def __init__(self, settings: Settings):
        """
        Initialize cost estimator with settings.

        Args:
            settings: Application settings with Keepa cost configuration
        """
        self.product_finder_cost = settings.keepa_product_finder_cost
        self.product_details_cost = settings.keepa_product_details_cost
        self.results_per_page = settings.keepa_results_per_page

    def estimate_discovery_cost(self, discovery_config: Dict[str, Any]) -> int:
        """
        Estimate token cost for Product Finder discovery phase.

        Args:
            discovery_config: Discovery configuration with categories and max_results

        Returns:
            Estimated tokens for discovery
        """
        categories = discovery_config.get("categories", [])
        max_results = discovery_config.get("max_results", 10)

        # Calculate pages needed per category
        pages_per_category = (max_results + self.results_per_page - 1) // self.results_per_page

        # Total cost = pages * categories * cost per page
        total_cost = pages_per_category * len(categories) * self.product_finder_cost

        return total_cost

    def estimate_analysis_cost(self, num_products: int) -> int:
        """
        Estimate token cost for product analysis phase.

        Args:
            num_products: Number of products to analyze

        Returns:
            Estimated tokens for analysis
        """
        return num_products * self.product_details_cost

    def estimate_total_job_cost(self, discovery_config: Dict[str, Any]) -> int:
        """
        Estimate total token cost for complete AutoSourcing job.

        Args:
            discovery_config: Discovery configuration

        Returns:
            Total estimated tokens (discovery + analysis)
        """
        max_results = discovery_config.get("max_results", 10)

        discovery_cost = self.estimate_discovery_cost(discovery_config)
        analysis_cost = self.estimate_analysis_cost(max_results)

        return discovery_cost + analysis_cost
