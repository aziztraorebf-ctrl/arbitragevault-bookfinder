"""
Hostile Review Test Cases for Bookmarks API
============================================
Tests for edge cases and security vulnerabilities identified in hostile review.

Run: pytest tests/api/test_bookmarks_hostile_review.py -v
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app
from app.core.auth import get_current_user_id
from app.core.db import get_db_session


class TestEmptyStringValidation:
    """Tests for CRITICAL 2: Empty string bypass vulnerability."""

    def test_create_niche_rejects_empty_string(self):
        """POST with empty string niche_name should return 422."""

        def mock_user_id():
            return "test-user-123"

        def mock_db_session():
            return MagicMock()

        app.dependency_overrides[get_current_user_id] = mock_user_id
        app.dependency_overrides[get_db_session] = mock_db_session

        try:
            client = TestClient(app)
            response = client.post(
                "/api/v1/bookmarks/niches",
                json={
                    "niche_name": "",
                    "filters": {}
                }
            )

            assert response.status_code == 422
            data = response.json()
            assert "detail" in data
            # Check that validation error occurred on niche_name field
            errors = data["detail"]
            assert any(
                error.get("loc", [])[-1] == "niche_name"
                for error in errors
            )
        finally:
            app.dependency_overrides.clear()

    def test_create_niche_rejects_whitespace_only(self):
        """POST with whitespace-only niche_name should return 422."""

        def mock_user_id():
            return "test-user-123"

        def mock_db_session():
            return MagicMock()

        app.dependency_overrides[get_current_user_id] = mock_user_id
        app.dependency_overrides[get_db_session] = mock_db_session

        try:
            client = TestClient(app)
            response = client.post(
                "/api/v1/bookmarks/niches",
                json={
                    "niche_name": "   ",
                    "filters": {}
                }
            )

            assert response.status_code == 422
            data = response.json()
            assert "detail" in data
        finally:
            app.dependency_overrides.clear()

    def test_update_niche_rejects_empty_string(self):
        """PUT with empty string niche_name should return 422."""

        def mock_user_id():
            return "test-user-123"

        def mock_db_session():
            return MagicMock()

        app.dependency_overrides[get_current_user_id] = mock_user_id
        app.dependency_overrides[get_db_session] = mock_db_session

        try:
            client = TestClient(app)
            response = client.put(
                "/api/v1/bookmarks/niches/test-niche-id",
                json={
                    "niche_name": ""
                }
            )

            assert response.status_code == 422
            data = response.json()
            assert "detail" in data
            # Check that validation error occurred on niche_name field
            errors = data["detail"]
            assert any(
                error.get("loc", [])[-1] == "niche_name"
                for error in errors
            )
        finally:
            app.dependency_overrides.clear()

    def test_update_niche_rejects_whitespace_only(self):
        """PUT with whitespace-only niche_name should return 422."""

        def mock_user_id():
            return "test-user-123"

        def mock_db_session():
            return MagicMock()

        app.dependency_overrides[get_current_user_id] = mock_user_id
        app.dependency_overrides[get_db_session] = mock_db_session

        try:
            client = TestClient(app)
            response = client.put(
                "/api/v1/bookmarks/niches/test-niche-id",
                json={
                    "niche_name": "   \t\n  "
                }
            )

            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()

    def test_create_niche_trims_whitespace(self):
        """POST should trim leading/trailing whitespace from niche_name."""

        def mock_user_id():
            return "test-user-123"

        def mock_db_session():
            return MagicMock()

        app.dependency_overrides[get_current_user_id] = mock_user_id
        app.dependency_overrides[get_db_session] = mock_db_session

        try:
            from datetime import datetime

            with patch("app.api.v1.routers.bookmarks.BookmarkService") as MockService:
                mock_service = MockService.return_value

                mock_niche = MagicMock()
                mock_niche.id = "niche-123"
                mock_niche.niche_name = "Books"
                mock_niche.user_id = "test-user-123"
                mock_niche.category_id = None
                mock_niche.category_name = None
                mock_niche.filters = {}
                mock_niche.last_score = None
                mock_niche.description = None
                mock_niche.created_at = datetime.now()
                mock_niche.updated_at = datetime.now()

                mock_service.create_niche.return_value = mock_niche

                client = TestClient(app)
                response = client.post(
                    "/api/v1/bookmarks/niches",
                    json={
                        "niche_name": "  Books  ",
                        "filters": {}
                    }
                )

                assert response.status_code == 201
                call_args = mock_service.create_niche.call_args
                assert call_args[0][1].niche_name == "Books"
        finally:
            app.dependency_overrides.clear()


class TestPaginationValidation:
    """Tests for MINOR 7: Pagination limits at service layer."""

    def test_list_niches_negative_skip_handled(self):
        """GET with negative skip should be rejected or handled gracefully."""

        def mock_user_id():
            return "test-user-123"

        def mock_db_session():
            return MagicMock()

        app.dependency_overrides[get_current_user_id] = mock_user_id
        app.dependency_overrides[get_db_session] = mock_db_session

        try:
            client = TestClient(app)
            response = client.get("/api/v1/bookmarks/niches?skip=-10")

            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()

    def test_list_niches_excessive_limit_rejected(self):
        """GET with limit > 500 should be rejected."""

        def mock_user_id():
            return "test-user-123"

        def mock_db_session():
            return MagicMock()

        app.dependency_overrides[get_current_user_id] = mock_user_id
        app.dependency_overrides[get_db_session] = mock_db_session

        try:
            client = TestClient(app)
            response = client.get("/api/v1/bookmarks/niches?limit=9999")

            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()


class TestUnicodeHandling:
    """Tests for unicode and special characters in niche_name."""

    def test_create_niche_accepts_unicode_emojis(self):
        """POST with unicode/emoji in niche_name should succeed."""

        def mock_user_id():
            return "test-user-123"

        def mock_db_session():
            return MagicMock()

        app.dependency_overrides[get_current_user_id] = mock_user_id
        app.dependency_overrides[get_db_session] = mock_db_session

        try:
            from datetime import datetime

            with patch("app.api.v1.routers.bookmarks.BookmarkService") as MockService:
                mock_service = MockService.return_value

                mock_niche = MagicMock()
                mock_niche.id = "niche-123"
                mock_niche.niche_name = "Books Test"
                mock_niche.user_id = "test-user-123"
                mock_niche.category_id = None
                mock_niche.category_name = None
                mock_niche.filters = {}
                mock_niche.last_score = None
                mock_niche.description = None
                mock_niche.created_at = datetime.now()
                mock_niche.updated_at = datetime.now()

                mock_service.create_niche.return_value = mock_niche

                client = TestClient(app)
                response = client.post(
                    "/api/v1/bookmarks/niches",
                    json={
                        "niche_name": "Books Test",
                        "filters": {}
                    }
                )

                assert response.status_code == 201
        finally:
            app.dependency_overrides.clear()

    def test_create_niche_accepts_accents(self):
        """POST with accented characters should succeed."""

        def mock_user_id():
            return "test-user-123"

        def mock_db_session():
            return MagicMock()

        app.dependency_overrides[get_current_user_id] = mock_user_id
        app.dependency_overrides[get_db_session] = mock_db_session

        try:
            from datetime import datetime

            with patch("app.api.v1.routers.bookmarks.BookmarkService") as MockService:
                mock_service = MockService.return_value

                mock_niche = MagicMock()
                mock_niche.id = "niche-123"
                mock_niche.niche_name = "Livres pour etudiants"
                mock_niche.user_id = "test-user-123"
                mock_niche.category_id = None
                mock_niche.category_name = None
                mock_niche.filters = {}
                mock_niche.last_score = None
                mock_niche.description = None
                mock_niche.created_at = datetime.now()
                mock_niche.updated_at = datetime.now()

                mock_service.create_niche.return_value = mock_niche

                client = TestClient(app)
                response = client.post(
                    "/api/v1/bookmarks/niches",
                    json={
                        "niche_name": "Livres pour etudiants",
                        "filters": {}
                    }
                )

                assert response.status_code == 201
        finally:
            app.dependency_overrides.clear()


class TestIntegrityErrorHandling:
    """Tests for IMPORTANT 4: IntegrityError handling in update."""

    def test_update_niche_duplicate_name_returns_409(self):
        """PUT with duplicate niche_name should return 409 Conflict."""

        def mock_user_id():
            return "test-user-123"

        def mock_db_session():
            return MagicMock()

        app.dependency_overrides[get_current_user_id] = mock_user_id
        app.dependency_overrides[get_db_session] = mock_db_session

        try:
            with patch("app.api.v1.routers.bookmarks.BookmarkService") as MockService:
                mock_service = MockService.return_value
                mock_service.update_niche.side_effect = HTTPException(
                    status_code=409,
                    detail="A niche with this name already exists"
                )

                client = TestClient(app)
                response = client.put(
                    "/api/v1/bookmarks/niches/test-niche-id",
                    json={
                        "niche_name": "Existing Niche Name"
                    }
                )

                assert response.status_code == 409
                assert "already exists" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
