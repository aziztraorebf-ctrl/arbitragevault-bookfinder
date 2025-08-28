"""
Keepa Service Factory - Handles API key injection and service creation
"""
import keyring
import logging
from typing import Optional
from .keepa_service import KeepaService

logger = logging.getLogger(__name__)

class KeepaServiceFactory:
    """Factory for creating KeepaService instances with proper API key injection."""
    
    _instance: Optional[KeepaService] = None
    
    @classmethod
    async def get_keepa_service(cls) -> KeepaService:
        """Get or create KeepaService instance with API key from secrets."""
        if cls._instance is None:
            api_key = cls._get_api_key_from_secrets()
            if not api_key:
                raise ValueError("Keepa API key not found in secrets. Please add it via Memex UI or keyring.")
            
            cls._instance = KeepaService(api_key=api_key)
            logger.info("KeepaService initialized with API key from secrets")
        
        return cls._instance
    
    @classmethod
    def _get_api_key_from_secrets(cls) -> Optional[str]:
        """Retrieve Keepa API key from keyring/secrets with fallback attempts."""
        key_variations = [
            "KEEPA_API_KEY",
            "keepa_api_key", 
            "keepa-api-key",
            "KEEPA_KEY",
            "keepa_key"
        ]
        
        # Try to get from keyring (Memex secrets)
        for key_name in key_variations:
            try:
                api_key = keyring.get_password("memex", key_name)
                if api_key and len(api_key) > 10:  # Basic validation
                    logger.info(f"Found Keepa API key via keyring: {key_name}")
                    return api_key
            except Exception as e:
                logger.debug(f"Failed to get {key_name} from keyring: {e}")
        
        logger.warning("No valid Keepa API key found in secrets")
        return None
    
    @classmethod
    def create_test_service(cls, api_key: str) -> KeepaService:
        """Create KeepaService for testing with explicit API key."""
        return KeepaService(api_key=api_key)
    
    @classmethod
    def reset_instance(cls):
        """Reset singleton instance - useful for testing."""
        if cls._instance:
            # Note: In production we might want to properly close the service
            pass
        cls._instance = None

# Convenience function for easy import
async def get_keepa_service() -> KeepaService:
    """Convenience function to get KeepaService instance."""
    return await KeepaServiceFactory.get_keepa_service()