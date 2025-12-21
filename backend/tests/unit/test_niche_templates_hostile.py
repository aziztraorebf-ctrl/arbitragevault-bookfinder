"""
Hostile Review Tests for niche_templates.py

Phase 6 Audit - Task 1: Validate structure and edge cases for CURATED_NICHES templates.
Tests verify template consistency, field validation, and strategy config sanity.
"""

import pytest
from app.services.niche_templates import (
    CURATED_NICHES,
    STRATEGY_CONFIGS,
    get_niche_template_by_id,
)


class TestNicheTemplatesValidation:
    """Hostile validation of CURATED_NICHES structure."""

    REQUIRED_FIELDS = [
        "id", "name", "description", "type", "categories",
        "bsr_range", "price_range", "min_margin", "max_fba_sellers",
        "min_roi", "min_velocity", "icon"
    ]

    def test_all_templates_have_required_fields(self):
        """Every template MUST have all required fields."""
        for tmpl in CURATED_NICHES:
            for field in self.REQUIRED_FIELDS:
                assert field in tmpl, f"Template {tmpl.get('id', 'UNKNOWN')} missing {field}"

    def test_template_ids_are_unique(self):
        """No duplicate template IDs allowed."""
        ids = [t["id"] for t in CURATED_NICHES]
        assert len(ids) == len(set(ids)), "Duplicate template IDs found"

    def test_bsr_range_valid(self):
        """BSR min must be < BSR max, both positive integers."""
        for tmpl in CURATED_NICHES:
            bsr_min, bsr_max = tmpl["bsr_range"]
            assert isinstance(bsr_min, int), f"{tmpl['id']}: BSR min must be int"
            assert isinstance(bsr_max, int), f"{tmpl['id']}: BSR max must be int"
            assert bsr_min > 0, f"{tmpl['id']}: BSR min must be > 0"
            assert bsr_max > bsr_min, f"{tmpl['id']}: BSR max must be > min"

    def test_price_range_valid(self):
        """Price min must be < Price max, both positive numbers."""
        for tmpl in CURATED_NICHES:
            price_min, price_max = tmpl["price_range"]
            assert price_min > 0, f"{tmpl['id']}: Price min must be > 0"
            assert price_max > price_min, f"{tmpl['id']}: Price max must be > min"

    def test_categories_not_empty(self):
        """Every template must have at least 1 category."""
        for tmpl in CURATED_NICHES:
            assert len(tmpl["categories"]) >= 1, f"{tmpl['id']}: Categories empty"
            assert all(isinstance(c, int) for c in tmpl["categories"]), \
                f"{tmpl['id']}: All categories must be integers"

    def test_type_matches_strategy_config(self):
        """Template type must exist in STRATEGY_CONFIGS."""
        for tmpl in CURATED_NICHES:
            assert tmpl["type"] in STRATEGY_CONFIGS, \
                f"{tmpl['id']}: Unknown type '{tmpl['type']}'"

    def test_margin_is_positive(self):
        """min_margin must be positive."""
        for tmpl in CURATED_NICHES:
            assert tmpl["min_margin"] > 0, f"{tmpl['id']}: min_margin must be > 0"

    def test_max_fba_sellers_reasonable(self):
        """max_fba_sellers must be between 1 and 10."""
        for tmpl in CURATED_NICHES:
            sellers = tmpl["max_fba_sellers"]
            assert 1 <= sellers <= 10, \
                f"{tmpl['id']}: max_fba_sellers {sellers} outside [1, 10]"


class TestGetNicheTemplateById:
    """Tests for get_niche_template_by_id function."""

    def test_returns_correct_template(self):
        """Should return exact template matching ID."""
        result = get_niche_template_by_id("tech-books-python")
        assert result is not None
        assert result["id"] == "tech-books-python"
        assert result["name"] == "[TECH] Python Books Beginners $20-50"

    def test_returns_none_for_unknown_id(self):
        """Should return None for non-existent ID."""
        result = get_niche_template_by_id("fake-template-xyz")
        assert result is None

    def test_returns_none_for_empty_string(self):
        """Should return None for empty string ID."""
        result = get_niche_template_by_id("")
        assert result is None

    def test_handles_none_input_gracefully(self):
        """Should handle None input - either return None or raise TypeError."""
        try:
            result = get_niche_template_by_id(None)
            # If it doesn't raise, it should return None
            assert result is None
        except TypeError:
            # Acceptable - function doesn't need to handle None
            pass


class TestStrategyConfigsConsistency:
    """Verify STRATEGY_CONFIGS values are sane."""

    def test_smart_velocity_thresholds(self):
        """Smart velocity should have reasonable thresholds."""
        config = STRATEGY_CONFIGS["smart_velocity"]
        assert config["min_margin"] >= 10.0, "Smart velocity margin too low"
        assert config["max_fba_sellers"] <= 10, "Max FBA sellers too high"
        assert config["bsr_range"][0] >= 1000, "BSR min too low for smart_velocity"
        assert config["bsr_range"][1] <= 100000, "BSR max too high for smart_velocity"

    def test_textbooks_thresholds(self):
        """Textbooks should have stricter margin thresholds."""
        config = STRATEGY_CONFIGS["textbooks"]
        assert config["min_margin"] >= 15.0, "Textbook margin too low"
        assert config["max_fba_sellers"] <= 5, "Textbook max FBA too high"
        assert config["bsr_range"][1] <= 500000, "BSR max too high for textbooks"

    def test_textbooks_stricter_competition_than_smart_velocity(self):
        """Textbooks should have stricter competition filter (fewer max FBA sellers)."""
        sv = STRATEGY_CONFIGS["smart_velocity"]
        tb = STRATEGY_CONFIGS["textbooks"]
        assert tb["max_fba_sellers"] < sv["max_fba_sellers"], \
            "Textbooks should have fewer max FBA sellers than smart_velocity"

    def test_textbooks_higher_margin_than_smart_velocity(self):
        """Textbooks should have higher min margin requirement."""
        sv = STRATEGY_CONFIGS["smart_velocity"]
        tb = STRATEGY_CONFIGS["textbooks"]
        assert tb["min_margin"] > sv["min_margin"], \
            "Textbooks should have higher min margin than smart_velocity"

    def test_strategy_configs_have_required_keys(self):
        """Each strategy config must have all required keys."""
        REQUIRED_KEYS = ["description", "bsr_range", "min_margin", "max_fba_sellers",
                         "price_range", "min_roi", "min_velocity"]
        for strategy_name, config in STRATEGY_CONFIGS.items():
            for key in REQUIRED_KEYS:
                assert key in config, f"Strategy {strategy_name} missing key {key}"


class TestTemplateTypeDistribution:
    """Verify template distribution across strategy types."""

    def test_has_smart_velocity_templates(self):
        """Should have at least 5 smart_velocity templates."""
        sv_count = sum(1 for t in CURATED_NICHES if t["type"] == "smart_velocity")
        assert sv_count >= 5, f"Only {sv_count} smart_velocity templates (expected >= 5)"

    def test_has_textbook_templates(self):
        """Should have at least 5 textbook templates."""
        tb_count = sum(1 for t in CURATED_NICHES if t["type"] == "textbooks")
        assert tb_count >= 5, f"Only {tb_count} textbook templates (expected >= 5)"

    def test_total_template_count(self):
        """Should have at least 10 total templates."""
        assert len(CURATED_NICHES) >= 10, f"Only {len(CURATED_NICHES)} templates (expected >= 10)"


class TestDualTemplateStrategy:
    """Tests for dual textbook template strategy (Standard + Patience).

    Phase 8: Implements PDF Golden Rule alignment with two specialized strategies:
    - textbooks_standard: BSR 100K-250K, FBA<=5, Profit $15+
    - textbooks_patience: BSR 250K-400K, FBA<=3, Profit $25+
    """

    def test_textbooks_standard_exists(self):
        """textbooks_standard strategy must exist in STRATEGY_CONFIGS."""
        assert "textbooks_standard" in STRATEGY_CONFIGS, \
            "Missing textbooks_standard in STRATEGY_CONFIGS"

    def test_textbooks_patience_exists(self):
        """textbooks_patience strategy must exist in STRATEGY_CONFIGS."""
        assert "textbooks_patience" in STRATEGY_CONFIGS, \
            "Missing textbooks_patience in STRATEGY_CONFIGS"

    def test_textbooks_standard_bsr_range(self):
        """Standard strategy: BSR 100K-250K (PDF Golden Rule)."""
        config = STRATEGY_CONFIGS["textbooks_standard"]
        bsr_min, bsr_max = config["bsr_range"]
        assert bsr_min == 100000, f"BSR min should be 100000, got {bsr_min}"
        assert bsr_max == 250000, f"BSR max should be 250000, got {bsr_max}"

    def test_textbooks_patience_bsr_range(self):
        """Patience strategy: BSR 250K-400K (under-the-radar)."""
        config = STRATEGY_CONFIGS["textbooks_patience"]
        bsr_min, bsr_max = config["bsr_range"]
        assert bsr_min == 250000, f"BSR min should be 250000, got {bsr_min}"
        assert bsr_max == 400000, f"BSR max should be 400000, got {bsr_max}"

    def test_textbooks_standard_margin(self):
        """Standard strategy: min margin $15."""
        config = STRATEGY_CONFIGS["textbooks_standard"]
        assert config["min_margin"] == 15.0, \
            f"min_margin should be 15.0, got {config['min_margin']}"

    def test_textbooks_patience_margin(self):
        """Patience strategy: min margin $25 (higher for slower rotation)."""
        config = STRATEGY_CONFIGS["textbooks_patience"]
        assert config["min_margin"] == 25.0, \
            f"min_margin should be 25.0, got {config['min_margin']}"

    def test_textbooks_standard_fba_sellers(self):
        """Standard strategy: max 5 FBA sellers."""
        config = STRATEGY_CONFIGS["textbooks_standard"]
        assert config["max_fba_sellers"] == 5, \
            f"max_fba_sellers should be 5, got {config['max_fba_sellers']}"

    def test_textbooks_patience_fba_sellers(self):
        """Patience strategy: max 3 FBA sellers (stricter)."""
        config = STRATEGY_CONFIGS["textbooks_patience"]
        assert config["max_fba_sellers"] == 3, \
            f"max_fba_sellers should be 3, got {config['max_fba_sellers']}"

    def test_textbooks_patience_has_warning(self):
        """Patience strategy MUST include rotation warning."""
        config = STRATEGY_CONFIGS["textbooks_patience"]
        assert "warning" in config, "textbooks_patience must have warning field"
        assert "4-6 semaines" in config["warning"], \
            f"Warning should mention 4-6 semaines, got: {config['warning']}"

    def test_patience_stricter_than_standard(self):
        """Patience must have stricter filters than Standard."""
        std = STRATEGY_CONFIGS["textbooks_standard"]
        pat = STRATEGY_CONFIGS["textbooks_patience"]

        # Patience: fewer FBA sellers allowed
        assert pat["max_fba_sellers"] < std["max_fba_sellers"], \
            "Patience should have fewer max_fba_sellers"

        # Patience: higher min margin required
        assert pat["min_margin"] > std["min_margin"], \
            "Patience should have higher min_margin"

    def test_standard_and_patience_price_ranges_aligned(self):
        """Both strategies should target same price range $40-$150."""
        std = STRATEGY_CONFIGS["textbooks_standard"]
        pat = STRATEGY_CONFIGS["textbooks_patience"]

        assert std["price_range"] == (40.0, 150.0), \
            f"Standard price range wrong: {std['price_range']}"
        assert pat["price_range"] == (40.0, 150.0), \
            f"Patience price range wrong: {pat['price_range']}"

    def test_bsr_ranges_are_contiguous(self):
        """Standard ends where Patience begins (250K)."""
        std = STRATEGY_CONFIGS["textbooks_standard"]
        pat = STRATEGY_CONFIGS["textbooks_patience"]

        assert std["bsr_range"][1] == pat["bsr_range"][0], \
            f"BSR ranges not contiguous: Standard ends at {std['bsr_range'][1]}, " \
            f"Patience starts at {pat['bsr_range'][0]}"

    def test_all_strategy_configs_have_required_keys(self):
        """Verify both new strategies have all required keys."""
        REQUIRED_KEYS = [
            "description", "bsr_range", "min_margin", "max_fba_sellers",
            "price_range", "min_roi", "min_velocity"
        ]

        for strategy_name in ["textbooks_standard", "textbooks_patience"]:
            config = STRATEGY_CONFIGS[strategy_name]
            for key in REQUIRED_KEYS:
                assert key in config, \
                    f"Strategy {strategy_name} missing required key: {key}"


class TestDualTemplateTemplates:
    """Tests for actual template entries using dual strategy types."""

    def test_standard_template_exists(self):
        """At least one template with type textbooks_standard must exist."""
        standard_templates = [t for t in CURATED_NICHES if t["type"] == "textbooks_standard"]
        assert len(standard_templates) >= 1, "No textbooks_standard templates found"

    def test_patience_template_exists(self):
        """At least one template with type textbooks_patience must exist."""
        patience_templates = [t for t in CURATED_NICHES if t["type"] == "textbooks_patience"]
        assert len(patience_templates) >= 1, "No textbooks_patience templates found"

    def test_standard_template_uses_correct_bsr(self):
        """Standard templates must use BSR 100K-250K."""
        for tmpl in CURATED_NICHES:
            if tmpl["type"] == "textbooks_standard":
                bsr_min, bsr_max = tmpl["bsr_range"]
                assert bsr_min == 100000, f"{tmpl['id']}: BSR min should be 100000"
                assert bsr_max == 250000, f"{tmpl['id']}: BSR max should be 250000"

    def test_patience_template_uses_correct_bsr(self):
        """Patience templates must use BSR 250K-400K."""
        for tmpl in CURATED_NICHES:
            if tmpl["type"] == "textbooks_patience":
                bsr_min, bsr_max = tmpl["bsr_range"]
                assert bsr_min == 250000, f"{tmpl['id']}: BSR min should be 250000"
                assert bsr_max == 400000, f"{tmpl['id']}: BSR max should be 400000"

    def test_standard_template_margin_is_15(self):
        """Standard templates must have min_margin $15."""
        for tmpl in CURATED_NICHES:
            if tmpl["type"] == "textbooks_standard":
                assert tmpl["min_margin"] == 15.0, \
                    f"{tmpl['id']}: min_margin should be 15.0"

    def test_patience_template_margin_is_25(self):
        """Patience templates must have min_margin $25."""
        for tmpl in CURATED_NICHES:
            if tmpl["type"] == "textbooks_patience":
                assert tmpl["min_margin"] == 25.0, \
                    f"{tmpl['id']}: min_margin should be 25.0"

    def test_standard_template_fba_sellers_is_5(self):
        """Standard templates: max 5 FBA sellers."""
        for tmpl in CURATED_NICHES:
            if tmpl["type"] == "textbooks_standard":
                assert tmpl["max_fba_sellers"] == 5, \
                    f"{tmpl['id']}: max_fba_sellers should be 5"

    def test_patience_template_fba_sellers_is_3(self):
        """Patience templates: max 3 FBA sellers (stricter)."""
        for tmpl in CURATED_NICHES:
            if tmpl["type"] == "textbooks_patience":
                assert tmpl["max_fba_sellers"] == 3, \
                    f"{tmpl['id']}: max_fba_sellers should be 3"

    def test_templates_price_range_is_40_150(self):
        """Both template types must use price range $40-$150."""
        for tmpl in CURATED_NICHES:
            if tmpl["type"] in ["textbooks_standard", "textbooks_patience"]:
                assert tmpl["price_range"] == (40.0, 150.0), \
                    f"{tmpl['id']}: price_range should be (40.0, 150.0)"


class TestLegacyTextbookTemplates:
    """Tests for legacy textbooks templates (backward compatibility)."""

    def test_legacy_textbooks_type_exists(self):
        """Legacy 'textbooks' strategy type still exists."""
        assert "textbooks" in STRATEGY_CONFIGS, \
            "Legacy textbooks strategy must exist for backward compatibility"

    def test_legacy_textbooks_templates_exist(self):
        """At least 5 templates with legacy 'textbooks' type."""
        legacy_count = sum(1 for t in CURATED_NICHES if t["type"] == "textbooks")
        assert legacy_count >= 5, f"Only {legacy_count} legacy textbook templates (expected >= 5)"

    def test_legacy_textbooks_bsr_range(self):
        """Legacy textbooks use BSR 30K-250K."""
        config = STRATEGY_CONFIGS["textbooks"]
        bsr_min, bsr_max = config["bsr_range"]
        assert bsr_min == 30000, f"Legacy BSR min should be 30000, got {bsr_min}"
        assert bsr_max == 250000, f"Legacy BSR max should be 250000, got {bsr_max}"

    def test_all_three_textbook_strategies_exist(self):
        """Verify all three textbook strategies are present."""
        expected = ["textbooks", "textbooks_standard", "textbooks_patience"]
        for strategy in expected:
            assert strategy in STRATEGY_CONFIGS, f"Missing strategy: {strategy}"
