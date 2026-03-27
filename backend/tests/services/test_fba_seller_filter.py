"""Tests for FBA seller count competition filter."""
from app.services.autosourcing_scoring import should_reject_by_competition


def test_reject_when_fba_sellers_exceeds_max():
    result = should_reject_by_competition(
        fba_seller_count=10,
        max_fba_sellers=5,
    )
    assert result is True


def test_accept_when_fba_sellers_within_max():
    result = should_reject_by_competition(
        fba_seller_count=4,
        max_fba_sellers=5,
    )
    assert result is False


def test_accept_when_fba_count_is_none():
    """If Keepa doesn't return the count, don't reject (incomplete data)."""
    result = should_reject_by_competition(
        fba_seller_count=None,
        max_fba_sellers=5,
    )
    assert result is False


def test_accept_when_max_fba_sellers_is_none():
    """If no max configured, no filter."""
    result = should_reject_by_competition(
        fba_seller_count=100,
        max_fba_sellers=None,
    )
    assert result is False


def test_reject_at_exact_boundary():
    """max=5: 5 sellers = OK, 6 = rejected."""
    assert should_reject_by_competition(5, 5) is False
    assert should_reject_by_competition(6, 5) is True
