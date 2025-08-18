"""Security utilities for password hashing and JWT operations."""

import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

import structlog
from jose import JWTError, jwt
from passlib.context import CryptContext

from .settings import get_settings

logger = structlog.get_logger()

# Password hashing context
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

# Role to scopes mapping
ROLE_SCOPES: Dict[str, Set[str]] = {
    "ADMIN": {
        "analyses:read",
        "analyses:write",
        "analyses:delete",
        "batches:read",
        "batches:write",
        "batches:delete",
        "users:read",
        "users:write",
        "users:admin",
    },
    "SOURCER": {
        "analyses:read",
        "analyses:write",
        "batches:read",
        "batches:write",
        "users:read",
    },
}


def hash_password(password: str) -> str:
    """Hash password using configured scheme with pepper."""
    settings = get_settings()

    # Add pepper to password before hashing
    try:
        pepper = settings.get_pepper()
        peppered_password = password + pepper
    except ValueError:
        logger.warning("PEPPER not configured, using password without pepper")
        peppered_password = password

    return pwd_context.hash(peppered_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    settings = get_settings()

    # Add pepper to password before verification
    try:
        pepper = settings.get_pepper()
        peppered_password = plain_password + pepper
    except ValueError:
        logger.warning("PEPPER not configured, verifying password without pepper")
        peppered_password = plain_password

    return pwd_context.verify(peppered_password, hashed_password)


def validate_password_strength(password: str) -> List[str]:
    """Validate password meets security requirements."""
    settings = get_settings()
    errors = []

    if len(password) < settings.password_min_length:
        errors.append(
            f"Password must be at least {settings.password_min_length} characters"
        )

    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")

    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")

    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")

    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        errors.append("Password must contain at least one special character")

    # Check for common weak patterns
    weak_patterns = ["123456", "password", "qwerty", "abc123", "admin"]
    if any(pattern in password.lower() for pattern in weak_patterns):
        errors.append("Password contains common weak patterns")

    return errors


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    settings = get_settings()
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({"exp": expire, "type": "access"})

    try:
        secret = settings.get_jwt_secret()
    except ValueError:
        logger.error("JWT_SECRET not configured")
        raise

    encoded_jwt = jwt.encode(to_encode, secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def create_refresh_token(data: Dict) -> str:
    """Create JWT refresh token."""
    settings = get_settings()
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})

    try:
        secret = settings.get_jwt_secret()
    except ValueError:
        logger.error("JWT_SECRET not configured")
        raise

    encoded_jwt = jwt.encode(to_encode, secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict]:
    """Decode and validate JWT token."""
    settings = get_settings()

    try:
        secret = settings.get_jwt_secret()
        payload = jwt.decode(token, secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError as e:
        logger.warning("Token decode failed", error=str(e))
        return None
    except ValueError:
        logger.error("JWT_SECRET not configured")
        return None


def hash_refresh_token(token: str) -> str:
    """Hash refresh token for secure storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def scopes_for_role(role: str) -> Set[str]:
    """Get scopes for a given role."""
    return ROLE_SCOPES.get(role.upper(), set())


def validate_scopes(required_scopes: Set[str], user_scopes: Set[str]) -> bool:
    """Check if user has required scopes."""
    return required_scopes.issubset(user_scopes)


def get_token_type(token: str) -> Optional[str]:
    """Extract token type from JWT payload."""
    payload = decode_token(token)
    if payload:
        return payload.get("type")
    return None


def is_token_expired(token: str) -> bool:
    """Check if token is expired."""
    payload = decode_token(token)
    if not payload:
        return True

    exp = payload.get("exp")
    if not exp:
        return True

    return datetime.utcnow().timestamp() > exp
