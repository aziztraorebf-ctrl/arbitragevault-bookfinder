"""Unit tests for condition filtering functionality."""

import pytest


class TestConditionFilterConstants:
    """Test condition filter constants and defaults."""

    def test_default_conditions_excludes_acceptable(self):
        """Default conditions should exclude 'acceptable'."""
        from app.services.keepa_constants import DEFAULT_CONDITIONS

        assert 'acceptable' not in DEFAULT_CONDITIONS
        assert 'new' in DEFAULT_CONDITIONS
        assert 'very_good' in DEFAULT_CONDITIONS
        assert 'good' in DEFAULT_CONDITIONS

    def test_all_condition_keys_defined(self):
        """All condition keys should be defined in KEEPA_CONDITION_CODES."""
        from app.services.keepa_constants import KEEPA_CONDITION_CODES, ALL_CONDITION_KEYS

        for key in ALL_CONDITION_KEYS:
            assert key in [code[0] for code in KEEPA_CONDITION_CODES.values()]
