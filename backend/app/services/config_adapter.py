"""
Adapter to bridge ConfigService interface to BusinessConfigService.

This allows legacy endpoints (niches, products) to use the modern
BusinessConfigService without code changes.
"""

import logging
import threading
from typing import Optional, Dict, Any
from dataclasses import dataclass

from app.services.business_config_service import get_business_config_service
from app.schemas.config_types import (
    ROIConfigUnified,
    FeeConfigUnified,
    VelocityConfigUnified,
    roi_schema_to_unified,
    fee_schema_to_unified,
    velocity_schema_to_unified,
)

logger = logging.getLogger(__name__)


# Mapping of Keepa category IDs to category names
CATEGORY_ID_MAP = {
    283155: "books",
}


@dataclass
class EffectiveConfigCompat:
    """Compatibility wrapper with unified config types."""
    base_config: Dict[str, Any]
    category_id: Optional[int]
    effective_fees: FeeConfigUnified
    effective_roi: ROIConfigUnified
    effective_velocity: VelocityConfigUnified
    applied_overrides: list


class ConfigServiceAdapter:
    """
    Adapter that provides ConfigService interface using BusinessConfigService.

    Usage:
        adapter = ConfigServiceAdapter()
        config = await adapter.get_effective_config(category_id=283155)
    """

    def __init__(self):
        self._service = get_business_config_service()

    async def get_effective_config(
        self,
        category_id: Optional[int] = None,
        config_id: Optional[str] = None,
        domain_id: int = 1
    ) -> EffectiveConfigCompat:
        """
        Get effective configuration, compatible with ConfigService interface.

        Args:
            category_id: Keepa category ID (mapped to category name)
            config_id: Ignored (for interface compatibility)
            domain_id: Keepa domain ID (default: 1=US)

        Returns:
            EffectiveConfigCompat with nested config sections
        """
        category_name = self._category_id_to_name(category_id) if category_id is not None else "books"

        config_dict = await self._service.get_effective_config(
            domain_id=domain_id,
            category=category_name
        )

        if config_dict is None:
            logger.warning("BusinessConfigService returned None, using empty defaults")
            config_dict = {}

        # Convert to unified types using the converter functions
        fees = fee_schema_to_unified(config_dict.get("fees", {}))
        roi = roi_schema_to_unified(config_dict.get("roi", {}))
        velocity = velocity_schema_to_unified(config_dict.get("velocity", {}))

        meta = config_dict.get("_meta", {})
        sources = meta.get("sources", {})
        # Extract applied overrides (exclude 'global' and False values)
        applied_overrides = [k for k, v in sources.items() if v and k != "global"]

        return EffectiveConfigCompat(
            base_config=config_dict,
            category_id=category_id,
            effective_fees=fees,
            effective_roi=roi,
            effective_velocity=velocity,
            applied_overrides=applied_overrides
        )

    def _category_id_to_name(self, category_id: int) -> str:
        """Map Keepa category ID to category name."""
        name = CATEGORY_ID_MAP.get(category_id)
        if name is None:
            logger.warning(f"Unknown Keepa category_id {category_id}, using 'default' config")
            return "default"
        return name


_adapter_instance = None
_adapter_lock = threading.Lock()


def get_config_adapter() -> ConfigServiceAdapter:
    """Get singleton adapter instance (thread-safe)."""
    global _adapter_instance
    if _adapter_instance is None:
        with _adapter_lock:
            if _adapter_instance is None:
                _adapter_instance = ConfigServiceAdapter()
    return _adapter_instance
