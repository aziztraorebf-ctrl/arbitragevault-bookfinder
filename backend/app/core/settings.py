"""Application settings and configuration."""

from functools import lru_cache
from typing import List, Optional

import keyring
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    app_name: str = "ArbitrageVault API"
    version: str = "0.1.0"

    # Database
    database_url: str = Field(..., alias="DATABASE_URL")

    # JWT Configuration
    jwt_secret: Optional[str] = Field(default=None, alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=20, alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    refresh_token_expire_days: int = Field(
        default=14, alias="REFRESH_TOKEN_EXPIRE_DAYS"
    )

    # Password Security
    pepper: Optional[str] = Field(default=None, alias="PEPPER")
    password_hash_scheme: str = Field(default="argon2", alias="PASSWORD_HASH_SCHEME")
    password_min_length: int = Field(default=8, alias="PASSWORD_MIN_LENGTH")

    # CORS
    cors_allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        alias="CORS_ALLOWED_ORIGINS",
    )

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")

    # Rate Limiting
    rate_limit_login_per_15_min: int = Field(
        default=5, alias="RATE_LIMIT_LOGIN_PER_15_MIN"
    )
    rate_limit_register_per_hour: int = Field(
        default=3, alias="RATE_LIMIT_REGISTER_PER_HOUR"
    )

    # Security
    trusted_hosts: List[str] = Field(
        default=["localhost", "127.0.0.1"], alias="TRUSTED_HOSTS"
    )

    # Documentation
    enable_docs: bool = Field(default=True, alias="ENABLE_DOCS")
    enable_redoc: bool = Field(default=True, alias="ENABLE_REDOC")
    
    # API Keys
    keepa_api_key: Optional[str] = Field(default=None, alias="KEEPA_API_KEY")

    @validator("cors_allowed_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @validator("trusted_hosts", pre=True)
    def parse_trusted_hosts(cls, v):
        """Parse trusted hosts from string or list."""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v

    def get_jwt_secret(self) -> str:
        """Get JWT secret from keyring or environment variable."""
        if self.app_env == "production":
            try:
                secret = keyring.get_password("memex", "JWT_SECRET")
                if secret:
                    return secret
            except Exception:
                pass  # Fallback to env variable

        if self.jwt_secret:
            return self.jwt_secret

        raise ValueError("JWT_SECRET must be set in environment or keyring")

    def get_pepper(self) -> str:
        """Get password pepper from keyring or environment variable."""
        if self.app_env == "production":
            try:
                pepper = keyring.get_password("memex", "PEPPER")
                if pepper:
                    return pepper
            except Exception:
                pass  # Fallback to env variable

        if self.pepper:
            return self.pepper

        raise ValueError("PEPPER must be set in environment or keyring")

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env.lower() in ("development", "dev")

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env.lower() in ("production", "prod")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
