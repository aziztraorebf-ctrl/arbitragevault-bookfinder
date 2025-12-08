"""
Unit tests for AutoSourcingService._meets_criteria method.
Validates velocity_min filtering behavior.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from app.services.autosourcing_service import AutoSourcingService
from app.models.autosourcing import AutoSourcingPick


class TestMeetsCriteria:
    """Test _meets_criteria velocity filtering."""

    @pytest.fixture
    def service(self):
        """Create AutoSourcingService with mocked dependencies."""
        mock_db = MagicMock()
        mock_keepa = AsyncMock()
        return AutoSourcingService(db_session=mock_db, keepa_service=mock_keepa)

    @pytest.fixture
    def create_pick(self):
        """Factory for creating test picks."""
        def _create(velocity_score: int, roi_percentage: float, overall_rating: str):
            pick = MagicMock(spec=AutoSourcingPick)
            pick.velocity_score = velocity_score
            pick.roi_percentage = roi_percentage
            pick.overall_rating = overall_rating
            return pick
        return _create

    def test_velocity_49_rejected_when_threshold_50(self, service, create_pick):
        """Pick with velocity 49 should be rejected when velocity_min is 50."""
        pick = create_pick(velocity_score=49, roi_percentage=35.0, overall_rating="GOOD")
        config = {"velocity_min": 50, "roi_min": 20, "rating_required": "FAIR"}

        result = service._meets_criteria(pick, config)

        assert result is False, "Velocity 49 should be rejected when threshold is 50"

    def test_velocity_50_accepted_when_threshold_50(self, service, create_pick):
        """Pick with velocity 50 should be accepted when velocity_min is 50."""
        pick = create_pick(velocity_score=50, roi_percentage=35.0, overall_rating="GOOD")
        config = {"velocity_min": 50, "roi_min": 20, "rating_required": "FAIR"}

        result = service._meets_criteria(pick, config)

        assert result is True, "Velocity 50 should be accepted when threshold is 50"

    def test_velocity_80_accepted_when_threshold_50(self, service, create_pick):
        """Pick with velocity 80 should be accepted when velocity_min is 50."""
        pick = create_pick(velocity_score=80, roi_percentage=35.0, overall_rating="GOOD")
        config = {"velocity_min": 50, "roi_min": 20, "rating_required": "FAIR"}

        result = service._meets_criteria(pick, config)

        assert result is True, "Velocity 80 should be accepted when threshold is 50"

    def test_velocity_check_skipped_when_threshold_zero(self, service, create_pick):
        """Velocity check should be skipped when velocity_min is 0."""
        pick = create_pick(velocity_score=10, roi_percentage=35.0, overall_rating="GOOD")
        config = {"velocity_min": 0, "roi_min": 20, "rating_required": "FAIR"}

        result = service._meets_criteria(pick, config)

        assert result is True, "Low velocity should be accepted when velocity_min is 0"

    def test_velocity_check_skipped_when_threshold_not_set(self, service, create_pick):
        """Velocity check should be skipped when velocity_min is not in config."""
        pick = create_pick(velocity_score=10, roi_percentage=35.0, overall_rating="GOOD")
        config = {"roi_min": 20, "rating_required": "FAIR"}

        result = service._meets_criteria(pick, config)

        assert result is True, "Low velocity should be accepted when velocity_min not configured"

    def test_roi_still_checked_after_velocity_passes(self, service, create_pick):
        """ROI check should still be enforced after velocity passes."""
        pick = create_pick(velocity_score=60, roi_percentage=15.0, overall_rating="GOOD")
        config = {"velocity_min": 50, "roi_min": 20, "rating_required": "FAIR"}

        result = service._meets_criteria(pick, config)

        assert result is False, "Should be rejected due to low ROI even with good velocity"

    def test_rating_still_checked_after_velocity_passes(self, service, create_pick):
        """Rating check should still be enforced after velocity passes."""
        pick = create_pick(velocity_score=60, roi_percentage=35.0, overall_rating="PASS")
        config = {"velocity_min": 50, "roi_min": 20, "rating_required": "GOOD"}

        result = service._meets_criteria(pick, config)

        assert result is False, "Should be rejected due to low rating even with good velocity"

    def test_smart_velocity_strategy_config(self, service, create_pick):
        """Test with Smart Velocity strategy config (velocity_min=50)."""
        smart_velocity_config = {
            "velocity_min": 50,
            "roi_min": 30,
            "rating_required": "FAIR"
        }

        # Should pass: velocity=55, ROI=35%, rating=GOOD
        good_pick = create_pick(velocity_score=55, roi_percentage=35.0, overall_rating="GOOD")
        assert service._meets_criteria(good_pick, smart_velocity_config) is True

        # Should fail: velocity=49 (below threshold)
        low_velocity_pick = create_pick(velocity_score=49, roi_percentage=35.0, overall_rating="GOOD")
        assert service._meets_criteria(low_velocity_pick, smart_velocity_config) is False

    def test_textbooks_strategy_config(self, service, create_pick):
        """Test with Textbooks strategy config (velocity_min=30)."""
        textbooks_config = {
            "velocity_min": 30,
            "roi_min": 50,
            "rating_required": "FAIR"
        }

        # Should pass: velocity=35, ROI=55%, rating=GOOD
        good_pick = create_pick(velocity_score=35, roi_percentage=55.0, overall_rating="GOOD")
        assert service._meets_criteria(good_pick, textbooks_config) is True

        # Should fail: velocity=25 (below threshold)
        low_velocity_pick = create_pick(velocity_score=25, roi_percentage=55.0, overall_rating="GOOD")
        assert service._meets_criteria(low_velocity_pick, textbooks_config) is False

        # Should fail: ROI=45% (below threshold)
        low_roi_pick = create_pick(velocity_score=35, roi_percentage=45.0, overall_rating="GOOD")
        assert service._meets_criteria(low_roi_pick, textbooks_config) is False
