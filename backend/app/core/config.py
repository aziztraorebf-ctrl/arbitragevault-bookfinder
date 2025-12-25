"""Application configuration."""

import os
import logging
from typing import Optional
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

# Security: Default key that MUST be changed in production
_DEFAULT_SECRET_KEY = "dev-secret-key-change-in-production"


class Settings(BaseSettings):
    """Application settings."""

    # API Settings
    PROJECT_NAME: str = "ArbitrageVault BookFinder API"
    VERSION: str = "1.5.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/arbitragevault"
    )

    # Keepa API
    KEEPA_API_KEY: Optional[str] = os.getenv("KEEPA_API_KEY")

    # CORS
    BACKEND_CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]

    # JWT Settings (for future auth)
    SECRET_KEY: str = os.getenv("SECRET_KEY", _DEFAULT_SECRET_KEY)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "ignore"  # Ignore extra env variables
    }

    def validate_security(self) -> None:
        """
        Validate security-critical settings.
        Logs warnings for insecure configurations.
        Should be called at application startup.
        """
        environment = os.getenv("ENVIRONMENT", "development")

        # Check SECRET_KEY
        if self.SECRET_KEY == _DEFAULT_SECRET_KEY:
            if environment == "production":
                logger.error(
                    "SECURITY CRITICAL: SECRET_KEY is using default value in PRODUCTION! "
                    "Set SECRET_KEY environment variable immediately."
                )
            else:
                logger.warning(
                    "SECRET_KEY is using default value. "
                    "This is acceptable for development but MUST be changed in production."
                )

        # Check KEEPA_API_KEY
        if not self.KEEPA_API_KEY:
            logger.warning("KEEPA_API_KEY is not configured. Keepa API calls will fail.")


# Create settings instance
settings = Settings()

# Validate security at import time (startup)
settings.validate_security()