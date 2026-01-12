"""
Evergreen Identifier Service for ArbitrageVault Textbook Pivot.

Identifies evergreen books that provide stable year-round income during off-peak seasons.
Evergreen books include professional certification guides, classics, reference materials,
and skill-based learning resources.

Key concepts:
- Evergreen books sell consistently regardless of academic calendar
- They provide income stability during summer/winter breaks
- Portfolio target: 30% evergreen to balance seasonal textbook volatility
"""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional


# =============================================================================
# CONSTANTS
# =============================================================================

EVERGREEN_KEYWORDS: Dict[str, List[str]] = {
    "PROFESSIONAL_CERTIFICATION": [
        "nclex", "cpa", "pmp", "mcat", "lsat", "gmat", "gre",
        "pharmacology", "anatomy", "physiology", "nursing",
        "medical", "clinical", "pathophysiology", "certification",
    ],
    "CLASSIC": [
        "clean code", "design patterns", "algorithms", "data structures",
        "effective java", "python crash course", "javascript",
        "leadership", "management", "7 habits",
    ],
    "REFERENCE": [
        "dictionary", "thesaurus", "style guide", "apa manual",
        "handbook", "encyclopedia", "atlas", "publication manual",
    ],
    "SKILL_BASED": [
        "spanish", "french", "german", "japanese", "chinese",
        "piano", "guitar", "music theory", "drawing", "photography",
    ],
}

# Volatility thresholds
MAX_EVERGREEN_VOLATILITY = 0.30
LOW_VOLATILITY_THRESHOLD = 0.15
MEDIUM_VOLATILITY_THRESHOLD = 0.25

# BSR thresholds
EXCELLENT_BSR = 50000
GOOD_BSR = 100000

# Sales thresholds
HIGH_SALES_THRESHOLD = 10
MEDIUM_SALES_THRESHOLD = 5

# Confidence multipliers
KEYWORD_CONFIDENCE_PER_MATCH = 0.3
MAX_KEYWORD_CONFIDENCE = 0.9
LOW_VOLATILITY_CONFIDENCE = 0.3
MEDIUM_VOLATILITY_CONFIDENCE = 0.15
EXCELLENT_BSR_CONFIDENCE = 0.2
GOOD_BSR_CONFIDENCE = 0.1
HIGH_SALES_CONFIDENCE = 0.2
MEDIUM_SALES_CONFIDENCE = 0.1

# Stock level multiplier
STOCK_LEVEL_MULTIPLIER = 2.5
MIN_STOCK_LEVEL = 2


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class EvergreenClassification:
    """Result of evergreen book classification."""
    is_evergreen: bool
    evergreen_type: str  # PROFESSIONAL_CERTIFICATION, CLASSIC, REFERENCE, SKILL_BASED, SEASONAL
    confidence: float
    reasons: List[str]
    recommended_stock_level: int
    expected_monthly_sales: Optional[float] = None


# =============================================================================
# MAIN FUNCTIONS
# =============================================================================

def identify_evergreen(product_data: Dict[str, Any]) -> EvergreenClassification:
    """
    Identify if a book is evergreen based on title keywords and market metrics.

    Args:
        product_data: Dict with keys:
            - title: Book title
            - category: Product category
            - bsr: Best seller rank
            - avg_price_12m: Average price over 12 months
            - price_volatility: Price volatility (0-1 scale)
            - sales_per_month: Estimated monthly sales

    Returns:
        EvergreenClassification with classification details

    Classification logic:
        1. Check keyword matches -> up to +0.9 confidence for 3+ matches
        2. Check volatility < 0.15 -> +0.3 confidence
        3. Check volatility < 0.25 -> +0.15 confidence
        4. Check BSR < 50000 -> +0.2 confidence
        5. Check BSR < 100000 -> +0.1 confidence
        6. Check monthly_sales >= 10 -> +0.2 confidence
        7. Check monthly_sales >= 5 -> +0.1 confidence
        8. is_evergreen = confidence >= 0.5 AND volatility < 0.30
        9. If not evergreen, type = "SEASONAL"
        10. recommended_stock_level = max(2, int(monthly_sales * 2.5)) if evergreen else 0
    """
    # Extract data with safe defaults
    title = (product_data.get("title") or "").lower()
    category = (product_data.get("category") or "").lower()
    bsr = product_data.get("bsr")
    price_volatility = product_data.get("price_volatility")
    sales_per_month = product_data.get("sales_per_month")

    # Initialize tracking
    confidence = 0.0
    reasons: List[str] = []
    matched_type: Optional[str] = None
    keyword_matches: List[str] = []

    # Step 1: Check keyword matches
    for evergreen_type, keywords in EVERGREEN_KEYWORDS.items():
        for keyword in keywords:
            if keyword in title or keyword in category:
                keyword_matches.append(keyword)
                if matched_type is None:
                    matched_type = evergreen_type

    # Calculate keyword confidence
    if keyword_matches:
        num_matches = len(keyword_matches)
        keyword_confidence = min(num_matches * KEYWORD_CONFIDENCE_PER_MATCH, MAX_KEYWORD_CONFIDENCE)
        confidence += keyword_confidence
        reasons.append(f"Keyword matches: {', '.join(keyword_matches[:5])}")

    # Step 2-3: Check volatility
    if price_volatility is not None:
        if price_volatility < LOW_VOLATILITY_THRESHOLD:
            confidence += LOW_VOLATILITY_CONFIDENCE
            reasons.append(f"Very low volatility: {price_volatility:.2f}")
        elif price_volatility < MEDIUM_VOLATILITY_THRESHOLD:
            confidence += MEDIUM_VOLATILITY_CONFIDENCE
            reasons.append(f"Low volatility: {price_volatility:.2f}")
        elif price_volatility >= MAX_EVERGREEN_VOLATILITY:
            reasons.append(f"High volatility blocks evergreen: {price_volatility:.2f}")

    # Step 4-5: Check BSR
    if bsr is not None:
        if bsr < EXCELLENT_BSR:
            confidence += EXCELLENT_BSR_CONFIDENCE
            reasons.append(f"Excellent BSR: {bsr:,}")
        elif bsr < GOOD_BSR:
            confidence += GOOD_BSR_CONFIDENCE
            reasons.append(f"Good BSR: {bsr:,}")

    # Step 6-7: Check monthly sales
    if sales_per_month is not None:
        if sales_per_month >= HIGH_SALES_THRESHOLD:
            confidence += HIGH_SALES_CONFIDENCE
            reasons.append(f"Strong sales: {sales_per_month:.1f}/month")
        elif sales_per_month >= MEDIUM_SALES_THRESHOLD:
            confidence += MEDIUM_SALES_CONFIDENCE
            reasons.append(f"Moderate sales: {sales_per_month:.1f}/month")

    # Step 8: Determine if evergreen
    # is_evergreen = confidence >= 0.5 AND volatility < 0.30
    volatility_ok = price_volatility is None or price_volatility < MAX_EVERGREEN_VOLATILITY
    is_evergreen = confidence >= 0.5 and volatility_ok

    # Step 9: Set type
    if is_evergreen:
        evergreen_type = matched_type or "CLASSIC"  # Default to CLASSIC if no keyword match
    else:
        evergreen_type = "SEASONAL"

    # Step 10: Calculate stock level
    if is_evergreen and sales_per_month is not None:
        recommended_stock_level = max(MIN_STOCK_LEVEL, int(sales_per_month * STOCK_LEVEL_MULTIPLIER))
    elif is_evergreen:
        recommended_stock_level = MIN_STOCK_LEVEL
    else:
        recommended_stock_level = 0

    return EvergreenClassification(
        is_evergreen=is_evergreen,
        evergreen_type=evergreen_type,
        confidence=round(confidence, 2),
        reasons=reasons,
        recommended_stock_level=recommended_stock_level,
        expected_monthly_sales=sales_per_month,
    )


def get_evergreen_portfolio_targets() -> Dict[str, Any]:
    """
    Return static portfolio target allocations for evergreen books.

    Returns:
        Dict with:
            - evergreen_target_pct: Target percentage of portfolio as evergreen (30%)
            - category_breakdown: Target allocation by evergreen category
    """
    return {
        "evergreen_target_pct": 30,
        "category_breakdown": {
            "PROFESSIONAL_CERTIFICATION": 12,
            "CLASSIC": 8,
            "REFERENCE": 5,
            "SKILL_BASED": 5,
        },
        "rationale": (
            "30% evergreen allocation provides income stability during "
            "off-peak seasons (summer break, winter break) when textbook "
            "demand drops significantly."
        ),
    }
