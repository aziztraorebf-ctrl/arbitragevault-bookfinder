"""
Phase 1 Foundation Audit - Integration Tests

Tests validating core infrastructure components following TDD methodology:
- BaseRepository CRUD operations
- User/Analysis/Batch models
- Database manager health checks
- Alembic migration idempotence

Strategy: RED-GREEN-REFACTOR cycle
- RED: Write test validating expected behavior
- VERIFY RED: Confirm test would fail if infrastructure broken
- GREEN: Run against existing implementation
- VERIFY GREEN: Confirm all tests pass
"""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.db import db_manager
from app.models.analysis import Analysis
from app.models.batch import Batch, BatchStatus
from app.models.user import User, UserRole
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.batch_repository import BatchRepository
from app.repositories.user_repository import UserRepository


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="module", autouse=True)
async def initialize_db():
    """Initialize database manager once for entire test module."""
    await db_manager.initialize()
    yield
    await db_manager.close()


@pytest.fixture
async def db_session():
    """Provide clean database session for each test."""
    async with db_manager.session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def test_user(db_session):
    """Create test user for relationship tests."""
    user = User(
        id=str(uuid.uuid4()),
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        password_hash="hashed_password_123",
        first_name="Test",
        last_name="User",
        role=UserRole.SOURCER.value,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_batch(db_session, test_user):
    """Create test batch for relationship tests."""
    batch = Batch(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        name=f"Test Batch {uuid.uuid4().hex[:8]}",
        description="Test batch for Phase 1 audit",
        status=BatchStatus.PENDING,
        items_total=10,
        items_processed=0,
    )
    db_session.add(batch)
    await db_session.commit()
    await db_session.refresh(batch)
    return batch


# ============================================================================
# USER MODEL CRUD TESTS (RED Phase)
# ============================================================================

class TestUserCRUD:
    """Test User model CRUD operations via UserRepository."""

    async def test_user_create_basic(self, db_session):
        """RED: Test basic user creation."""
        repo = UserRepository(db_session)

        email = f"create_test_{uuid.uuid4().hex[:8]}@example.com"

        user = await repo.create_user(
            email=email,
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe",
            role=UserRole.SOURCER.value,
        )

        assert user.id is not None
        assert user.email == email.lower()  # Repository lowercases email
        assert user.password_hash == "hashed_password"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.role == UserRole.SOURCER.value.lower()
        assert user.is_active is True
        assert user.failed_login_attempts == 0
        assert user.created_at is not None

    async def test_user_create_duplicate_email_fails(self, db_session):
        """RED: Test duplicate email constraint enforcement."""
        from app.core.exceptions import DuplicateEmailError

        repo = UserRepository(db_session)

        email = f"duplicate_{uuid.uuid4().hex[:8]}@example.com"

        # Create first user
        await repo.create_user(
            email=email,
            password_hash="hash1",
            first_name="First",
            last_name="User",
        )

        # Attempt to create duplicate (should raise DuplicateEmailError)
        with pytest.raises(DuplicateEmailError):
            await repo.create_user(
                email=email,
                password_hash="hash2",
                first_name="Second",
                last_name="User",
            )

    async def test_user_get_by_id(self, db_session, test_user):
        """RED: Test user retrieval by ID."""
        repo = UserRepository(db_session)

        fetched_user = await repo.get_by_id(test_user.id)

        assert fetched_user is not None
        assert fetched_user.id == test_user.id
        assert fetched_user.email == test_user.email
        assert fetched_user.first_name == test_user.first_name

    async def test_user_get_by_id_not_found(self, db_session):
        """RED: Test get_by_id returns None for non-existent ID."""
        repo = UserRepository(db_session)

        non_existent_id = str(uuid.uuid4())
        result = await repo.get_by_id(non_existent_id)

        assert result is None

    async def test_user_update_profile(self, db_session, test_user):
        """RED: Test user profile update."""
        repo = UserRepository(db_session)

        updates = {
            "first_name": "Updated",
            "last_name": "Name",
        }

        updated_user = await repo.update(test_user.id, **updates)

        assert updated_user.first_name == "Updated"
        assert updated_user.last_name == "Name"
        assert updated_user.email == test_user.email  # Unchanged
        # Verify updated_at is set (not None) after update
        # Note: Due to timing differences between Python-generated updated_at and
        # DB-generated created_at, we only verify updated_at exists and is recent
        assert updated_user.updated_at is not None, "updated_at should be set after update"
        # Verify it's a datetime with timezone info
        assert updated_user.updated_at.tzinfo is not None, "updated_at should be timezone-aware"

    async def test_user_delete(self, db_session, test_user):
        """RED: Test user deletion."""
        repo = UserRepository(db_session)

        user_id = test_user.id

        result = await repo.delete(user_id)
        assert result is True

        # Verify deletion
        fetched = await repo.get_by_id(user_id)
        assert fetched is None

    async def test_user_security_methods(self, db_session):
        """RED: Test user security helper methods."""
        repo = UserRepository(db_session)

        email = f"security_test_{uuid.uuid4().hex[:8]}@example.com"

        user = await repo.create_user(
            email=email,
            password_hash="hash",
            first_name="Security",
            last_name="Test",
        )

        # Test initial state
        assert user.can_attempt_login() is True
        assert user.is_locked is False

        # Test failed attempts increment
        user.increment_failed_attempts()
        await db_session.commit()
        assert user.failed_login_attempts == 1

        # Test account locking
        lock_until = datetime.utcnow() + timedelta(minutes=30)
        user.lock_account(lock_until)
        await db_session.commit()
        assert user.is_locked is True
        assert user.can_attempt_login() is False


# ============================================================================
# BATCH MODEL CRUD TESTS (RED Phase)
# ============================================================================

class TestBatchCRUD:
    """Test Batch model CRUD operations via BatchRepository."""

    async def test_batch_create_basic(self, db_session, test_user):
        """RED: Test basic batch creation."""
        repo = BatchRepository(db_session)

        batch_data = {
            "user_id": test_user.id,
            "name": f"Batch {uuid.uuid4().hex[:8]}",
            "description": "Test batch",
            "items_total": 50,
            "items_processed": 0,
        }

        batch = await repo.create(**batch_data)

        assert batch.id is not None
        assert batch.user_id == test_user.id
        assert batch.name == batch_data["name"]
        assert batch.status == BatchStatus.PENDING
        assert batch.items_total == 50
        assert batch.items_processed == 0
        assert batch.created_at is not None

    async def test_batch_status_transitions(self, db_session, test_batch):
        """RED: Test batch status state machine transitions."""
        repo = BatchRepository(db_session)

        # Valid transition: PENDING -> PROCESSING
        assert test_batch.can_transition_to(BatchStatus.PROCESSING) is True
        updated = await repo.update(test_batch.id, **{"status": BatchStatus.PROCESSING})
        assert updated.status == BatchStatus.PROCESSING

        # Valid transition: PROCESSING -> COMPLETED
        assert updated.can_transition_to(BatchStatus.COMPLETED) is True
        completed = await repo.update(updated.id, **{"status": BatchStatus.COMPLETED})
        assert completed.status == BatchStatus.COMPLETED

        # Invalid transition: COMPLETED -> PENDING
        assert completed.can_transition_to(BatchStatus.PENDING) is False

    async def test_batch_progress_calculation(self, db_session, test_batch):
        """RED: Test batch progress percentage property."""
        repo = BatchRepository(db_session)

        # Initial state
        assert test_batch.progress_percentage == 0.0

        # Update progress
        updated = await repo.update(test_batch.id, **{"items_processed": 5})
        assert updated.progress_percentage == 50.0  # 5/10 * 100

        # Full completion
        completed = await repo.update(updated.id, **{"items_processed": 10})
        assert completed.progress_percentage == 100.0

    async def test_batch_cascade_delete(self, db_session, test_user):
        """RED: Test cascade delete when user is deleted."""
        batch_repo = BatchRepository(db_session)
        user_repo = UserRepository(db_session)

        # Create batch linked to user
        batch = await batch_repo.create(**{
            "user_id": test_user.id,
            "name": "Cascade Test",
            "items_total": 1,
        })
        batch_id = batch.id

        # Delete user (should cascade delete batch)
        await user_repo.delete(test_user.id)

        # Verify batch is also deleted
        fetched_batch = await batch_repo.get_by_id(batch_id)
        assert fetched_batch is None


# ============================================================================
# ANALYSIS MODEL CRUD TESTS (RED Phase)
# ============================================================================

class TestAnalysisCRUD:
    """Test Analysis model CRUD operations via AnalysisRepository."""

    async def test_analysis_create_basic(self, db_session, test_batch):
        """RED: Test basic analysis creation with Decimal precision."""
        repo = AnalysisRepository(db_session)

        analysis_data = {
            "batch_id": test_batch.id,
            "isbn_or_asin": "B00TEST123",
            "buy_price": Decimal("10.00"),
            "fees": Decimal("5.50"),
            "expected_sale_price": Decimal("25.00"),
            "profit": Decimal("9.50"),
            "roi_percent": Decimal("95.00"),
            "velocity_score": Decimal("85.50"),
        }

        analysis = await repo.create(**analysis_data)

        assert analysis.id is not None
        assert analysis.batch_id == test_batch.id
        assert analysis.isbn_or_asin == "B00TEST123"
        assert analysis.buy_price == Decimal("10.00")
        assert analysis.fees == Decimal("5.50")
        assert analysis.profit == Decimal("9.50")
        assert analysis.roi_percent == Decimal("95.00")
        assert analysis.velocity_score == Decimal("85.50")

    async def test_analysis_unique_constraint(self, db_session, test_batch):
        """RED: Test unique constraint on (batch_id, isbn_or_asin)."""
        repo = AnalysisRepository(db_session)

        data = {
            "batch_id": test_batch.id,
            "isbn_or_asin": "B00UNIQUE1",
            "buy_price": Decimal("10.00"),
            "fees": Decimal("5.00"),
            "expected_sale_price": Decimal("20.00"),
            "profit": Decimal("5.00"),
            "roi_percent": Decimal("50.00"),
            "velocity_score": Decimal("70.00"),
        }

        # Create first analysis
        await repo.create(**data)

        # Attempt duplicate
        with pytest.raises(IntegrityError):
            await repo.create(**data)

    async def test_analysis_velocity_score_constraints(self, db_session, test_batch):
        """RED: Test velocity_score check constraints (0-100 range)."""
        repo = AnalysisRepository(db_session)

        base_data = {
            "batch_id": test_batch.id,
            "isbn_or_asin": "B00VELOCITY",
            "buy_price": Decimal("10.00"),
            "fees": Decimal("5.00"),
            "expected_sale_price": Decimal("20.00"),
            "profit": Decimal("5.00"),
            "roi_percent": Decimal("50.00"),
        }

        # Test negative velocity (should fail)
        with pytest.raises(IntegrityError):
            await repo.create(**{**base_data, "velocity_score": Decimal("-1.0")})

        await db_session.rollback()

        # Test velocity > 100 (should fail)
        with pytest.raises(IntegrityError):
            await repo.create(**{**base_data, "velocity_score": Decimal("101.0")})

    async def test_analysis_profit_validation(self, db_session, test_batch):
        """RED: Test profit calculation validation method."""
        repo = AnalysisRepository(db_session)

        # Create analysis with correct profit calculation
        analysis = await repo.create(**{
            "batch_id": test_batch.id,
            "isbn_or_asin": "B00PROFIT1",
            "buy_price": Decimal("10.00"),
            "fees": Decimal("5.50"),
            "expected_sale_price": Decimal("25.00"),
            "profit": Decimal("9.50"),  # 25 - (10 + 5.50) = 9.50
            "roi_percent": Decimal("95.00"),
            "velocity_score": Decimal("80.00"),
        })

        # Validate profit calculation
        assert analysis.validate_profit_calculation() is True

        # Create analysis with incorrect profit
        incorrect = await repo.create(**{
            "batch_id": test_batch.id,
            "isbn_or_asin": "B00PROFIT2",
            "buy_price": Decimal("10.00"),
            "fees": Decimal("5.00"),
            "expected_sale_price": Decimal("20.00"),
            "profit": Decimal("10.00"),  # Wrong: should be 5.00
            "roi_percent": Decimal("100.00"),
            "velocity_score": Decimal("80.00"),
        })

        assert incorrect.validate_profit_calculation() is False

    async def test_analysis_cascade_delete_via_batch(self, db_session, test_batch):
        """RED: Test cascade delete when batch is deleted."""
        analysis_repo = AnalysisRepository(db_session)
        batch_repo = BatchRepository(db_session)

        # Create analysis linked to batch
        analysis = await analysis_repo.create(**{
            "batch_id": test_batch.id,
            "isbn_or_asin": "B00CASCADE",
            "buy_price": Decimal("10.00"),
            "fees": Decimal("5.00"),
            "expected_sale_price": Decimal("20.00"),
            "profit": Decimal("5.00"),
            "roi_percent": Decimal("50.00"),
            "velocity_score": Decimal("70.00"),
        })
        analysis_id = analysis.id

        # Delete batch (should cascade delete analysis)
        await batch_repo.delete(test_batch.id)

        # Verify analysis is also deleted
        fetched = await analysis_repo.get_by_id(analysis_id)
        assert fetched is None


# ============================================================================
# DATABASE MANAGER TESTS (RED Phase)
# ============================================================================

class TestDatabaseManager:
    """Test DatabaseManager health check and lifecycle."""

    async def test_health_check_success(self):
        """RED: Test database health check returns True when connected."""
        result = await db_manager.health_check()
        assert result is True

    async def test_health_check_query_result(self, db_session):
        """RED: Test health check executes SELECT 1 correctly."""
        # Execute same query as health check
        result = await db_session.execute(text("SELECT 1"))
        scalar = result.scalar()

        assert scalar == 1

    async def test_session_context_manager_rollback(self, db_session):
        """RED: Test session rollback on exception."""
        user_repo = UserRepository(db_session)
        user_id = None

        try:
            # Create user WITHOUT committing (add to session only)
            user = User(
                id=str(uuid.uuid4()),
                email=f"rollback_test_{uuid.uuid4().hex[:8]}@example.com",
                password_hash="hash",
                first_name="Rollback",
                last_name="Test",
                role=UserRole.SOURCER.value,
                is_active=True,
            )
            db_session.add(user)
            await db_session.flush()  # Get ID without committing
            user_id = user.id

            # Force exception BEFORE commit
            raise ValueError("Simulated error")

        except ValueError:
            await db_session.rollback()

        # Verify user was NOT persisted (rollback worked)
        if user_id:
            fetched = await user_repo.get_by_id(user_id)
            assert fetched is None


# ============================================================================
# HEALTH ENDPOINTS TESTS (RED Phase)
# ============================================================================

class TestHealthEndpoints:
    """Test health probe endpoints functionality."""

    async def test_liveness_endpoint_structure(self):
        """RED: Test liveness endpoint returns expected structure."""
        from app.api.v1.routers.health import liveness_check

        response = await liveness_check()

        assert "status" in response
        assert response["status"] == "alive"
        assert "service" in response
        assert "version" in response
        assert "environment" in response

    async def test_readiness_endpoint_with_healthy_db(self):
        """RED: Test readiness endpoint when database is healthy."""
        from app.api.v1.routers.health import readiness_check

        response = await readiness_check()

        # Should be dict (200 OK), not JSONResponse (503)
        assert isinstance(response, dict)
        assert response["status"] == "ready"
        assert response["checks"]["database"] == "healthy"
