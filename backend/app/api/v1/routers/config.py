"""
Business Configuration API endpoints.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Header, Depends
from pydantic import ValidationError
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db_session
from app.models.business_config import BusinessConfig
from app.schemas.business_config_schemas import (
    BusinessConfigResponse,
    ConfigUpdateRequest, 
    ConfigPreviewRequest,
    ConfigPreviewResponse,
    ConfigChangeResponse,
    ConfigStatsResponse,
    ConfigErrorResponse,
    ValidationErrorResponse
)
from app.services.business_config_service import get_business_config_service, BusinessConfigService
from app.services.config_preview_service import ConfigPreviewService
import logging

router = APIRouter(prefix="/config", tags=["Configuration"])
logger = logging.getLogger(__name__)


def get_config_service() -> BusinessConfigService:
    """Dependency to get business config service."""
    return get_business_config_service()


@router.get("/", response_model=BusinessConfigResponse)
async def get_effective_config(
    domain_id: int = Query(1, description="Keepa domain ID (1=US, 2=UK, etc.)"),
    category: str = Query("books", description="Product category for config context"),
    force_refresh: bool = Query(False, description="Force refresh from database"),
    config_service: BusinessConfigService = Depends(get_config_service)
):
    """
    Get effective business configuration with hierarchical merging.
    
    Returns merged configuration: global < domain < category
    """
    try:
        effective_config = await config_service.get_effective_config(
            domain_id=domain_id,
            category=category,
            force_refresh=force_refresh
        )
        
        # Extract metadata
        meta = effective_config.get("_meta", {})
        sources = meta.get("sources", {})
        
        return BusinessConfigResponse(
            scope=f"effective:domain:{domain_id}:category:{category}",
            config=effective_config,
            version=1,  # Effective configs don't have versions
            effective_config=effective_config,
            sources=sources,
            updated_at=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Failed to get effective config: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve configuration: {str(e)}"
        )


@router.put("/", response_model=BusinessConfigResponse)
async def update_config(
    request: ConfigUpdateRequest,
    scope: str = Query("global", description="Configuration scope to update"),
    changed_by: str = Query("api_user", description="User making the change"),
    if_match: Optional[str] = Header(None, description="Expected version for optimistic locking"),
    config_service: BusinessConfigService = Depends(get_config_service)
):
    """
    Update business configuration with optimistic concurrency control.
    
    Supports partial updates (patches) and version checking.
    """
    try:
        # Parse If-Match header
        if_match_version = None
        if if_match:
            try:
                if_match_version = int(if_match.strip('"'))
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid If-Match header format. Expected integer version."
                )
        
        # Convert pydantic model to dict for service
        config_patch = request.config_patch.dict(exclude_unset=True, exclude_none=True)
        
        # Update configuration
        updated_config, change_record = await config_service.update_config(
            scope=scope,
            config_patch=config_patch,
            changed_by=changed_by,
            if_match_version=if_match_version,
            change_reason=request.change_reason
        )
        
        logger.info(f"Configuration updated: scope={scope}, version={updated_config.version}")
        
        return BusinessConfigResponse(
            scope=updated_config.scope,
            config=updated_config.data,
            version=updated_config.version,
            updated_at=updated_config.updated_at
        )
        
    except ValueError as e:
        # Version mismatch or validation error
        if "version mismatch" in str(e).lower():
            raise HTTPException(status_code=409, detail=str(e))
        else:
            raise HTTPException(status_code=422, detail=str(e))
            
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail=ValidationErrorResponse(
                validation_errors=[str(err) for err in e.errors()]
            ).dict()
        )
        
    except Exception as e:
        logger.error(f"Config update failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Configuration update failed: {str(e)}"
        )


@router.post("/preview", response_model=ConfigPreviewResponse)
async def preview_config(
    request: ConfigPreviewRequest,
    config_service: BusinessConfigService = Depends(get_config_service)
):
    """
    Preview configuration changes without applying them.
    
    Tests changes against demo ASINs and shows before/after comparison.
    """
    try:
        # Initialize preview service
        preview_service = ConfigPreviewService()
        
        # Convert pydantic model to dict
        config_patch = request.config_patch.dict(exclude_unset=True, exclude_none=True)
        
        # Generate preview
        preview_results = await preview_service.preview_config_impact(
            config_patch=config_patch,
            domain_id=request.domain_id,
            category=request.category
        )
        
        # Generate config summary
        config_summary = {
            "domain_id": request.domain_id,
            "category": request.category,
            "patch_size": len(str(config_patch)),
            "demo_asins_tested": len(preview_results),
            "changes_detected": sum(1 for r in preview_results if r.get("changes"))
        }
        
        # Check for validation warnings (non-blocking)
        validation_warnings = []
        temp_service = get_business_config_service()
        
        # Get current config and merge for validation
        current_config = await temp_service.get_effective_config(
            request.domain_id, request.category
        )
        merged_config = temp_service._deep_merge_configs([current_config, config_patch])
        validation_errors = await temp_service._validate_config(merged_config)
        
        validation_warnings = validation_errors  # Convert errors to warnings for preview
        
        logger.info(f"Config preview completed: {len(preview_results)} ASINs tested")
        
        return ConfigPreviewResponse(
            preview_results=preview_results,
            config_summary=config_summary,
            validation_warnings=validation_warnings
        )
        
    except Exception as e:
        logger.error(f"Config preview failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Configuration preview failed: {str(e)}"
        )


@router.get("/changes", response_model=List[ConfigChangeResponse])
async def get_config_changes(
    scope: Optional[str] = Query(None, description="Filter by configuration scope"),
    changed_by: Optional[str] = Query(None, description="Filter by user who made changes"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of changes to return"),
    config_service: BusinessConfigService = Depends(get_config_service)
):
    """
    Get configuration change history (audit trail).
    
    Returns recent configuration changes with diffs and metadata.
    """
    try:
        changes = await config_service.get_config_changes(
            scope=scope,
            changed_by=changed_by,
            limit=limit
        )
        
        # Convert to response format
        change_responses = []
        for change in changes:
            change_responses.append(ConfigChangeResponse(
                change_id=change.id,
                config_scope=change.config.scope if change.config else "unknown",
                changed_by=change.changed_by,
                change_reason=change.change_reason,
                change_source=change.change_source,
                old_version=change.old_version,
                new_version=change.new_version,
                diff_summary=change.summary,  # Uses property from model
                diff_jsonpatch=change.diff_jsonpatch,
                changed_at=change.created_at
            ))
        
        logger.info(f"Retrieved {len(change_responses)} config changes")
        return change_responses
        
    except Exception as e:
        logger.error(f"Failed to get config changes: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve configuration changes: {str(e)}"
        )


@router.get("/stats", response_model=ConfigStatsResponse)
async def get_config_stats(
    config_service: BusinessConfigService = Depends(get_config_service),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get configuration service statistics and health info.

    Useful for monitoring cache performance and service health.
    Returns real database counts instead of placeholders.
    """
    try:
        # Get cache statistics
        cache_stats = config_service.get_cache_stats()

        # Real database queries for accurate statistics
        # Count total configs
        total_result = await db.execute(
            select(func.count()).select_from(BusinessConfig)
        )
        total_configs = total_result.scalar() or 0

        # Count active configs
        active_result = await db.execute(
            select(func.count()).select_from(BusinessConfig).where(
                BusinessConfig.is_active == True
            )
        )
        active_configs = active_result.scalar() or 0

        # Count recent changes (last 24 hours)
        yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_result = await db.execute(
            select(func.count()).select_from(BusinessConfig).where(
                BusinessConfig.updated_at > yesterday
            )
        )
        recent_changes = recent_result.scalar() or 0

        return ConfigStatsResponse(
            cache_stats=cache_stats,
            total_configs=total_configs,
            active_configs=active_configs,
            recent_changes=recent_changes,
            service_health="healthy"
        )

    except Exception as e:
        logger.error(f"Failed to get config stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve configuration statistics: {str(e)}"
        )


# Health check endpoint for config service
@router.get("/health")
async def config_service_health():
    """Basic health check for configuration service."""
    try:
        service = get_business_config_service()
        cache_stats = service.get_cache_stats()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "cache_active": cache_stats["active_entries"],
            "service": "business_config"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy", 
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "service": "business_config"
        }