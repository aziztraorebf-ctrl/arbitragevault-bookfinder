"""
Keepa Token Cost Registry
Defines token costs for business actions to enable intelligent pre-execution control.
"""
from typing import TypedDict


class ActionCost(TypedDict):
    """Token cost specification for a business action."""
    cost: int
    description: str
    endpoint_type: str  # "single", "composite", "batch"


# Token costs for business-level actions
TOKEN_COSTS: dict[str, ActionCost] = {
    "surprise_me": {
        "cost": 50,
        "description": "Generate random niche via bestsellers",
        "endpoint_type": "single"
    },
    "niche_discovery": {
        "cost": 150,
        "description": "Discover 3 niches (3x bestsellers)",
        "endpoint_type": "composite"
    },
    "manual_search": {
        "cost": 10,
        "description": "Manual product search with filters",
        "endpoint_type": "single"
    },
    "product_lookup": {
        "cost": 1,
        "description": "Single ASIN analysis",
        "endpoint_type": "single"
    },
    "auto_sourcing_job": {
        "cost": 200,
        "description": "Full AutoSourcing discovery run",
        "endpoint_type": "batch"
    },
}

# Balance thresholds
CRITICAL_THRESHOLD = 20
WARNING_THRESHOLD = 100
SAFE_THRESHOLD = 200
