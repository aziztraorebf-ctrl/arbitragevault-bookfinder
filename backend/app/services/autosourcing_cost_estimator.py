"""
AutoSourcing cost estimation service.
Calculates Keepa API token costs before job execution.
"""
from typing import Dict, Any

class AutoSourcingCostEstimator:
    """Estimates token costs for AutoSourcing jobs."""

    # Keepa API token costs
    PRODUCT_FINDER_COST = 10  # tokens per page
    PRODUCT_DETAILS_COST = 1  # tokens per ASIN
    RESULTS_PER_PAGE = 10     # Product Finder returns 10 results per page

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
        pages_per_category = (max_results + self.RESULTS_PER_PAGE - 1) // self.RESULTS_PER_PAGE

        # Total cost = pages * categories * cost per page
        total_cost = pages_per_category * len(categories) * self.PRODUCT_FINDER_COST

        return total_cost

    def estimate_analysis_cost(self, num_products: int) -> int:
        """
        Estimate token cost for product analysis phase.

        Args:
            num_products: Number of products to analyze

        Returns:
            Estimated tokens for analysis
        """
        return num_products * self.PRODUCT_DETAILS_COST

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
