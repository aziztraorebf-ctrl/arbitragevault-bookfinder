"""
Business Configuration Service - Hierarchical config management with caching.
"""

import json
import threading
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging

import jsonpatch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.business_config import BusinessConfig, ConfigChange, DEFAULT_BUSINESS_CONFIG
from app.core.db import db_manager


logger = logging.getLogger(__name__)


@dataclass
class ConfigCacheEntry:
    """Cache entry for configuration data."""
    config: Dict[str, Any]
    timestamp: datetime
    scope: str
    ttl_minutes: int = 15  # Short TTL for business config
    
    def is_expired(self) -> bool:
        return datetime.now() > self.timestamp + timedelta(minutes=self.ttl_minutes)


class BusinessConfigService:
    """
    Hierarchical business configuration service.
    
    Features:
    - Deep merge: global < domain < category
    - Thread-safe caching with RLock
    - JSONPatch diff generation
    - Config validation and rollback
    """
    
    def __init__(self):
        self._cache: Dict[str, ConfigCacheEntry] = {}
        self._lock = threading.RLock()
        self._config_file_path = Path(__file__).parent.parent.parent / "config" / "business_rules.json"
        
    async def get_effective_config(
        self, 
        domain_id: int = 1, 
        category: str = "books", 
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Get effective configuration with hierarchical merging.
        
        Priority: global < domain < category
        
        Args:
            domain_id: Keepa domain ID (1=US, 2=UK, etc.)
            category: Product category
            force_refresh: Skip cache and reload from DB
            
        Returns:
            Merged configuration dict
        """
        cache_key = f"effective:{domain_id}:{category}"
        
        with self._lock:
            # Check cache first (unless force refresh)
            if not force_refresh:
                cached_entry = self._cache.get(cache_key)
                if cached_entry and not cached_entry.is_expired():
                    logger.debug(f"Config cache HIT for {cache_key}")
                    return cached_entry.config
            
            # Load and merge hierarchy
            try:
                async with db_manager.session() as session:
                    # 1. Load global config
                    global_config = await self._load_config_by_scope(session, "global")
                    if not global_config:
                        global_config = await self._load_fallback_config()
                    
                    # 2. Load domain override
                    domain_scope = f"domain:{domain_id}"
                    domain_config = await self._load_config_by_scope(session, domain_scope)
                    
                    # 3. Load category override  
                    category_scope = f"category:{category}"
                    category_config = await self._load_config_by_scope(session, category_scope)
                    
                    # 4. Deep merge hierarchy
                    effective_config = self._deep_merge_configs([
                        global_config,
                        domain_config, 
                        category_config
                    ])
                    
                    # Add metadata
                    effective_config["_meta"] = {
                        "domain_id": domain_id,
                        "category": category,
                        "generated_at": datetime.now().isoformat(),
                        "sources": {
                            "global": global_config is not None,
                            "domain": domain_config is not None, 
                            "category": category_config is not None
                        }
                    }
                    
                    # Cache result
                    self._cache[cache_key] = ConfigCacheEntry(
                        config=effective_config,
                        timestamp=datetime.now(),
                        scope=cache_key
                    )
                    
                    logger.info(f"Generated effective config for domain={domain_id}, category={category}")
                    return effective_config
                    
            except Exception as e:
                logger.warning(f"Failed to load effective config from DB: {e}")
                
        # Return fallback config if DB access fails
        logger.info("Using fallback configuration")
        fallback = await self._load_fallback_config()
        return fallback
    
    async def update_config(
        self,
        scope: str,
        config_patch: Dict[str, Any],
        changed_by: str,
        if_match_version: Optional[int] = None,
        change_reason: Optional[str] = None
    ) -> Tuple[BusinessConfig, ConfigChange]:
        """
        Update configuration with optimistic concurrency control.
        
        Args:
            scope: Config scope ("global", "domain:1", "category:books")
            config_patch: Partial config to merge
            changed_by: User identifier
            if_match_version: Expected version for optimistic locking
            change_reason: Optional change description
            
        Returns:
            Tuple of (updated_config, change_record)
            
        Raises:
            ValueError: If version mismatch or validation fails
        """
        async with db_manager.session() as session:
            try:
                # Load existing config
                existing_config = await self._load_config_by_scope(session, scope)
                
                if existing_config is None:
                    # Create new config entry
                    if scope == "global":
                        config_id = 1
                    else:
                        # Generate new ID for domain/category configs
                        config_id = None
                    
                    old_data = {}
                    old_version = 0
                else:
                    config_id = existing_config.id
                    old_data = existing_config.data
                    old_version = existing_config.version
                    
                    # Check version match if specified
                    if if_match_version is not None and existing_config.version != if_match_version:
                        raise ValueError(f"Version mismatch: expected {if_match_version}, got {existing_config.version}")
                
                # Deep merge patch with existing data
                new_data = self._deep_merge_configs([old_data, config_patch])
                
                # Validate new config
                validation_errors = await self._validate_config(new_data)
                if validation_errors:
                    raise ValueError(f"Config validation failed: {', '.join(validation_errors)}")
                
                # Generate JSONPatch diff
                diff_jsonpatch = self._generate_jsonpatch_diff(old_data, new_data)
                
                # Update or create config
                if existing_config:
                    existing_config.data = new_data
                    existing_config.version += 1
                    existing_config.updated_at = datetime.now()
                    updated_config = existing_config
                else:
                    updated_config = BusinessConfig(
                        id=config_id,
                        scope=scope,
                        data=new_data,
                        version=1,
                        description=f"Config for {scope}"
                    )
                    session.add(updated_config)
                
                # Create change record
                change_record = ConfigChange(
                    config_id=updated_config.id,
                    old_config=old_data,
                    new_config=new_data,
                    diff_jsonpatch=diff_jsonpatch,
                    changed_by=changed_by,
                    change_reason=change_reason,
                    change_source="api",
                    old_version=old_version,
                    new_version=updated_config.version
                )
                session.add(change_record)
                
                await session.commit()
                
                # Invalidate cache
                self._invalidate_cache()
                
                logger.info(f"Updated config {scope} by {changed_by} (version {old_version} → {updated_config.version})")
                return updated_config, change_record
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Config update failed: {e}")
                raise
    
    async def get_config_changes(
        self,
        scope: Optional[str] = None,
        limit: int = 20,
        changed_by: Optional[str] = None
    ) -> List[ConfigChange]:
        """
        Get configuration change history.
        
        Args:
            scope: Filter by config scope
            limit: Maximum number of changes to return
            changed_by: Filter by user who made changes
            
        Returns:
            List of ConfigChange records
        """
        async with db_manager.session() as session:
            query = select(ConfigChange).order_by(ConfigChange.created_at.desc())
            
            # Apply filters
            if scope:
                query = query.join(BusinessConfig).where(BusinessConfig.scope == scope)
            if changed_by:
                query = query.where(ConfigChange.changed_by == changed_by)
            
            query = query.limit(limit)
            
            result = await session.execute(query)
            changes = result.scalars().all()
            
            return changes
    
    def _deep_merge_configs(self, configs: List[Optional[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Deep merge multiple configuration dictionaries.
        
        Later configs override earlier ones.
        
        Args:
            configs: List of config dicts (None entries are skipped)
            
        Returns:
            Merged configuration dict
        """
        result = {}
        
        for config in configs:
            if config is None:
                continue
            
            result = self._recursive_merge(result, config)
        
        return result
    
    def _recursive_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge two dictionaries."""
        result = deepcopy(base)
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._recursive_merge(result[key], value)
            else:
                result[key] = deepcopy(value)
        
        return result
    
    def _generate_jsonpatch_diff(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate JSONPatch diff between two configurations."""
        try:
            patch = jsonpatch.make_patch(old_config, new_config)
            return patch.patch  # Return as list of dicts
        except Exception as e:
            logger.warning(f"JSONPatch generation failed: {e}")
            return [{"op": "replace", "path": "/", "value": new_config}]
    
    async def _load_config_by_scope(self, session: AsyncSession, scope: str) -> Optional[BusinessConfig]:
        """Load configuration by scope from database."""
        query = select(BusinessConfig).where(
            and_(
                BusinessConfig.scope == scope,
                BusinessConfig.is_active == True
            )
        )
        
        result = await session.execute(query)
        config = result.scalar_one_or_none()
        
        return config
    
    async def _load_fallback_config(self) -> Dict[str, Any]:
        """Load fallback config from file or default."""
        try:
            # Try to load from config file
            if self._config_file_path.exists():
                with open(self._config_file_path, 'r') as f:
                    config_data = json.load(f)
                    logger.info("Loaded fallback config from business_rules.json")
                    return config_data
        except Exception as e:
            logger.warning(f"Failed to load config file: {e}")
        
        # Use hardcoded default
        logger.info("Using hardcoded default config")
        return DEFAULT_BUSINESS_CONFIG
    
    async def _validate_config(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate configuration data.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        try:
            # Check combined score weights
            combined_score = config.get("combined_score", {})
            roi_weight = combined_score.get("roi_weight", 0.6)
            velocity_weight = combined_score.get("velocity_weight", 0.4)
            
            if abs(roi_weight + velocity_weight - 1.0) > 0.001:
                errors.append(f"Combined score weights must sum to 1.0 (got {roi_weight + velocity_weight})")
            
            if not (0 <= roi_weight <= 1):
                errors.append(f"ROI weight must be between 0 and 1 (got {roi_weight})")
            
            if not (0 <= velocity_weight <= 1):
                errors.append(f"Velocity weight must be between 0 and 1 (got {velocity_weight})")
            
            # Check ROI thresholds
            roi_config = config.get("roi", {})
            target_pct = roi_config.get("target_pct_default", 30.0)
            min_for_buy = roi_config.get("min_for_buy", 15.0)
            
            if not (0 <= target_pct <= 200):
                errors.append(f"ROI target must be between 0% and 200% (got {target_pct}%)")
            
            if not (0 <= min_for_buy <= 100):
                errors.append(f"ROI min for buy must be between 0% and 100% (got {min_for_buy}%)")
            
            # Check buffer percentage
            fees_config = config.get("fees", {})
            buffer_pct = fees_config.get("buffer_pct_default", 5.0)
            
            if not (0 <= buffer_pct <= 50):
                errors.append(f"Buffer percentage must be between 0% and 50% (got {buffer_pct}%)")
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return errors
    
    def _invalidate_cache(self):
        """Invalidate all cached configurations."""
        with self._lock:
            self._cache.clear()
            logger.debug("Config cache invalidated")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring."""
        with self._lock:
            total_entries = len(self._cache)
            expired_entries = sum(1 for entry in self._cache.values() if entry.is_expired())
            
            return {
                "total_entries": total_entries,
                "active_entries": total_entries - expired_entries,
                "expired_entries": expired_entries,
                "cache_keys": list(self._cache.keys())
            }


# Global service instance
_business_config_service = None
_service_lock = threading.Lock()


def get_business_config_service() -> BusinessConfigService:
    """Get singleton instance of BusinessConfigService."""
    global _business_config_service
    
    if _business_config_service is None:
        with _service_lock:
            if _business_config_service is None:
                _business_config_service = BusinessConfigService()
    
    return _business_config_service


async def get_effective_config(domain_id: int = 1, category: str = "books") -> Dict[str, Any]:
    """Convenience function to get effective configuration."""
    service = get_business_config_service()
    return await service.get_effective_config(domain_id, category)