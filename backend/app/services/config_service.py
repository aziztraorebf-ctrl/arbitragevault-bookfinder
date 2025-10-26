"""
Configuration service for managing dynamic business parameters.

This service handles configuration CRUD operations, category overrides,
and provides effective configuration calculation for specific contexts.
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import uuid4
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.config import Configuration, CategoryOverride
from app.schemas.config import (
    ConfigCreate, ConfigUpdate, ConfigResponse, EffectiveConfig,
    FeeConfig, ROIConfig, VelocityConfig, CategoryConfig,
    DataQualityThresholds, ProductFinderConfig
)
from app.core.exceptions import NotFoundError, ConflictError


class ConfigService:
    """Service for managing business configuration."""

    def __init__(self, db: Session):
        """Initialize configuration service."""
        self.db = db

    def create_configuration(self, config_data: ConfigCreate) -> ConfigResponse:
        """
        Create a new configuration.

        Args:
            config_data: Configuration creation data

        Returns:
            Created configuration

        Raises:
            ConflictError: If configuration name already exists
        """
        # Check if name already exists
        existing = self.db.query(Configuration).filter(
            Configuration.name == config_data.name
        ).first()

        if existing:
            raise ConflictError(f"Configuration '{config_data.name}' already exists")

        # If this is set as active, deactivate others
        if config_data.is_active:
            self._deactivate_all_configs()

        # Create configuration
        config = Configuration(
            id=str(uuid4()),
            name=config_data.name,
            description=config_data.description,
            fees=config_data.fees.model_dump(),
            roi=config_data.roi.model_dump(),
            velocity=config_data.velocity.model_dump(),
            data_quality=config_data.data_quality.model_dump(),
            product_finder=config_data.product_finder.model_dump(),
            is_active=config_data.is_active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Add category overrides
        for override in config_data.category_overrides:
            category_override = CategoryOverride(
                id=str(uuid4()),
                config_id=config.id,
                category_id=override.category_id,
                category_name=override.category_name,
                fees=override.fees.model_dump() if override.fees else None,
                roi=override.roi.model_dump() if override.roi else None,
                velocity=override.velocity.model_dump() if override.velocity else None
            )
            config.category_overrides.append(category_override)

        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)

        return self._to_response(config)

    def get_configuration(self, config_id: str) -> ConfigResponse:
        """
        Get configuration by ID.

        Args:
            config_id: Configuration ID

        Returns:
            Configuration details

        Raises:
            NotFoundError: If configuration not found
        """
        config = self.db.query(Configuration).filter(
            Configuration.id == config_id
        ).first()

        if not config:
            raise NotFoundError(f"Configuration '{config_id}' not found")

        return self._to_response(config)

    def get_active_configuration(self) -> ConfigResponse:
        """
        Get the currently active configuration.

        Returns:
            Active configuration

        Raises:
            NotFoundError: If no active configuration exists
        """
        config = self.db.query(Configuration).filter(
            Configuration.is_active == True
        ).first()

        if not config:
            # Create default configuration if none exists
            return self.create_default_configuration()

        return self._to_response(config)

    def update_configuration(
        self,
        config_id: str,
        update_data: ConfigUpdate
    ) -> ConfigResponse:
        """
        Update an existing configuration.

        Args:
            config_id: Configuration ID
            update_data: Update data

        Returns:
            Updated configuration

        Raises:
            NotFoundError: If configuration not found
        """
        config = self.db.query(Configuration).filter(
            Configuration.id == config_id
        ).first()

        if not config:
            raise NotFoundError(f"Configuration '{config_id}' not found")

        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)

        if 'is_active' in update_dict and update_dict['is_active']:
            self._deactivate_all_configs()

        for field, value in update_dict.items():
            if field == 'category_overrides':
                # Handle category overrides separately
                self._update_category_overrides(config, value)
            elif value is not None:
                setattr(config, field, value)

        config.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(config)

        return self._to_response(config)

    def delete_configuration(self, config_id: str) -> None:
        """
        Delete a configuration.

        Args:
            config_id: Configuration ID

        Raises:
            NotFoundError: If configuration not found
            ConflictError: If trying to delete active configuration
        """
        config = self.db.query(Configuration).filter(
            Configuration.id == config_id
        ).first()

        if not config:
            raise NotFoundError(f"Configuration '{config_id}' not found")

        if config.is_active:
            raise ConflictError("Cannot delete active configuration")

        self.db.delete(config)
        self.db.commit()

    def list_configurations(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[ConfigResponse]:
        """
        List all configurations.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of configurations
        """
        configs = self.db.query(Configuration).offset(skip).limit(limit).all()
        return [self._to_response(config) for config in configs]

    def get_effective_config(
        self,
        category_id: Optional[int] = None,
        config_id: Optional[str] = None
    ) -> EffectiveConfig:
        """
        Get effective configuration for a specific context.

        This applies category overrides to the base configuration.

        Args:
            category_id: Optional category ID for overrides
            config_id: Optional specific config ID (uses active if not provided)

        Returns:
            Effective configuration with overrides applied
        """
        # Get base configuration
        if config_id:
            base_config = self.get_configuration(config_id)
        else:
            base_config = self.get_active_configuration()

        # Start with base values
        effective_fees = FeeConfig(**base_config.fees.model_dump())
        effective_roi = ROIConfig(**base_config.roi.model_dump())
        effective_velocity = VelocityConfig(**base_config.velocity.model_dump())
        applied_overrides = []

        # Apply category overrides if category specified
        if category_id:
            for override in base_config.category_overrides:
                if override.category_id == category_id:
                    if override.fees:
                        effective_fees = FeeConfig(**override.fees.model_dump())
                        applied_overrides.append("fees")
                    if override.roi:
                        effective_roi = ROIConfig(**override.roi.model_dump())
                        applied_overrides.append("roi")
                    if override.velocity:
                        effective_velocity = VelocityConfig(**override.velocity.model_dump())
                        applied_overrides.append("velocity")
                    break

        return EffectiveConfig(
            base_config=base_config,
            category_id=category_id,
            effective_fees=effective_fees,
            effective_roi=effective_roi,
            effective_velocity=effective_velocity,
            applied_overrides=applied_overrides
        )

    def create_default_configuration(self) -> ConfigResponse:
        """
        Create a default configuration if none exists.

        Returns:
            Default configuration
        """
        default_config = ConfigCreate(
            name="Default Configuration",
            description="Auto-generated default configuration",
            is_active=True
        )

        return self.create_configuration(default_config)

    def _deactivate_all_configs(self) -> None:
        """Deactivate all configurations."""
        self.db.query(Configuration).update({'is_active': False})

    def _update_category_overrides(
        self,
        config: Configuration,
        overrides: List[Dict]
    ) -> None:
        """Update category overrides for a configuration."""
        # Delete existing overrides
        self.db.query(CategoryOverride).filter(
            CategoryOverride.config_id == config.id
        ).delete()

        # Add new overrides
        for override_data in overrides:
            override = CategoryOverride(
                id=str(uuid4()),
                config_id=config.id,
                category_id=override_data['category_id'],
                category_name=override_data['category_name'],
                fees=override_data.get('fees'),
                roi=override_data.get('roi'),
                velocity=override_data.get('velocity')
            )
            self.db.add(override)

    def _to_response(self, config: Configuration) -> ConfigResponse:
        """Convert ORM model to response schema."""
        # Parse category overrides
        category_overrides = []
        for override in config.category_overrides:
            category_config = CategoryConfig(
                category_id=override.category_id,
                category_name=override.category_name,
                fees=FeeConfig(**override.fees) if override.fees else None,
                roi=ROIConfig(**override.roi) if override.roi else None,
                velocity=VelocityConfig(**override.velocity) if override.velocity else None
            )
            category_overrides.append(category_config)

        return ConfigResponse(
            id=config.id,
            name=config.name,
            description=config.description,
            fees=FeeConfig(**config.fees),
            roi=ROIConfig(**config.roi),
            velocity=VelocityConfig(**config.velocity),
            data_quality=DataQualityThresholds(**config.data_quality),
            product_finder=ProductFinderConfig(**config.product_finder),
            category_overrides=category_overrides,
            is_active=config.is_active,
            created_at=config.created_at,
            updated_at=config.updated_at
        )