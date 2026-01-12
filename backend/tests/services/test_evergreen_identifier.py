"""
Unit tests for Evergreen Identifier Service.

TDD: These tests are written FIRST before implementation.
Tests the evergreen book identification logic for stable year-round income.
"""
import pytest
from typing import Dict, Any

# Import will fail until service is implemented - expected for TDD
from app.services.evergreen_identifier_service import (
    EvergreenClassification,
    identify_evergreen,
    get_evergreen_portfolio_targets,
    EVERGREEN_KEYWORDS,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def nursing_textbook_data() -> Dict[str, Any]:
    """
    NCLEX nursing prep book - classic evergreen product.
    High keyword matches + stable metrics.
    """
    return {
        "title": "Saunders Comprehensive Review for the NCLEX-RN Examination",
        "category": "Nursing",
        "bsr": 35000,
        "avg_price_12m": 49.99,
        "price_volatility": 0.12,
        "sales_per_month": 25.0,
    }


@pytest.fixture
def programming_book_data() -> Dict[str, Any]:
    """
    Clean Code classic - evergreen programming reference.
    """
    return {
        "title": "Clean Code: A Handbook of Agile Software Craftsmanship",
        "category": "Computer Science",
        "bsr": 8500,
        "avg_price_12m": 34.99,
        "price_volatility": 0.08,
        "sales_per_month": 45.0,
    }


@pytest.fixture
def seasonal_textbook_data() -> Dict[str, Any]:
    """
    Generic college textbook with high volatility - NOT evergreen.
    """
    return {
        "title": "Introduction to Biology 14th Edition Fall 2025",
        "category": "Textbooks",
        "bsr": 250000,
        "avg_price_12m": 89.99,
        "price_volatility": 0.45,
        "sales_per_month": 3.0,
    }


@pytest.fixture
def language_learning_book_data() -> Dict[str, Any]:
    """
    Spanish learning book - skill-based evergreen.
    """
    return {
        "title": "Practice Makes Perfect: Complete Spanish Grammar",
        "category": "Language Learning",
        "bsr": 12000,
        "avg_price_12m": 18.99,
        "price_volatility": 0.10,
        "sales_per_month": 30.0,
    }


@pytest.fixture
def reference_book_data() -> Dict[str, Any]:
    """
    Dictionary/Reference book - evergreen reference type.
    """
    return {
        "title": "Merriam-Webster's Collegiate Dictionary",
        "category": "Reference",
        "bsr": 5000,
        "avg_price_12m": 24.99,
        "price_volatility": 0.05,
        "sales_per_month": 60.0,
    }


@pytest.fixture
def borderline_volatility_data() -> Dict[str, Any]:
    """
    Book with volatility right at the boundary (0.29).
    Should still be evergreen if other factors are strong.
    """
    return {
        "title": "MCAT Prep Plus 2025-2026",
        "category": "Test Preparation",
        "bsr": 45000,
        "avg_price_12m": 69.99,
        "price_volatility": 0.29,
        "sales_per_month": 15.0,
    }


@pytest.fixture
def high_volatility_certification_data() -> Dict[str, Any]:
    """
    Certification book but with very high volatility - NOT evergreen.
    Even good keywords can not save high volatility.
    """
    return {
        "title": "CPA Exam Review 2025 Edition",
        "category": "Business",
        "bsr": 80000,
        "avg_price_12m": 120.00,
        "price_volatility": 0.35,
        "sales_per_month": 8.0,
    }


# =============================================================================
# TEST: identify_evergreen - Nursing Book
# =============================================================================

class TestIdentifyNursingBook:
    """Test identification of nursing/medical books as evergreen."""

    def test_identify_nursing_book_as_evergreen(self, nursing_textbook_data):
        """
        NCLEX nursing book should be identified as PROFESSIONAL_CERTIFICATION evergreen.
        - Multiple keyword matches (nclex, nursing)
        - Low volatility (0.12)
        - Good BSR (35000)
        - Strong sales (25/month)
        """
        result = identify_evergreen(nursing_textbook_data)

        # Verify structure
        assert isinstance(result, EvergreenClassification)

        # Must be evergreen
        assert result.is_evergreen is True

        # Must be PROFESSIONAL_CERTIFICATION type
        assert result.evergreen_type == "PROFESSIONAL_CERTIFICATION"

        # Confidence should be high (keyword matches + good metrics)
        assert result.confidence >= 0.6

        # Should have reasons explaining the classification
        assert len(result.reasons) >= 2
        assert any("nclex" in r.lower() or "nursing" in r.lower() for r in result.reasons)

        # Should recommend stock level based on sales
        # recommended_stock_level = max(2, int(monthly_sales * 2.5))
        # = max(2, int(25 * 2.5)) = max(2, 62) = 62
        assert result.recommended_stock_level == 62

        # Should estimate monthly sales
        assert result.expected_monthly_sales == 25.0

    def test_nursing_book_includes_medical_reasons(self, nursing_textbook_data):
        """
        Classification should include medical/nursing related reasons.
        """
        result = identify_evergreen(nursing_textbook_data)

        # At least one reason should mention medical/nursing keywords
        medical_keywords = ["nclex", "nursing", "medical", "certification"]
        has_medical_reason = any(
            any(kw in reason.lower() for kw in medical_keywords)
            for reason in result.reasons
        )
        assert has_medical_reason


# =============================================================================
# TEST: identify_evergreen - Programming Book
# =============================================================================

class TestIdentifyProgrammingBook:
    """Test identification of programming classics as evergreen."""

    def test_identify_programming_book_as_evergreen(self, programming_book_data):
        """
        Clean Code should be identified as CLASSIC evergreen.
        - Keyword match (clean code)
        - Very low volatility (0.08)
        - Excellent BSR (8500)
        - Very strong sales (45/month)
        """
        result = identify_evergreen(programming_book_data)

        assert isinstance(result, EvergreenClassification)
        assert result.is_evergreen is True
        assert result.evergreen_type == "CLASSIC"
        assert result.confidence >= 0.7

        # Stock level = max(2, int(45 * 2.5)) = 112
        assert result.recommended_stock_level == 112

    def test_programming_book_high_confidence(self, programming_book_data):
        """
        Strong metrics should result in high confidence.
        """
        result = identify_evergreen(programming_book_data)

        # Low volatility + good BSR + strong sales = high confidence
        assert result.confidence >= 0.7


# =============================================================================
# TEST: identify_evergreen - Seasonal Textbook
# =============================================================================

class TestSeasonalTextbook:
    """Test that seasonal textbooks are NOT identified as evergreen."""

    def test_seasonal_textbook_not_evergreen(self, seasonal_textbook_data):
        """
        Generic college textbook with high volatility should NOT be evergreen.
        - No keyword matches
        - High volatility (0.45 > 0.30 threshold)
        - Poor BSR (250000)
        - Low sales (3/month)
        """
        result = identify_evergreen(seasonal_textbook_data)

        assert isinstance(result, EvergreenClassification)

        # Must NOT be evergreen
        assert result.is_evergreen is False

        # Type should be SEASONAL
        assert result.evergreen_type == "SEASONAL"

        # Confidence should be low
        assert result.confidence < 0.5

        # Stock recommendation should be 0 for non-evergreen
        assert result.recommended_stock_level == 0

    def test_seasonal_volatility_blocks_evergreen(self, seasonal_textbook_data):
        """
        High volatility (>0.30) should block evergreen classification.
        """
        result = identify_evergreen(seasonal_textbook_data)

        # Volatility 0.45 exceeds 0.30 threshold
        assert result.is_evergreen is False
        assert any("volatility" in r.lower() for r in result.reasons)


# =============================================================================
# TEST: identify_evergreen - Other Evergreen Types
# =============================================================================

class TestOtherEvergreenTypes:
    """Test other evergreen book types."""

    def test_language_book_as_skill_based(self, language_learning_book_data):
        """
        Spanish learning book should be SKILL_BASED evergreen.
        """
        result = identify_evergreen(language_learning_book_data)

        assert result.is_evergreen is True
        assert result.evergreen_type == "SKILL_BASED"
        assert result.confidence >= 0.6

    def test_reference_book_as_reference(self, reference_book_data):
        """
        Dictionary should be REFERENCE evergreen.
        """
        result = identify_evergreen(reference_book_data)

        assert result.is_evergreen is True
        assert result.evergreen_type == "REFERENCE"
        assert result.confidence >= 0.7


# =============================================================================
# TEST: identify_evergreen - Boundary Conditions
# =============================================================================

class TestBoundaryConditions:
    """Test edge cases and boundary conditions."""

    def test_borderline_volatility_still_evergreen(self, borderline_volatility_data):
        """
        Volatility at 0.29 (just under 0.30) with strong keywords should be evergreen.
        """
        result = identify_evergreen(borderline_volatility_data)

        # MCAT keyword + volatility 0.29 < 0.30 threshold
        assert result.is_evergreen is True
        assert result.evergreen_type == "PROFESSIONAL_CERTIFICATION"

    def test_high_volatility_blocks_even_good_keywords(self, high_volatility_certification_data):
        """
        Even with CPA keyword, high volatility (0.35 > 0.30) blocks evergreen.
        """
        result = identify_evergreen(high_volatility_certification_data)

        # CPA is a certification keyword, but volatility is too high
        assert result.is_evergreen is False
        assert result.evergreen_type == "SEASONAL"

    def test_empty_title_handled(self):
        """
        Empty title should not crash.
        """
        data = {
            "title": "",
            "category": "Unknown",
            "bsr": 100000,
            "avg_price_12m": 25.0,
            "price_volatility": 0.20,
            "sales_per_month": 5.0,
        }

        result = identify_evergreen(data)

        # Should complete without error
        assert isinstance(result, EvergreenClassification)
        assert result.is_evergreen is False  # No keywords to match

    def test_none_values_handled(self):
        """
        None values should be handled gracefully.
        """
        data = {
            "title": "Some Book Title",
            "category": None,
            "bsr": None,
            "avg_price_12m": None,
            "price_volatility": None,
            "sales_per_month": None,
        }

        result = identify_evergreen(data)

        # Should complete without error
        assert isinstance(result, EvergreenClassification)

    def test_missing_keys_handled(self):
        """
        Missing keys should be handled gracefully.
        """
        data = {
            "title": "Pharmacology for Nurses",
            # Missing other keys
        }

        result = identify_evergreen(data)

        # Should complete without error
        assert isinstance(result, EvergreenClassification)
        # Should still detect keyword
        assert "pharmacology" in str(result.reasons).lower() or "nursing" in str(result.reasons).lower()


# =============================================================================
# TEST: identify_evergreen - Confidence Calculation
# =============================================================================

class TestConfidenceCalculation:
    """Test the confidence score calculation logic."""

    def test_multiple_keywords_boost_confidence(self):
        """
        Multiple keyword matches should boost confidence significantly.
        """
        data = {
            "title": "NCLEX Nursing Pharmacology Clinical Review",
            "category": "Nursing",
            "bsr": 50000,
            "avg_price_12m": 45.0,
            "price_volatility": 0.15,
            "sales_per_month": 10.0,
        }

        result = identify_evergreen(data)

        # 4 keywords (nclex, nursing, pharmacology, clinical) = +0.9 confidence
        assert result.confidence >= 0.9

    def test_low_volatility_adds_confidence(self):
        """
        Low volatility (<0.15) should add +0.3 confidence.
        """
        data = {
            "title": "Some Generic Book",
            "category": "General",
            "bsr": 50000,
            "avg_price_12m": 25.0,
            "price_volatility": 0.10,  # Very low
            "sales_per_month": 10.0,
        }

        result = identify_evergreen(data)

        # No keywords but low volatility should add confidence
        assert result.confidence >= 0.3

    def test_good_bsr_adds_confidence(self):
        """
        Good BSR (<50000) should add +0.2 confidence.
        """
        data = {
            "title": "Some Book",
            "category": "General",
            "bsr": 30000,  # Good BSR
            "avg_price_12m": 25.0,
            "price_volatility": 0.20,
            "sales_per_month": 10.0,
        }

        result = identify_evergreen(data)

        # Good BSR contributes to confidence
        assert result.confidence >= 0.2

    def test_high_sales_adds_confidence(self):
        """
        High sales (>=10/month) should add +0.2 confidence.
        """
        data = {
            "title": "Some Book",
            "category": "General",
            "bsr": 100000,
            "avg_price_12m": 25.0,
            "price_volatility": 0.20,
            "sales_per_month": 15.0,  # Good sales
        }

        result = identify_evergreen(data)

        # High sales contributes to confidence
        assert result.confidence >= 0.2


# =============================================================================
# TEST: identify_evergreen - Stock Level Calculation
# =============================================================================

class TestStockLevelCalculation:
    """Test recommended stock level calculation."""

    def test_stock_level_formula(self, nursing_textbook_data):
        """
        Stock level = max(2, int(monthly_sales * 2.5))
        """
        result = identify_evergreen(nursing_textbook_data)

        # 25 * 2.5 = 62.5 -> int -> 62
        expected = max(2, int(25.0 * 2.5))
        assert result.recommended_stock_level == expected

    def test_minimum_stock_level(self):
        """
        Minimum stock level should be 2 for evergreen books.
        """
        data = {
            "title": "NCLEX Review Guide",
            "category": "Nursing",
            "bsr": 45000,
            "avg_price_12m": 30.0,
            "price_volatility": 0.12,
            "sales_per_month": 0.5,  # Very low sales
        }

        result = identify_evergreen(data)

        if result.is_evergreen:
            # 0.5 * 2.5 = 1.25 -> int -> 1, but min is 2
            assert result.recommended_stock_level == 2

    def test_zero_stock_for_seasonal(self, seasonal_textbook_data):
        """
        Non-evergreen books should have 0 recommended stock.
        """
        result = identify_evergreen(seasonal_textbook_data)

        assert result.is_evergreen is False
        assert result.recommended_stock_level == 0


# =============================================================================
# TEST: get_evergreen_portfolio_targets
# =============================================================================

class TestEvergreenPortfolioTargets:
    """Test portfolio target allocation function."""

    def test_returns_static_dict(self):
        """
        Should return a dict with target allocations.
        """
        result = get_evergreen_portfolio_targets()

        assert isinstance(result, dict)
        assert "evergreen_target_pct" in result
        assert "category_breakdown" in result

    def test_evergreen_target_is_30_percent(self):
        """
        Target evergreen allocation should be 30%.
        """
        result = get_evergreen_portfolio_targets()

        assert result["evergreen_target_pct"] == 30

    def test_category_breakdown_exists(self):
        """
        Should have breakdown by evergreen category.
        """
        result = get_evergreen_portfolio_targets()

        breakdown = result["category_breakdown"]
        assert "PROFESSIONAL_CERTIFICATION" in breakdown
        assert "CLASSIC" in breakdown
        assert "REFERENCE" in breakdown
        assert "SKILL_BASED" in breakdown

    def test_category_allocations_sum_correctly(self):
        """
        Category allocations should sum to evergreen_target_pct.
        """
        result = get_evergreen_portfolio_targets()

        breakdown = result["category_breakdown"]
        total = sum(breakdown.values())

        # Should sum to 30 (the evergreen target)
        assert total == result["evergreen_target_pct"]


# =============================================================================
# TEST: EVERGREEN_KEYWORDS constant
# =============================================================================

class TestEvergreenKeywords:
    """Test the EVERGREEN_KEYWORDS constant."""

    def test_keywords_dict_exists(self):
        """
        EVERGREEN_KEYWORDS should be a dict with categories.
        """
        assert isinstance(EVERGREEN_KEYWORDS, dict)
        assert "PROFESSIONAL_CERTIFICATION" in EVERGREEN_KEYWORDS
        assert "CLASSIC" in EVERGREEN_KEYWORDS
        assert "REFERENCE" in EVERGREEN_KEYWORDS
        assert "SKILL_BASED" in EVERGREEN_KEYWORDS

    def test_professional_certification_keywords(self):
        """
        Professional certification should include key medical/legal terms.
        """
        keywords = EVERGREEN_KEYWORDS["PROFESSIONAL_CERTIFICATION"]

        assert "nclex" in keywords
        assert "cpa" in keywords
        assert "mcat" in keywords
        assert "nursing" in keywords
        assert "pharmacology" in keywords

    def test_classic_keywords(self):
        """
        Classics should include programming and business staples.
        """
        keywords = EVERGREEN_KEYWORDS["CLASSIC"]

        assert "clean code" in keywords
        assert "design patterns" in keywords
        assert "algorithms" in keywords

    def test_skill_based_keywords(self):
        """
        Skill-based should include language and music terms.
        """
        keywords = EVERGREEN_KEYWORDS["SKILL_BASED"]

        assert "spanish" in keywords
        assert "piano" in keywords
        assert "guitar" in keywords


# =============================================================================
# TEST: Integration / Real-World Scenarios
# =============================================================================

class TestRealWorldScenarios:
    """Test with realistic book data."""

    def test_anatomy_physiology_textbook(self):
        """
        Anatomy & Physiology textbooks are perennial sellers.
        """
        data = {
            "title": "Human Anatomy and Physiology 11th Edition",
            "category": "Medical",
            "bsr": 25000,
            "avg_price_12m": 149.99,
            "price_volatility": 0.18,
            "sales_per_month": 20.0,
        }

        result = identify_evergreen(data)

        assert result.is_evergreen is True
        assert result.evergreen_type == "PROFESSIONAL_CERTIFICATION"

    def test_gre_prep_book(self):
        """
        GRE prep books should be professional certification.
        """
        data = {
            "title": "GRE Prep Plus 2025: Practice Tests + Strategies",
            "category": "Test Prep",
            "bsr": 15000,
            "avg_price_12m": 29.99,
            "price_volatility": 0.22,
            "sales_per_month": 35.0,
        }

        result = identify_evergreen(data)

        assert result.is_evergreen is True
        assert result.evergreen_type == "PROFESSIONAL_CERTIFICATION"

    def test_style_guide_reference(self):
        """
        APA Manual should be reference.
        """
        data = {
            "title": "Publication Manual of the APA 7th Edition",
            "category": "Reference",
            "bsr": 3000,
            "avg_price_12m": 32.00,
            "price_volatility": 0.06,
            "sales_per_month": 80.0,
        }

        result = identify_evergreen(data)

        assert result.is_evergreen is True
        assert result.evergreen_type == "REFERENCE"

    def test_effective_java_classic(self):
        """
        Effective Java should be a classic.
        """
        data = {
            "title": "Effective Java 3rd Edition",
            "category": "Computer Science",
            "bsr": 6000,
            "avg_price_12m": 45.00,
            "price_volatility": 0.09,
            "sales_per_month": 40.0,
        }

        result = identify_evergreen(data)

        assert result.is_evergreen is True
        assert result.evergreen_type == "CLASSIC"

    def test_photography_skill_book(self):
        """
        Photography learning book should be skill-based.
        """
        data = {
            "title": "Understanding Exposure: Photography Fundamentals",
            "category": "Arts",
            "bsr": 20000,
            "avg_price_12m": 24.99,
            "price_volatility": 0.11,
            "sales_per_month": 22.0,
        }

        result = identify_evergreen(data)

        assert result.is_evergreen is True
        assert result.evergreen_type == "SKILL_BASED"
