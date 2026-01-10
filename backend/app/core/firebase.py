"""Firebase Admin SDK initialization and utilities."""

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

import structlog
from dotenv import load_dotenv
from firebase_admin import auth, credentials, initialize_app
from firebase_admin.auth import ExpiredIdTokenError, InvalidIdTokenError, RevokedIdTokenError

# Load .env file for Firebase credentials
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

logger = structlog.get_logger()

_firebase_app = None


def get_firebase_credentials():
    """
    Get Firebase credentials from environment variables.

    Supports two modes:
    1. FIREBASE_SERVICE_ACCOUNT_JSON - Full JSON string (for Render/production)
    2. FIREBASE_SERVICE_ACCOUNT_PATH - Path to JSON file (for local dev)
    """
    # Try JSON string first (production)
    json_str = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if json_str:
        try:
            service_account_info = json.loads(json_str)
            return credentials.Certificate(service_account_info)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse FIREBASE_SERVICE_ACCOUNT_JSON", error=str(e))
            raise ValueError("Invalid FIREBASE_SERVICE_ACCOUNT_JSON format")

    # Try file path (local development)
    json_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    if json_path and os.path.exists(json_path):
        return credentials.Certificate(json_path)

    # Check for individual env vars as fallback
    project_id = os.getenv("FIREBASE_PROJECT_ID")
    client_email = os.getenv("FIREBASE_CLIENT_EMAIL")
    private_key = os.getenv("FIREBASE_PRIVATE_KEY")

    if project_id and client_email and private_key:
        # Handle escaped newlines in private key
        private_key = private_key.replace("\\n", "\n")
        service_account_info = {
            "type": "service_account",
            "project_id": project_id,
            "client_email": client_email,
            "private_key": private_key,
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        return credentials.Certificate(service_account_info)

    raise ValueError(
        "Firebase credentials not configured. Set FIREBASE_SERVICE_ACCOUNT_JSON, "
        "FIREBASE_SERVICE_ACCOUNT_PATH, or individual FIREBASE_* env vars."
    )


def init_firebase():
    """Initialize Firebase Admin SDK (called once at startup)."""
    global _firebase_app

    if _firebase_app is not None:
        return _firebase_app

    try:
        cred = get_firebase_credentials()
        _firebase_app = initialize_app(cred)
        logger.info("Firebase Admin SDK initialized successfully")
        return _firebase_app
    except Exception as e:
        logger.error("Failed to initialize Firebase Admin SDK", error=str(e))
        raise


def verify_firebase_token(id_token: str) -> Optional[dict]:
    """
    Verify a Firebase ID token and return the decoded claims.

    Args:
        id_token: The Firebase ID token from the client

    Returns:
        Dict with user claims (uid, email, etc.) or None if invalid

    Raises:
        InvalidIdTokenError: Token is malformed or invalid
        ExpiredIdTokenError: Token has expired
        RevokedIdTokenError: Token has been revoked
    """
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except ExpiredIdTokenError:
        logger.warning("Firebase token expired")
        raise
    except RevokedIdTokenError:
        logger.warning("Firebase token revoked")
        raise
    except InvalidIdTokenError as e:
        logger.warning("Invalid Firebase token", error=str(e))
        raise
    except Exception as e:
        logger.error("Unexpected error verifying Firebase token", error=str(e))
        raise


def get_firebase_user(uid: str) -> Optional[auth.UserRecord]:
    """
    Get Firebase user by UID.

    Args:
        uid: Firebase user UID

    Returns:
        UserRecord or None if not found
    """
    try:
        return auth.get_user(uid)
    except auth.UserNotFoundError:
        return None
    except Exception as e:
        logger.error("Error fetching Firebase user", uid=uid, error=str(e))
        raise
