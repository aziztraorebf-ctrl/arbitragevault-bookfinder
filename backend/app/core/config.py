"""Application configuration."""

import os
from typing import Optional
from pydantic_settings import BaseSettings


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
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "ignore"  # Ignore extra env variables
    }


# Create settings instance
settings = Settings()