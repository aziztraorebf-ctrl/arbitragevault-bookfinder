"""
Daily Review Service - Product classification engine.

Classifies AutoSourcing picks into actionable categories based on
historical data, ROI metrics, and market conditions.

Categories (priority order - first match wins):
1. REJECT  - Amazon on listing, OR ROI < 0, OR BSR <= 0
2. FLUKE   - No history (never seen before)
3. JACKPOT - ROI > 80% with history
4. REVENANT - Last seen 24h+ ago, reappears today
5. STABLE  - 2+ sightings, ROI 15-80%, BSR > 0, no Amazon
"""
import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class Classification(str, Enum):
    """Product classification categories."""
    STABLE = "STABLE"
    JACKPOT = "JACKPOT"
    REVENANT = "REVENANT"
    FLUKE = "FLUKE"
    REJECT = "REJECT"


CLASSIFICATION_META: Dict[Classification, Dict[str, str]] = {
    Classification.STABLE: {
        "label": "Opportunite fiable",
        "action": "Achat recommande",
        "color": "green",
    },
    Classification.JACKPOT: {
        "label": "ROI exceptionnel",
        "action": "Verification manuelle requise",
        "color": "yellow",
    },
    Classification.REVENANT: {
        "label": "Produit de retour",
        "action": "Pattern a surveiller",
        "color": "blue",
    },
    Classification.FLUKE: {
        "label": "Donnees suspectes",
        "action": "Ignorer",
        "color": "gray",
    },
    Classification.REJECT: {
        "label": "A eviter",
        "action": "Ne pas acheter",
        "color": "red",
    },
}

# --- Thresholds (configurable constants) ---
JACKPOT_ROI_THRESHOLD = 80.0
STABLE_MIN_ROI = 15.0
REVENANT_GAP_HOURS = 24
MIN_HISTORY_FOR_STABLE = 2


def classify_product(
    product: Dict[str, Any],
    history: List[Dict[str, Any]],
    now: Optional[datetime] = None,
) -> Classification:
    """
    Classify a product based on its metrics and sighting history.

    Priority order: REJECT > FLUKE > JACKPOT > REVENANT > STABLE.
    Default fallback: FLUKE (not enough evidence to classify).

    Args:
        product: Dict with keys: roi_percentage, bsr, amazon_on_listing, etc.
        history: List of past sightings with tracked_at, bsr, price.

    Returns:
        Classification enum value.
    """
    now = now or datetime.now(timezone.utc)

    roi = product.get("roi_percentage", 0.0) or 0.0
    bsr = product.get("bsr", -1) or -1
    amazon = product.get("amazon_on_listing", False)

    # --- REJECT: Amazon seller, negative ROI, or invalid BSR ---
    if amazon:
        logger.debug("REJECT: Amazon on listing for %s", product.get("asin"))
        return Classification.REJECT
    if roi < 0:
        logger.debug("REJECT: Negative ROI (%.2f) for %s", roi, product.get("asin"))
        return Classification.REJECT
    if bsr <= 0:
        logger.debug("REJECT: Invalid BSR (%d) for %s", bsr, product.get("asin"))
        return Classification.REJECT

    # --- FLUKE: No history at all (never seen before) ---
    if not history:
        logger.debug("FLUKE: No history for %s", product.get("asin"))
        return Classification.FLUKE

    # --- JACKPOT: Exceptionally high ROI (must have history) ---
    if roi > JACKPOT_ROI_THRESHOLD:
        logger.debug(
            "JACKPOT: ROI %.2f%% > %.2f%% for %s",
            roi, JACKPOT_ROI_THRESHOLD, product.get("asin"),
        )
        return Classification.JACKPOT

    # --- REVENANT: Last seen 24h+ ago, reappears today ---
    most_recent = max(history, key=lambda h: h["tracked_at"])
    gap = now - most_recent["tracked_at"]
    if gap > timedelta(hours=REVENANT_GAP_HOURS):
        logger.debug(
            "REVENANT: Gap of %s for %s (threshold: %dh)",
            gap, product.get("asin"), REVENANT_GAP_HOURS,
        )
        return Classification.REVENANT

    # --- STABLE: 2+ sightings, decent ROI, no Amazon ---
    if len(history) >= MIN_HISTORY_FOR_STABLE and roi >= STABLE_MIN_ROI:
        logger.debug(
            "STABLE: %d sightings, ROI %.2f%% for %s",
            len(history), roi, product.get("asin"),
        )
        return Classification.STABLE

    # --- Default: FLUKE (not enough evidence) ---
    logger.debug("FLUKE (default): Insufficient evidence for %s", product.get("asin"))
    return Classification.FLUKE


def generate_daily_review(
    picks: List[Dict[str, Any]],
    history_map: Dict[str, List[Dict[str, Any]]],
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Aggregate product picks into a daily review with classifications.

    For each pick, classifies it using classify_product(), then builds
    a summary with counts, top opportunities, and a text overview.

    Args:
        picks: List of product pick dicts (must contain 'asin' key).
        history_map: Dict mapping ASIN -> list of history entries.
        now: Optional datetime for classification (passed to classify_product).

    Returns:
        Dict with: review_date, total, counts, classified_products,
        top_opportunities, summary.
    """
    now = now or datetime.now(timezone.utc)

    # Initialize counts for all categories
    counts: Dict[str, int] = {c.value: 0 for c in Classification}

    classified_products: List[Dict[str, Any]] = []

    for pick in picks:
        asin = pick.get("asin", "")
        history = history_map.get(asin, [])
        classification = classify_product(pick, history, now=now)

        counts[classification.value] += 1

        meta = CLASSIFICATION_META[classification]
        enriched = {
            **pick,
            "classification": classification.value,
            "classification_label": meta["label"],
            "classification_action": meta["action"],
            "classification_color": meta["color"],
        }
        classified_products.append(enriched)

    # Top opportunities: exclude REJECT and FLUKE, sort by ROI desc, max 3
    excluded = {Classification.REJECT.value, Classification.FLUKE.value}
    top_opportunities = [
        p for p in classified_products
        if p["classification"] not in excluded
    ]
    top_opportunities.sort(key=lambda p: p.get("roi_percentage", 0.0) or 0.0, reverse=True)
    top_opportunities = top_opportunities[:3]

    # Build summary text
    total = len(picks)
    stable_count = counts[Classification.STABLE.value]
    jackpot_count = counts[Classification.JACKPOT.value]

    if total > 0:
        avg_roi = sum(p.get("roi_percentage", 0.0) or 0.0 for p in picks) / total
        summary = (
            f"{stable_count} achat(s) recommande(s). "
            f"{jackpot_count} jackpot(s) a verifier. "
            f"ROI moyen {avg_roi:.1f}%"
        )
    else:
        summary = "Aucun produit a analyser."

    return {
        "review_date": now.strftime("%Y-%m-%d"),
        "total": total,
        "counts": counts,
        "classified_products": classified_products,
        "top_opportunities": top_opportunities,
        "summary": summary,
    }
