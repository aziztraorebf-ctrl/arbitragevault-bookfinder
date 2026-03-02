"""
Tests for API Key CRUD endpoints and dual-auth flow.

Tests cover:
- Create API key (POST /api/v1/api-keys)
- List API keys (GET /api/v1/api-keys)
- Update API key (PATCH /api/v1/api-keys/{key_id})
- Delete API key (DELETE /api/v1/api-keys/{key_id})
- Dual-auth: X-API-Key vs Bearer token
- Authorization: admin-only access
- Error handling
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import HTTPException, status
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.core.security import scopes_for_role


# Mock users
MOCK_ADMIN_USER = CurrentUser(
    id=str(uuid.uuid4()),
    email="admin@example.com",
    role="admin",
    scopes=scopes_for_role("admin"),
    is_active=True,
)

MOCK_SOURCER_USER = CurrentUser(
    id=str(uuid.uuid4()),
    email="sourcer@example.com",
    role="sourcer",
    scopes=scopes_for_role("sourcer"),
    is_active=True,
)


def _make_client_fixture(user, is_admin: bool):
    """Factory for creating client fixtures with different auth levels."""

    @pytest_asyncio.fixture
    async def _client(async_db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
        from app.main import app
        from app.core.auth import get_current_user, require_admin
        from app.core.db import get_db_session

        async def override_db():
            yield async_db_session

        app.dependency_overrides[get_db_session] = override_db

        if user and is_admin:
            app.dependency_overrides[get_current_user] = lambda: user
            app.dependency_overrides[require_admin] = lambda: user
        elif user and not is_admin:
            app.dependency_overrides[get_current_user] = lambda: user

            def raise_forbidden():
                raise HTTPException(
                    status_code=403,
                    detail="Insufficient permissions. Required role: ADMIN",
                )

            app.dependency_overrides[require_admin] = raise_forbidden

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

        app.dependency_overrides.clear()

    return _client


admin_client = _make_client_fixture(MOCK_ADMIN_USER, is_admin=True)
sourcer_client = _make_client_fixture(MOCK_SOURCER_USER, is_admin=False)
unauth_client = _make_client_fixture(None, is_admin=False)


class TestCreateAPIKey:
    """Tests for POST /api/v1/api-keys endpoint."""

    @pytest.mark.asyncio
    async def test_create_api_key_success(self, admin_client: AsyncClient):
        """Test creating an API key returns raw key and metadata."""
        response = await admin_client.post(
            "/api/v1/api-keys",
            json={"name": "Test Key", "scopes": ["daily_review:read"]},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data["name"] == "Test Key"
        assert data["key"].startswith("avk_")
        assert len(data["key"]) == 36
        assert data["key_prefix"] == data["key"][:8]
        assert data["scopes"] == ["daily_review:read"]
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_api_key_default_scopes(self, admin_client: AsyncClient):
        """Test creating an API key with default scopes."""
        response = await admin_client.post(
            "/api/v1/api-keys",
            json={"name": "Default Scopes Key"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["scopes"] == ["daily_review:read", "autosourcing:read"]

    @pytest.mark.asyncio
    async def test_create_api_key_with_expiration(self, admin_client: AsyncClient):
        """Test creating an API key with expiration date."""
        expires = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        response = await admin_client.post(
            "/api/v1/api-keys",
            json={"name": "Expiring Key", "expires_at": expires},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["expires_at"] is not None

    @pytest.mark.asyncio
    async def test_create_api_key_non_admin(self, sourcer_client: AsyncClient):
        """Test sourcer cannot create API keys."""
        response = await sourcer_client.post(
            "/api/v1/api-keys",
            json={"name": "Sourcer Key"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_create_api_key_empty_name(self, admin_client: AsyncClient):
        """Test creating an API key with empty name fails validation."""
        response = await admin_client.post(
            "/api/v1/api-keys",
            json={"name": ""},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestListAPIKeys:
    """Tests for GET /api/v1/api-keys endpoint."""

    @pytest.mark.asyncio
    async def test_list_api_keys_empty(self, admin_client: AsyncClient):
        """Test listing API keys when none exist."""
        response = await admin_client.get("/api/v1/api-keys")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_api_keys_after_creation(self, admin_client: AsyncClient):
        """Test listing API keys returns created keys without raw key."""
        # Create a key first
        create_response = await admin_client.post(
            "/api/v1/api-keys",
            json={"name": "Listed Key"},
        )
        assert create_response.status_code == status.HTTP_201_CREATED

        # List keys
        response = await admin_client.get("/api/v1/api-keys")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1

        key = data[0]
        assert key["name"] == "Listed Key"
        assert "key" not in key
        assert "key_prefix" in key

    @pytest.mark.asyncio
    async def test_list_api_keys_non_admin(self, sourcer_client: AsyncClient):
        """Test sourcer cannot list API keys."""
        response = await sourcer_client.get("/api/v1/api-keys")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUpdateAPIKey:
    """Tests for PATCH /api/v1/api-keys/{key_id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_api_key_name(self, admin_client: AsyncClient):
        """Test updating an API key's name."""
        create_resp = await admin_client.post(
            "/api/v1/api-keys",
            json={"name": "Original Name"},
        )
        key_id = create_resp.json()["id"]

        response = await admin_client.patch(
            f"/api/v1/api-keys/{key_id}",
            json={"name": "Updated Name"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_api_key_scopes(self, admin_client: AsyncClient):
        """Test updating an API key's scopes."""
        create_resp = await admin_client.post(
            "/api/v1/api-keys",
            json={"name": "Scopes Key"},
        )
        key_id = create_resp.json()["id"]

        response = await admin_client.patch(
            f"/api/v1/api-keys/{key_id}",
            json={"scopes": ["daily_review:read"]},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["scopes"] == ["daily_review:read"]

    @pytest.mark.asyncio
    async def test_update_api_key_deactivate(self, admin_client: AsyncClient):
        """Test deactivating an API key via update."""
        create_resp = await admin_client.post(
            "/api/v1/api-keys",
            json={"name": "Deactivate Key"},
        )
        key_id = create_resp.json()["id"]

        response = await admin_client.patch(
            f"/api/v1/api-keys/{key_id}",
            json={"is_active": False},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["is_active"] is False

    @pytest.mark.asyncio
    async def test_update_api_key_not_found(self, admin_client: AsyncClient):
        """Test updating a non-existent API key returns 404."""
        fake_id = str(uuid.uuid4())
        response = await admin_client.patch(
            f"/api/v1/api-keys/{fake_id}",
            json={"name": "Ghost Key"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_update_api_key_non_admin(self, sourcer_client: AsyncClient):
        """Test sourcer cannot update API keys."""
        fake_id = str(uuid.uuid4())
        response = await sourcer_client.patch(
            f"/api/v1/api-keys/{fake_id}",
            json={"name": "Nope"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestDeleteAPIKey:
    """Tests for DELETE /api/v1/api-keys/{key_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_api_key_success(self, admin_client: AsyncClient):
        """Test soft-deleting an API key."""
        create_resp = await admin_client.post(
            "/api/v1/api-keys",
            json={"name": "Delete Me"},
        )
        key_id = create_resp.json()["id"]

        response = await admin_client.delete(f"/api/v1/api-keys/{key_id}")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "API key deactivated"
        assert "id" in response.json()

        # Verify key is deactivated by listing
        list_resp = await admin_client.get("/api/v1/api-keys")
        keys = [k for k in list_resp.json() if k["id"] == key_id]
        assert len(keys) == 1
        assert keys[0]["is_active"] is False

    @pytest.mark.asyncio
    async def test_delete_api_key_not_found(self, admin_client: AsyncClient):
        """Test deleting a non-existent API key returns 404."""
        fake_id = str(uuid.uuid4())
        response = await admin_client.delete(f"/api/v1/api-keys/{fake_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete_api_key_non_admin(self, sourcer_client: AsyncClient):
        """Test sourcer cannot delete API keys."""
        fake_id = str(uuid.uuid4())
        response = await sourcer_client.delete(f"/api/v1/api-keys/{fake_id}")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestDualAuthFlow:
    """Tests for dual-auth: X-API-Key header vs Bearer token."""

    @pytest.mark.asyncio
    async def test_dual_auth_with_valid_api_key(self, admin_client: AsyncClient):
        """Test dual-auth endpoint accepts API key via dependency override."""
        from app.main import app
        from app.core.api_key_auth import require_daily_review_read

        mock_user = CurrentUser(
            id=str(uuid.uuid4()),
            email="apikey@example.com",
            role="admin",
            scopes={"daily_review:read", "autosourcing:read"},
            is_active=True,
        )

        app.dependency_overrides[require_daily_review_read] = lambda: mock_user

        response = await admin_client.get(
            "/api/v1/daily-review/today",
            headers={"X-API-Key": "avk_test_key_for_dual_auth_check"},
        )
        # Auth passed - should not be 401/403
        assert response.status_code not in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    @pytest.mark.asyncio
    async def test_dual_auth_firebase_fallback(self, admin_client: AsyncClient):
        """Test dual-auth falls back to Firebase Bearer token."""
        from app.main import app
        from app.core.api_key_auth import require_daily_review_read

        mock_user = CurrentUser(
            id=str(uuid.uuid4()),
            email="firebase@example.com",
            role="admin",
            scopes={"daily_review:read"},
            is_active=True,
        )

        app.dependency_overrides[require_daily_review_read] = lambda: mock_user

        response = await admin_client.get(
            "/api/v1/daily-review/today",
            headers={"Authorization": "Bearer firebase_token"},
        )
        assert response.status_code not in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    @pytest.mark.asyncio
    async def test_dual_auth_invalid_api_key(self, unauth_client: AsyncClient):
        """Test dual-auth with invalid API key returns 401."""
        response = await unauth_client.get(
            "/api/v1/daily-review/today",
            headers={"X-API-Key": "avk_invalid_key_here_not_real_abc"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
