"""
API Integration Tests for Bookmarks Endpoints
==============================================
Tests for /api/v1/bookmarks endpoints including auth, validation, and error cases.

Run: pytest tests/api/test_bookmarks_api.py -v
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from fastapi import HTTPException
from unittest.mock import MagicMock, patch

from app.main import app
from app.core.auth import get_current_user_id
from app.core.db import get_db_session
from app.services.bookmark_service import BookmarkService


class TestBookmarksAPIAuthentication:
    """Tests for authentication requirements on bookmark endpoints."""

    def test_create_bookmark_requires_auth(self):
        """POST /api/v1/bookmarks/niches returns 401 without auth token."""
        client = TestClient(app)

        response = client.post(
            "/api/v1/bookmarks/niches",
            json={
                "niche_name": "Test Niche",
                "category_id": 1,
                "filters": {}
            }
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_list_bookmarks_requires_auth(self):
        """GET /api/v1/bookmarks/niches returns 401 without auth token."""
        client = TestClient(app)

        response = client.get("/api/v1/bookmarks/niches")

        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"


class TestBookmarksAPIValidation:
    """Tests for request validation on bookmark endpoints."""

    def test_create_bookmark_validates_name_required(self):
        """POST /api/v1/bookmarks/niches returns 422 when niche_name is missing."""
        # Mock auth to bypass authentication
        def mock_user_id():
            return "test-user-123"

        def mock_db_session():
            return MagicMock()

        app.dependency_overrides[get_current_user_id] = mock_user_id
        app.dependency_overrides[get_db_session] = mock_db_session

        try:
            client = TestClient(app)

            # Missing niche_name in payload
            response = client.post(
                "/api/v1/bookmarks/niches",
                json={
                    "category_id": 1,
                    "filters": {}
                }
            )

            assert response.status_code == 422
            data = response.json()
            assert "detail" in data

            # Verify error mentions niche_name field
            errors = data["detail"]
            assert any(
                error["loc"][-1] == "niche_name"
                for error in errors
            )
        finally:
            app.dependency_overrides.clear()


class TestBookmarksAPIEmptyList:
    """Tests for empty list responses."""

    def test_list_bookmarks_returns_empty_list(self):
        """GET /api/v1/bookmarks/niches returns 200 with empty list when no bookmarks exist."""
        # Mock auth and service
        def mock_user_id():
            return "test-user-empty"

        def mock_bookmark_service(db):
            service_mock = MagicMock(spec=BookmarkService)
            service_mock.list_niches_by_user.return_value = ([], 0)
            return service_mock

        # Create a mock db session
        mock_db = MagicMock()

        def mock_db_session():
            return mock_db

        app.dependency_overrides[get_current_user_id] = mock_user_id
        app.dependency_overrides[get_db_session] = mock_db_session

        try:
            # Patch BookmarkService constructor to return our mock
            from unittest.mock import patch

            with patch('app.api.v1.routers.bookmarks.BookmarkService') as mock_service_class:
                mock_service_instance = MagicMock()
                mock_service_instance.list_niches_by_user.return_value = ([], 0)
                mock_service_class.return_value = mock_service_instance

                client = TestClient(app)
                response = client.get("/api/v1/bookmarks/niches")

                assert response.status_code == 200
                data = response.json()
                assert data["niches"] == []
                assert data["total_count"] == 0
        finally:
            app.dependency_overrides.clear()


class TestBookmarksAPINotFound:
    """Tests for 404 error cases."""

    def test_get_bookmark_not_found(self):
        """GET /api/v1/bookmarks/niches/{niche_id} returns 404 when bookmark doesn't exist."""
        # Mock auth and service
        def mock_user_id():
            return "test-user-404"

        mock_db = MagicMock()

        def mock_db_session():
            return mock_db

        app.dependency_overrides[get_current_user_id] = mock_user_id
        app.dependency_overrides[get_db_session] = mock_db_session

        try:
            from unittest.mock import patch

            with patch('app.api.v1.routers.bookmarks.BookmarkService') as mock_service_class:
                mock_service_instance = MagicMock()
                mock_service_instance.get_niche_by_id.return_value = None
                mock_service_class.return_value = mock_service_instance

                client = TestClient(app)
                response = client.get("/api/v1/bookmarks/niches/nonexistent-id")

                assert response.status_code == 404
                assert response.json()["detail"] == "Saved niche not found"
        finally:
            app.dependency_overrides.clear()

    def test_update_bookmark_not_found(self):
        """PUT /api/v1/bookmarks/niches/{niche_id} returns 404 when bookmark doesn't exist."""
        def mock_user_id():
            return "test-user-404"

        mock_db = MagicMock()

        def mock_db_session():
            return mock_db

        app.dependency_overrides[get_current_user_id] = mock_user_id
        app.dependency_overrides[get_db_session] = mock_db_session

        try:
            from unittest.mock import patch

            with patch('app.api.v1.routers.bookmarks.BookmarkService') as mock_service_class:
                mock_service_instance = MagicMock()
                mock_service_instance.update_niche.return_value = None
                mock_service_class.return_value = mock_service_instance

                client = TestClient(app)
                response = client.put(
                    "/api/v1/bookmarks/niches/nonexistent-id",
                    json={"niche_name": "Updated Name"}
                )

                assert response.status_code == 404
                assert response.json()["detail"] == "Saved niche not found"
        finally:
            app.dependency_overrides.clear()

    def test_delete_bookmark_not_found(self):
        """DELETE /api/v1/bookmarks/niches/{niche_id} returns 404 when bookmark doesn't exist."""
        def mock_user_id():
            return "test-user-404"

        mock_db = MagicMock()

        def mock_db_session():
            return mock_db

        app.dependency_overrides[get_current_user_id] = mock_user_id
        app.dependency_overrides[get_db_session] = mock_db_session

        try:
            from unittest.mock import patch

            with patch('app.api.v1.routers.bookmarks.BookmarkService') as mock_service_class:
                mock_service_instance = MagicMock()
                mock_service_instance.delete_niche.return_value = False
                mock_service_class.return_value = mock_service_instance

                client = TestClient(app)
                response = client.delete("/api/v1/bookmarks/niches/nonexistent-id")

                assert response.status_code == 404
                assert response.json()["detail"] == "Saved niche not found"
        finally:
            app.dependency_overrides.clear()

    def test_get_filters_not_found(self):
        """GET /api/v1/bookmarks/niches/{niche_id}/filters returns 404 when bookmark doesn't exist."""
        def mock_user_id():
            return "test-user-404"

        mock_db = MagicMock()

        def mock_db_session():
            return mock_db

        app.dependency_overrides[get_current_user_id] = mock_user_id
        app.dependency_overrides[get_db_session] = mock_db_session

        try:
            from unittest.mock import patch

            with patch('app.api.v1.routers.bookmarks.BookmarkService') as mock_service_class:
                mock_service_instance = MagicMock()
                mock_service_instance.get_niche_filters_for_analysis.return_value = None
                mock_service_class.return_value = mock_service_instance

                client = TestClient(app)
                response = client.get("/api/v1/bookmarks/niches/nonexistent-id/filters")

                assert response.status_code == 404
                assert response.json()["detail"] == "Saved niche not found"
        finally:
            app.dependency_overrides.clear()


class TestBookmarksAPISuccess:
    """Test successful API operations."""

    def test_create_bookmark_returns_201_with_valid_data(self):
        """POST /api/v1/bookmarks/niches returns 201 with valid niche data."""
        def mock_user_id():
            return "test-user-123"

        def mock_db_session():
            return MagicMock()

        app.dependency_overrides[get_current_user_id] = mock_user_id
        app.dependency_overrides[get_db_session] = mock_db_session

        try:
            with patch("app.api.v1.routers.bookmarks.BookmarkService") as MockService:
                mock_service = MockService.return_value

                mock_niche = MagicMock()
                mock_niche.id = "niche-123"
                mock_niche.niche_name = "Test Niche"
                mock_niche.user_id = "test-user-123"
                mock_niche.category_id = 283155
                mock_niche.category_name = "Books"
                mock_niche.filters = {"min_bsr": 1000}
                mock_niche.last_score = 85.5
                mock_niche.description = "Test description"
                mock_niche.created_at = datetime.now()
                mock_niche.updated_at = datetime.now()

                mock_service.create_niche.return_value = mock_niche

                client = TestClient(app)
                response = client.post(
                    "/api/v1/bookmarks/niches",
                    json={
                        "niche_name": "Test Niche",
                        "category_id": 283155,
                        "category_name": "Books",
                        "filters": {"min_bsr": 1000}
                    }
                )

                assert response.status_code == 201
                data = response.json()
                assert data["id"] == "niche-123"
                assert data["niche_name"] == "Test Niche"
        finally:
            app.dependency_overrides.clear()

    def test_get_bookmark_returns_200(self):
        """GET /api/v1/bookmarks/niches/{niche_id} returns 200 with bookmark data."""
        def mock_user_id():
            return "test-user-123"

        def mock_db_session():
            return MagicMock()

        app.dependency_overrides[get_current_user_id] = mock_user_id
        app.dependency_overrides[get_db_session] = mock_db_session

        try:
            with patch("app.api.v1.routers.bookmarks.BookmarkService") as MockService:
                mock_service = MockService.return_value

                mock_niche = MagicMock()
                mock_niche.id = "niche-456"
                mock_niche.niche_name = "Existing Niche"
                mock_niche.user_id = "test-user-123"
                mock_niche.category_id = 283155
                mock_niche.category_name = "Books"
                mock_niche.filters = {"min_bsr": 500}
                mock_niche.last_score = 92.0
                mock_niche.description = None
                mock_niche.created_at = datetime.now()
                mock_niche.updated_at = datetime.now()

                mock_service.get_niche_by_id.return_value = mock_niche

                client = TestClient(app)
                response = client.get("/api/v1/bookmarks/niches/niche-456")

                assert response.status_code == 200
                data = response.json()
                assert data["id"] == "niche-456"
                assert data["niche_name"] == "Existing Niche"
        finally:
            app.dependency_overrides.clear()

    def test_update_bookmark_returns_200(self):
        """PUT /api/v1/bookmarks/niches/{niche_id} returns 200 with updated data."""
        def mock_user_id():
            return "test-user-123"

        def mock_db_session():
            return MagicMock()

        app.dependency_overrides[get_current_user_id] = mock_user_id
        app.dependency_overrides[get_db_session] = mock_db_session

        try:
            with patch("app.api.v1.routers.bookmarks.BookmarkService") as MockService:
                mock_service = MockService.return_value

                mock_niche = MagicMock()
                mock_niche.id = "niche-789"
                mock_niche.niche_name = "Updated Niche Name"
                mock_niche.user_id = "test-user-123"
                mock_niche.category_id = 283155
                mock_niche.category_name = "Books"
                mock_niche.filters = {"min_bsr": 2000}
                mock_niche.last_score = 88.0
                mock_niche.description = "Updated description"
                mock_niche.created_at = datetime.now()
                mock_niche.updated_at = datetime.now()

                mock_service.update_niche.return_value = mock_niche

                client = TestClient(app)
                response = client.put(
                    "/api/v1/bookmarks/niches/niche-789",
                    json={
                        "niche_name": "Updated Niche Name",
                        "description": "Updated description"
                    }
                )

                assert response.status_code == 200
                data = response.json()
                assert data["id"] == "niche-789"
                assert data["niche_name"] == "Updated Niche Name"
                assert data["description"] == "Updated description"
        finally:
            app.dependency_overrides.clear()

    def test_delete_bookmark_returns_204(self):
        """DELETE /api/v1/bookmarks/niches/{niche_id} returns 204 on success."""
        def mock_user_id():
            return "test-user-123"

        def mock_db_session():
            return MagicMock()

        app.dependency_overrides[get_current_user_id] = mock_user_id
        app.dependency_overrides[get_db_session] = mock_db_session

        try:
            with patch("app.api.v1.routers.bookmarks.BookmarkService") as MockService:
                mock_service = MockService.return_value
                mock_service.delete_niche.return_value = True

                client = TestClient(app)
                response = client.delete("/api/v1/bookmarks/niches/niche-delete-123")

                assert response.status_code == 204
        finally:
            app.dependency_overrides.clear()

    def test_create_bookmark_duplicate_name_returns_409(self):
        """POST /api/v1/bookmarks/niches returns 409 when niche name already exists."""
        def mock_user_id():
            return "test-user-123"

        def mock_db_session():
            return MagicMock()

        app.dependency_overrides[get_current_user_id] = mock_user_id
        app.dependency_overrides[get_db_session] = mock_db_session

        try:
            with patch("app.api.v1.routers.bookmarks.BookmarkService") as MockService:
                mock_service = MockService.return_value
                mock_service.create_niche.side_effect = HTTPException(
                    status_code=409,
                    detail="Niche with name 'Test Niche' already exists for this user"
                )

                client = TestClient(app)
                response = client.post(
                    "/api/v1/bookmarks/niches",
                    json={
                        "niche_name": "Test Niche",
                        "category_id": 283155,
                        "category_name": "Books",
                        "filters": {"min_bsr": 1000}
                    }
                )

                assert response.status_code == 409
                assert "already exists" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_list_bookmarks_returns_paginated_results(self):
        """GET /api/v1/bookmarks/niches returns 200 with paginated results."""
        def mock_user_id():
            return "test-user-123"

        def mock_db_session():
            return MagicMock()

        app.dependency_overrides[get_current_user_id] = mock_user_id
        app.dependency_overrides[get_db_session] = mock_db_session

        try:
            with patch("app.api.v1.routers.bookmarks.BookmarkService") as MockService:
                mock_service = MockService.return_value

                mock_niche1 = MagicMock()
                mock_niche1.id = "niche-1"
                mock_niche1.niche_name = "Niche 1"
                mock_niche1.user_id = "test-user-123"
                mock_niche1.category_id = 283155
                mock_niche1.category_name = "Books"
                mock_niche1.filters = {"min_bsr": 1000}
                mock_niche1.last_score = 85.0
                mock_niche1.description = None
                mock_niche1.created_at = datetime.now()
                mock_niche1.updated_at = datetime.now()

                mock_niche2 = MagicMock()
                mock_niche2.id = "niche-2"
                mock_niche2.niche_name = "Niche 2"
                mock_niche2.user_id = "test-user-123"
                mock_niche2.category_id = 283155
                mock_niche2.category_name = "Books"
                mock_niche2.filters = {"min_bsr": 2000}
                mock_niche2.last_score = 90.0
                mock_niche2.description = None
                mock_niche2.created_at = datetime.now()
                mock_niche2.updated_at = datetime.now()

                mock_service.list_niches_by_user.return_value = ([mock_niche1, mock_niche2], 2)

                client = TestClient(app)
                response = client.get("/api/v1/bookmarks/niches")

                assert response.status_code == 200
                data = response.json()
                assert len(data["niches"]) == 2
                assert data["total_count"] == 2
                assert data["niches"][0]["id"] == "niche-1"
                assert data["niches"][1]["id"] == "niche-2"
        finally:
            app.dependency_overrides.clear()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
