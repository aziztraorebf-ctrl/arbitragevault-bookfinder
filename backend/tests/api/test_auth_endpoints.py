"""
Tests for Firebase Authentication endpoints.

Tests cover:
- Token verification
- User sync
- Error handling
- Edge cases
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import status
from httpx import AsyncClient

from app.models.user import User


# Mock Firebase token claims
MOCK_FIREBASE_CLAIMS = {
    "uid": "test_firebase_uid_123",
    "email": "test@example.com",
    "name": "Test User",
    "email_verified": True,
}


@pytest.fixture
def mock_firebase_verify():
    """Mock Firebase token verification."""
    with patch("app.core.firebase.verify_firebase_token") as mock:
        mock.return_value = MOCK_FIREBASE_CLAIMS
        yield mock


@pytest.fixture
def mock_firebase_verify_invalid():
    """Mock Firebase token verification - invalid token."""
    with patch("app.core.firebase.verify_firebase_token") as mock:
        from firebase_admin.auth import InvalidIdTokenError
        mock.side_effect = InvalidIdTokenError("Invalid token")
        yield mock


@pytest.fixture
def mock_firebase_verify_expired():
    """Mock Firebase token verification - expired token."""
    with patch("app.core.firebase.verify_firebase_token") as mock:
        from firebase_admin.auth import ExpiredIdTokenError
        mock.side_effect = ExpiredIdTokenError("Token expired")
        yield mock


class TestAuthMeEndpoint:
    """Tests for GET /api/v1/auth/me endpoint."""

    @pytest.mark.asyncio
    async def test_get_me_without_token(self, async_client: AsyncClient):
        """Test /me without authorization header returns 422."""
        response = await async_client.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_get_me_with_invalid_token(
        self, async_client: AsyncClient, mock_firebase_verify_invalid
    ):
        """Test /me with invalid token returns 401."""
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_me_with_expired_token(
        self, async_client: AsyncClient, mock_firebase_verify_expired
    ):
        """Test /me with expired token returns 401."""
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer expired_token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_me_with_valid_token_new_user(
        self, async_client: AsyncClient, mock_firebase_verify
    ):
        """Test /me with valid token creates user and returns data."""
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer valid_token"}
        )

        # Should succeed and create user
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["email"] == "test@example.com"
        assert data["firebase_uid"] == "test_firebase_uid_123"
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_get_me_existing_user(
        self, async_client: AsyncClient, mock_firebase_verify, db_session
    ):
        """Test /me with existing user returns their data."""
        # Create existing user
        from app.repositories.user_repository import UserRepository
        repo = UserRepository(db_session)
        existing_user = await repo.create_user_from_firebase(
            firebase_uid="test_firebase_uid_123",
            email="test@example.com",
            first_name="Existing",
            last_name="User",
            role="admin",
        )
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer valid_token"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["email"] == "test@example.com"
        assert data["first_name"] == "Existing"
        assert data["role"] == "admin"


class TestAuthSyncEndpoint:
    """Tests for POST /api/v1/auth/sync endpoint."""

    @pytest.mark.asyncio
    async def test_sync_without_token(self, async_client: AsyncClient):
        """Test /sync without authorization header returns 422."""
        response = await async_client.post("/api/v1/auth/sync")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_sync_creates_new_user(
        self, async_client: AsyncClient, mock_firebase_verify
    ):
        """Test /sync creates new user from Firebase token."""
        response = await async_client.post(
            "/api/v1/auth/sync",
            headers={"Authorization": "Bearer valid_token"}
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data["email"] == "test@example.com"
        assert data["firebase_uid"] == "test_firebase_uid_123"
        assert data["first_name"] == "Test"
        assert data["last_name"] == "User"

    @pytest.mark.asyncio
    async def test_sync_links_existing_user_by_email(
        self, async_client: AsyncClient, mock_firebase_verify, db_session
    ):
        """Test /sync links Firebase UID to existing user with same email."""
        # Create user without firebase_uid
        from app.models.user import User
        import uuid

        existing_user = User(
            id=str(uuid.uuid4()),
            email="test@example.com",
            firebase_uid=None,
            password_hash="old_hash",
            role="sourcer",
        )
        db_session.add(existing_user)
        await db_session.commit()
        await db_session.refresh(existing_user)

        response = await async_client.post(
            "/api/v1/auth/sync",
            headers={"Authorization": "Bearer valid_token"}
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        # Should be the same user, now linked
        assert data["id"] == str(existing_user.id)
        assert data["firebase_uid"] == "test_firebase_uid_123"

    @pytest.mark.asyncio
    async def test_sync_inactive_user(
        self, async_client: AsyncClient, mock_firebase_verify, db_session
    ):
        """Test /sync with inactive user returns 403."""
        # Create inactive user
        from app.repositories.user_repository import UserRepository
        repo = UserRepository(db_session)
        inactive_user = await repo.create_user_from_firebase(
            firebase_uid="test_firebase_uid_123",
            email="test@example.com",
        )
        inactive_user.is_active = False
        await db_session.commit()

        response = await async_client.post(
            "/api/v1/auth/sync",
            headers={"Authorization": "Bearer valid_token"}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestAuthVerifyEndpoint:
    """Tests for GET /api/v1/auth/verify endpoint."""

    @pytest.mark.asyncio
    async def test_verify_valid_token(
        self, async_client: AsyncClient, mock_firebase_verify
    ):
        """Test /verify with valid token returns success."""
        response = await async_client.get(
            "/api/v1/auth/verify",
            headers={"Authorization": "Bearer valid_token"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["valid"] is True
        assert data["uid"] == "test_firebase_uid_123"
        assert data["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_verify_invalid_token(
        self, async_client: AsyncClient, mock_firebase_verify_invalid
    ):
        """Test /verify with invalid token returns 401."""
        response = await async_client.get(
            "/api/v1/auth/verify",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestFirebaseAuthService:
    """Tests for FirebaseAuthService."""

    @pytest.mark.asyncio
    async def test_get_or_create_user_new(self, db_session):
        """Test creating a new user from Firebase claims."""
        from app.services.firebase_auth_service import FirebaseAuthService

        service = FirebaseAuthService(db_session)

        with patch("app.core.firebase.verify_firebase_token") as mock_verify:
            mock_verify.return_value = MOCK_FIREBASE_CLAIMS

            user, claims = await service.verify_token_and_get_user("test_token")

            assert user.email == "test@example.com"
            assert user.firebase_uid == "test_firebase_uid_123"
            assert user.first_name == "Test"
            assert user.last_name == "User"

    @pytest.mark.asyncio
    async def test_get_or_create_user_existing_by_firebase_uid(self, db_session):
        """Test getting existing user by Firebase UID."""
        from app.services.firebase_auth_service import FirebaseAuthService
        from app.repositories.user_repository import UserRepository

        # Create existing user
        repo = UserRepository(db_session)
        existing = await repo.create_user_from_firebase(
            firebase_uid="test_firebase_uid_123",
            email="test@example.com",
            first_name="Original",
        )
        await db_session.commit()

        service = FirebaseAuthService(db_session)

        with patch("app.core.firebase.verify_firebase_token") as mock_verify:
            mock_verify.return_value = MOCK_FIREBASE_CLAIMS

            user, claims = await service.verify_token_and_get_user("test_token")

            assert user.id == existing.id
            assert user.first_name == "Original"

    @pytest.mark.asyncio
    async def test_get_or_create_user_link_by_email(self, db_session):
        """Test linking Firebase UID to existing user by email."""
        from app.services.firebase_auth_service import FirebaseAuthService
        from app.models.user import User
        import uuid

        # Create user without firebase_uid
        existing = User(
            id=str(uuid.uuid4()),
            email="test@example.com",
            firebase_uid=None,
            role="sourcer",
        )
        db_session.add(existing)
        await db_session.commit()
        await db_session.refresh(existing)

        service = FirebaseAuthService(db_session)

        with patch("app.core.firebase.verify_firebase_token") as mock_verify:
            mock_verify.return_value = MOCK_FIREBASE_CLAIMS

            user, claims = await service.verify_token_and_get_user("test_token")

            assert user.id == existing.id
            assert user.firebase_uid == "test_firebase_uid_123"
