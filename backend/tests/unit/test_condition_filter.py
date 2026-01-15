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


class TestGroupOffersByConditionFilter:
    """Test _group_offers_by_condition with condition_filter parameter."""

    def test_group_offers_by_condition_with_filter(self):
        """Test filtering offers by condition."""
        from app.services.keepa_parser_v2 import _group_offers_by_condition
        from app.services.keepa_constants import DEFAULT_CONDITIONS

        # Mock offers with all 4 conditions
        mock_offers = [
            {'condition': 1, 'offerCSV': [[[0, 1000, 0]]], 'sellerId': 'A1', 'isFBA': True},  # new
            {'condition': 3, 'offerCSV': [[[0, 800, 0]]], 'sellerId': 'A2', 'isFBA': True},   # very_good
            {'condition': 4, 'offerCSV': [[[0, 600, 0]]], 'sellerId': 'A3', 'isFBA': False},  # good
            {'condition': 5, 'offerCSV': [[[0, 400, 0]]], 'sellerId': 'A4', 'isFBA': False},  # acceptable
        ]

        # With DEFAULT_CONDITIONS filter, should exclude 'acceptable'
        result = _group_offers_by_condition(mock_offers, condition_filter=DEFAULT_CONDITIONS)

        assert 'new' in result
        assert 'very_good' in result
        assert 'good' in result
        assert 'acceptable' not in result  # Should be excluded

    def test_group_offers_by_condition_without_filter(self):
        """Test that without filter, all conditions are included."""
        from app.services.keepa_parser_v2 import _group_offers_by_condition

        mock_offers = [
            {'condition': 1, 'offerCSV': [[[0, 1000, 0]]], 'sellerId': 'A1', 'isFBA': True},
            {'condition': 5, 'offerCSV': [[[0, 400, 0]]], 'sellerId': 'A4', 'isFBA': False},
        ]

        # Without filter, all conditions should be included
        result = _group_offers_by_condition(mock_offers, condition_filter=None)

        assert 'new' in result
        assert 'acceptable' in result

    def test_group_offers_by_condition_backward_compatible(self):
        """Test that function works without condition_filter argument (backward compatible)."""
        from app.services.keepa_parser_v2 import _group_offers_by_condition

        mock_offers = [
            {'condition': 1, 'offerCSV': [[[0, 1000, 0]]], 'sellerId': 'A1', 'isFBA': True},
            {'condition': 5, 'offerCSV': [[[0, 400, 0]]], 'sellerId': 'A4', 'isFBA': False},
        ]

        # Call without condition_filter argument at all (backward compatibility)
        result = _group_offers_by_condition(mock_offers)

        # Should return all conditions found
        assert 'new' in result
        assert 'acceptable' in result

    def test_group_offers_by_condition_custom_filter(self):
        """Test with custom filter list."""
        from app.services.keepa_parser_v2 import _group_offers_by_condition

        mock_offers = [
            {'condition': 1, 'offerCSV': [[[0, 1000, 0]]], 'sellerId': 'A1', 'isFBA': True},   # new
            {'condition': 3, 'offerCSV': [[[0, 800, 0]]], 'sellerId': 'A2', 'isFBA': True},    # very_good
            {'condition': 4, 'offerCSV': [[[0, 600, 0]]], 'sellerId': 'A3', 'isFBA': False},   # good
            {'condition': 5, 'offerCSV': [[[0, 400, 0]]], 'sellerId': 'A4', 'isFBA': False},   # acceptable
        ]

        # Only include 'new' and 'acceptable'
        result = _group_offers_by_condition(mock_offers, condition_filter=['new', 'acceptable'])

        assert 'new' in result
        assert 'acceptable' in result
        assert 'very_good' not in result
        assert 'good' not in result


class TestParseKeepaProductUnifiedFilter:
    """Tests for condition_filter in parse_keepa_product_unified."""

    def test_parse_keepa_product_unified_with_condition_filter(self):
        """Test that condition_filter is passed through to offers grouping."""
        from app.services.keepa_parser_v2 import parse_keepa_product_unified
        from app.services.keepa_constants import DEFAULT_CONDITIONS

        # Mock Keepa data with offers in all conditions
        mock_keepa = {
            'asin': 'B00TEST123',
            'title': 'Test Product',
            'offers': [
                {'condition': 1, 'offerCSV': [[[0, 1000, 0]]], 'sellerId': 'A1', 'isFBA': True},  # new
                {'condition': 3, 'offerCSV': [[[0, 800, 0]]], 'sellerId': 'A2', 'isFBA': True},   # very_good
                {'condition': 4, 'offerCSV': [[[0, 600, 0]]], 'sellerId': 'A3', 'isFBA': False},  # good
                {'condition': 5, 'offerCSV': [[[0, 400, 0]]], 'sellerId': 'A4', 'isFBA': False},  # acceptable
            ],
            'stats': {'current': [None] * 20}
        }

        # With filter, acceptable should be excluded
        result = parse_keepa_product_unified(mock_keepa, condition_filter=DEFAULT_CONDITIONS)

        offers = result.get('offers_by_condition', {})
        assert 'new' in offers
        assert 'very_good' in offers
        assert 'good' in offers
        assert 'acceptable' not in offers

    def test_parse_keepa_product_unified_without_filter(self):
        """Test backward compatibility - no filter includes all."""
        from app.services.keepa_parser_v2 import parse_keepa_product_unified

        mock_keepa = {
            'asin': 'B00TEST456',
            'title': 'Test Product 2',
            'offers': [
                {'condition': 1, 'offerCSV': [[[0, 1000, 0]]], 'sellerId': 'A1', 'isFBA': True},
                {'condition': 5, 'offerCSV': [[[0, 400, 0]]], 'sellerId': 'A4', 'isFBA': False},
            ],
            'stats': {'current': [None] * 20}
        }

        # Without filter, all conditions included
        result = parse_keepa_product_unified(mock_keepa)

        offers = result.get('offers_by_condition', {})
        assert 'new' in offers
        assert 'acceptable' in offers
