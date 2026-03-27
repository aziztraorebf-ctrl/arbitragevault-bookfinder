"""
Tests for 2026 calibrated sourcing thresholds in business_rules.json.

Validates BSR limits, ROI minimums, profit floors, and max FBA sellers
per strategy after online model recalibration (March 2026).
"""
import json
import pathlib


def load_rules():
    path = pathlib.Path("config/business_rules.json")
    return json.loads(path.read_text())


def test_textbook_bsr_max_is_250k():
    rules = load_rules()
    assert rules["strategies"]["textbook"]["max_bsr"] == 250000


def test_velocity_bsr_max_is_75k():
    rules = load_rules()
    assert rules["strategies"]["velocity"]["max_bsr"] == 75000


def test_balanced_bsr_max_is_100k():
    rules = load_rules()
    assert rules["strategies"]["balanced"]["max_bsr"] == 100000


def test_textbook_roi_min_is_35():
    rules = load_rules()
    assert rules["strategies"]["textbook"]["roi_min"] == 35.0


def test_velocity_roi_min_is_30():
    rules = load_rules()
    assert rules["strategies"]["velocity"]["roi_min"] == 30.0


def test_textbook_min_profit_dollars():
    rules = load_rules()
    assert rules["strategies"]["textbook"]["min_profit_dollars"] == 12.0


def test_velocity_min_profit_dollars():
    rules = load_rules()
    assert rules["strategies"]["velocity"]["min_profit_dollars"] == 8.0


def test_textbook_max_fba_sellers():
    rules = load_rules()
    assert rules["strategies"]["textbook"]["max_fba_sellers"] == 8


def test_velocity_max_fba_sellers():
    rules = load_rules()
    assert rules["strategies"]["velocity"]["max_fba_sellers"] == 5


def test_balanced_max_fba_sellers():
    rules = load_rules()
    assert rules["strategies"]["balanced"]["max_fba_sellers"] == 6


def test_balanced_min_profit_dollars():
    rules = load_rules()
    assert rules["strategies"]["balanced"]["min_profit_dollars"] == 10.0
