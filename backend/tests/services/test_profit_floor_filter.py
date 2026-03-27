"""Tests for profit floor filter."""
from app.services.autosourcing_scoring import should_reject_by_profit_floor


def test_reject_when_profit_below_floor():
    assert should_reject_by_profit_floor(profit_net=5.0, min_profit_dollars=8.0) is True


def test_accept_when_profit_above_floor():
    assert should_reject_by_profit_floor(profit_net=10.0, min_profit_dollars=8.0) is False


def test_accept_at_exact_floor():
    assert should_reject_by_profit_floor(profit_net=8.0, min_profit_dollars=8.0) is False


def test_accept_when_no_floor_configured():
    assert should_reject_by_profit_floor(profit_net=1.0, min_profit_dollars=None) is False


def test_accept_when_profit_is_none():
    """Incomplete data should not reject."""
    assert should_reject_by_profit_floor(profit_net=None, min_profit_dollars=8.0) is False
