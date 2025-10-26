"""
API endpoints for configuration management.

This module provides REST endpoints for managing business configuration,
including fees, ROI thresholds, velocity tiers, and category overrides.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.config_service import ConfigService
from app.schemas.config import (
    ConfigCreate,
    ConfigUpdate,
    ConfigResponse,
    EffectiveConfig
)
from app.core.exceptions import NotFoundError, ConflictError

router = APIRouter()


@router.post(
    "/",
    response_model=ConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new configuration",
    description="Create a new business configuration with fees, ROI, and velocity settings"
)
def create_configuration(
    config_data: ConfigCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new configuration.

    - **name**: Unique configuration name
    - **description**: Optional description
    - **fees**: Fee structure configuration
    - **roi**: ROI calculation parameters
    - **velocity**: Velocity scoring tiers
    - **data_quality**: Data quality thresholds
    - **product_finder**: Product Finder settings
    - **category_overrides**: Category-specific overrides
    - **is_active**: Set as active configuration
    """
    service = ConfigService(db)

    try:
        return service.create_configuration(config_data)
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create configuration: {str(e)}"
        )


@router.get(
    "/active",
    response_model=ConfigResponse,
    summary="Get active configuration",
    description="Retrieve the currently active configuration"
)
def get_active_configuration(
    db: Session = Depends(get_db)
):
    """
    Get the currently active configuration.

    Returns the active configuration or creates a default one if none exists.
    """
    service = ConfigService(db)

    try:
        return service.get_active_configuration()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve active configuration: {str(e)}"
        )


@router.get(
    "/effective",
    response_model=EffectiveConfig,
    summary="Get effective configuration",
    description="Get configuration with category overrides applied"
)
def get_effective_configuration(
    category_id: Optional[int] = Query(None, description="Category ID for overrides"),
    config_id: Optional[str] = Query(None, description="Specific config ID (uses active if not provided)"),
    db: Session = Depends(get_db)
):
    """
    Get effective configuration for a specific context.

    This endpoint returns the configuration with category-specific overrides applied.

    - **category_id**: Optional category to apply overrides for
    - **config_id**: Optional specific configuration (uses active if not provided)
    """
    service = ConfigService(db)

    try:
        return service.get_effective_config(
            category_id=category_id,
            config_id=config_id
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate effective configuration: {str(e)}"
        )


@router.get(
    "/",
    response_model=List[ConfigResponse],
    summary="List configurations",
    description="List all available configurations"
)
def list_configurations(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records"),
    db: Session = Depends(get_db)
):
    """
    List all configurations.

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    """
    service = ConfigService(db)

    try:
        return service.list_configurations(skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list configurations: {str(e)}"
        )


@router.get(
    "/{config_id}",
    response_model=ConfigResponse,
    summary="Get configuration by ID",
    description="Retrieve a specific configuration by its ID"
)
def get_configuration(
    config_id: str,
    db: Session = Depends(get_db)
):
    """
    Get configuration by ID.

    - **config_id**: Configuration unique identifier
    """
    service = ConfigService(db)

    try:
        return service.get_configuration(config_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve configuration: {str(e)}"
        )


@router.put(
    "/{config_id}",
    response_model=ConfigResponse,
    summary="Update configuration",
    description="Update an existing configuration"
)
def update_configuration(
    config_id: str,
    update_data: ConfigUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing configuration.

    - **config_id**: Configuration unique identifier
    - **update_data**: Fields to update (partial update supported)
    """
    service = ConfigService(db)

    try:
        return service.update_configuration(config_id, update_data)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}"
        )


@router.delete(
    "/{config_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete configuration",
    description="Delete a configuration (cannot delete active configuration)"
)
def delete_configuration(
    config_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a configuration.

    - **config_id**: Configuration unique identifier

    Note: Cannot delete the active configuration.
    """
    service = ConfigService(db)

    try:
        service.delete_configuration(config_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete configuration: {str(e)}"
        )


@router.post(
    "/{config_id}/activate",
    response_model=ConfigResponse,
    summary="Activate configuration",
    description="Set a configuration as active (deactivates others)"
)
def activate_configuration(
    config_id: str,
    db: Session = Depends(get_db)
):
    """
    Activate a configuration.

    This will deactivate all other configurations and set this one as active.

    - **config_id**: Configuration unique identifier
    """
    service = ConfigService(db)

    try:
        # Use update to activate
        update_data = ConfigUpdate(is_active=True)
        return service.update_configuration(config_id, update_data)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate configuration: {str(e)}"
        )