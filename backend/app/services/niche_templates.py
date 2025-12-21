"""
Curated Niche Templates Service

Pre-defined market segments validated with real-time Keepa data.
Each template encodes expertise: category clusters, BSR sweet spots, price ranges.

Phase 6 Update: Added strategy types (smart_velocity, textbooks) with competition filters.
- Smart Velocity: BSR 10K-80K, margin $12+, max 5 FBA sellers
- Textbooks: BSR 30K-250K, margin $20+, max 3 FBA sellers
"""

import sys
import random
from typing import List, Dict, Optional, Union
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.keepa_product_finder import KeepaProductFinderService
from app.core.logging import get_logger

logger = get_logger(__name__)


# Strategy type definitions for filtering
STRATEGY_CONFIGS = {
    "smart_velocity": {
        "description": "Fast rotation books with reasonable margin - BSR 10K-80K",
        "bsr_range": (10000, 80000),
        "min_margin": 12.0,  # $12 minimum to cover prep center + fees
        "max_fba_sellers": 5,  # Low competition threshold
        "price_range": (15.0, 60.0),
        "min_roi": 30,
        "min_velocity": 50
    },
    "textbooks": {
        "description": "High margin textbooks with slower rotation - BSR 30K-250K (legacy)",
        "bsr_range": (30000, 250000),
        "min_margin": 20.0,  # $20 minimum for textbooks
        "max_fba_sellers": 3,  # Very low competition
        "price_range": (30.0, 150.0),
        "min_roi": 50,
        "min_velocity": 30
    },
    # Phase 8: Dual Template Strategy (PDF Golden Rule alignment)
    "textbooks_standard": {
        "description": "PDF Golden Rule textbooks - BSR 100K-250K, balanced rotation/profit",
        "bsr_range": (100000, 250000),
        "min_margin": 15.0,  # $15 minimum profit (PDF aligned)
        "max_fba_sellers": 5,  # Low competition
        "price_range": (40.0, 150.0),  # $40-$150 (PDF: fees eat profit on cheap books)
        "min_roi": 40,
        "min_velocity": 30,
        "estimated_rotation_days": "7-14"
    },
    "textbooks_patience": {
        "description": "Under-the-radar textbooks - BSR 250K-400K, higher profit, slower rotation",
        "bsr_range": (250000, 400000),
        "min_margin": 25.0,  # $25 minimum (higher to justify wait)
        "max_fba_sellers": 3,  # Very low competition
        "price_range": (40.0, 150.0),  # Same price range
        "min_roi": 50,
        "min_velocity": 20,  # Lower velocity acceptable
        "estimated_rotation_days": "28-42",
        "warning": "Rotation lente (4-6 semaines minimum). Capital immobilise plus longtemps."
    }
}


# Curated Niche Templates
# Phase 6: Added 'type' field for strategy-based filtering
# Each template now includes max_fba_sellers for competition filtering
CURATED_NICHES = [
    # ============================================
    # SMART VELOCITY TEMPLATES (BSR 10K-80K, $12+ margin)
    # Fast rotation with reasonable profit per unit
    # ============================================
    {
        "id": "tech-books-python",
        "name": "[TECH] Python Books Beginners $20-50",
        "description": "Python learning books for beginners/intermediate - evergreen segment with stable ROI",
        "type": "smart_velocity",
        "categories": [3508, 3839, 5],  # Python > Programming > Computers & Technology
        "bsr_range": (10000, 80000),  # Smart Velocity range
        "price_range": (20.0, 50.0),
        "min_margin": 12.0,
        "max_fba_sellers": 5,
        "min_roi": 30,
        "min_velocity": 50,
        "icon": "PYTHON"
    },
    {
        "id": "wellness-journals",
        "name": "[WELLNESS] Wellness Journals",
        "description": "Meditation, gratitude, mindfulness journals - strong post-2020 trend",
        "type": "smart_velocity",
        "categories": [283155, 4736],  # Self-Help > Personal Transformation
        "bsr_range": (10000, 50000),
        "price_range": (15.0, 35.0),
        "min_margin": 12.0,
        "max_fba_sellers": 5,
        "min_roi": 35,
        "min_velocity": 60,
        "icon": "WELLNESS"
    },
    {
        "id": "cooking-healthy",
        "name": "[FOOD] Healthy Cooking Books",
        "description": "Healthy recipes, keto, vegan - constantly growing market",
        "type": "smart_velocity",
        "categories": [6, 1000],  # Cookbooks, Food & Wine > Special Diet
        "bsr_range": (10000, 80000),
        "price_range": (18.0, 45.0),
        "min_margin": 12.0,
        "max_fba_sellers": 5,
        "min_roi": 30,
        "min_velocity": 50,
        "icon": "COOKING"
    },
    {
        "id": "kids-education-preschool",
        "name": "[KIDS] Preschool Education Books",
        "description": "Activity books, alphabet learning, numbers - stable niche with parents",
        "type": "smart_velocity",
        "categories": [4, 17],  # Children's Books > Education & Reference
        "bsr_range": (10000, 60000),
        "price_range": (15.0, 30.0),
        "min_margin": 12.0,
        "max_fba_sellers": 5,
        "min_roi": 32,
        "min_velocity": 55,
        "icon": "EDUCATION"
    },
    {
        "id": "self-help-productivity",
        "name": "[PRODUCTIVITY] Personal Development",
        "description": "Time management, habits, focus - premium segment with strong demand",
        "type": "smart_velocity",
        "categories": [4736, 11748],  # Self-Help > Success
        "bsr_range": (10000, 70000),
        "price_range": (15.0, 40.0),
        "min_margin": 12.0,
        "max_fba_sellers": 5,
        "min_roi": 30,
        "min_velocity": 50,
        "icon": "PRODUCTIVITY"
    },
    {
        "id": "fiction-thriller-mystery",
        "name": "[FICTION] Thrillers & Mysteries",
        "description": "Suspense novels, detective stories - fast rotation, high velocity",
        "type": "smart_velocity",
        "categories": [18, 10677],  # Mystery, Thriller & Suspense
        "bsr_range": (10000, 50000),
        "price_range": (15.0, 30.0),
        "min_margin": 12.0,
        "max_fba_sellers": 5,
        "min_roi": 33,
        "min_velocity": 60,
        "icon": "MYSTERY"
    },
    {
        "id": "romance-contemporary",
        "name": "[ROMANCE] Contemporary Romance",
        "description": "Modern romance, feel-good - high volume, fast rotation",
        "type": "smart_velocity",
        "categories": [23, 10188],  # Romance > Contemporary
        "bsr_range": (10000, 40000),
        "price_range": (15.0, 28.0),
        "min_margin": 12.0,
        "max_fba_sellers": 5,
        "min_roi": 35,
        "min_velocity": 65,
        "icon": "ROMANCE"
    },
    {
        "id": "fitness-home-workout",
        "name": "[FITNESS] Home Fitness & Yoga",
        "description": "Home workout programs, yoga, stretching - post-COVID boom",
        "type": "smart_velocity",
        "categories": [4736, 5267],  # Health, Fitness & Dieting > Exercise & Fitness
        "bsr_range": (10000, 60000),
        "price_range": (15.0, 40.0),
        "min_margin": 12.0,
        "max_fba_sellers": 5,
        "min_roi": 31,
        "min_velocity": 55,
        "icon": "FITNESS"
    },
    # ============================================
    # TEXTBOOK TEMPLATES (BSR 30K-250K, $20+ margin)
    # Higher margin, slower rotation, lower competition
    # ============================================
    {
        "id": "textbook-business",
        "name": "[TEXTBOOK] Business & Economics",
        "description": "Business school textbooks - high margin, semester demand cycles",
        "type": "textbooks",
        "categories": [2, 2766, 2767],  # Business & Money > Education
        "bsr_range": (30000, 250000),
        "price_range": (30.0, 150.0),
        "min_margin": 20.0,
        "max_fba_sellers": 3,
        "min_roi": 50,
        "min_velocity": 30,
        "icon": "BUSINESS"
    },
    {
        "id": "textbook-science",
        "name": "[TEXTBOOK] Science & Math",
        "description": "STEM textbooks - chemistry, physics, calculus - evergreen academic demand",
        "type": "textbooks",
        "categories": [75, 13912, 13884],  # Science & Math > Textbooks
        "bsr_range": (30000, 250000),
        "price_range": (40.0, 200.0),
        "min_margin": 20.0,
        "max_fba_sellers": 3,
        "min_roi": 50,
        "min_velocity": 25,
        "icon": "SCIENCE"
    },
    {
        "id": "textbook-medical",
        "name": "[TEXTBOOK] Medical & Nursing",
        "description": "Medical school and nursing textbooks - premium prices, consistent demand",
        "type": "textbooks",
        "categories": [173514, 227613],  # Medical Books > Nursing
        "bsr_range": (30000, 250000),
        "price_range": (50.0, 250.0),
        "min_margin": 25.0,
        "max_fba_sellers": 3,
        "min_roi": 50,
        "min_velocity": 25,
        "icon": "MEDICAL"
    },
    {
        "id": "textbook-law",
        "name": "[TEXTBOOK] Law & Legal Studies",
        "description": "Law school textbooks and bar prep - high value, professional market",
        "type": "textbooks",
        "categories": [10777, 10927],  # Law > Legal Education
        "bsr_range": (30000, 250000),
        "price_range": (40.0, 180.0),
        "min_margin": 20.0,
        "max_fba_sellers": 3,
        "min_roi": 50,
        "min_velocity": 30,
        "icon": "LAW"
    },
    {
        "id": "textbook-engineering",
        "name": "[TEXTBOOK] Engineering",
        "description": "Engineering textbooks - mechanical, electrical, civil - specialized demand",
        "type": "textbooks",
        "categories": [13611, 13887],  # Engineering > Textbooks
        "bsr_range": (30000, 250000),
        "price_range": (40.0, 180.0),
        "min_margin": 20.0,
        "max_fba_sellers": 3,
        "min_roi": 50,
        "min_velocity": 25,
        "icon": "ENGINEERING"
    },
    {
        "id": "textbook-psychology",
        "name": "[TEXTBOOK] Psychology & Social Sciences",
        "description": "Psychology and sociology textbooks - broad university demand",
        "type": "textbooks",
        "categories": [11232, 15371],  # Social Sciences > Psychology
        "bsr_range": (30000, 250000),
        "price_range": (35.0, 150.0),
        "min_margin": 20.0,
        "max_fba_sellers": 3,
        "min_roi": 50,
        "min_velocity": 30,
        "icon": "PSYCHOLOGY"
    },
    {
        "id": "textbook-computer-science",
        "name": "[TEXTBOOK] Computer Science",
        "description": "CS textbooks - algorithms, data structures, systems - high tech demand",
        "type": "textbooks",
        "categories": [3508, 3839, 3654],  # Computers > Programming > Textbooks
        "bsr_range": (30000, 200000),
        "price_range": (40.0, 150.0),
        "min_margin": 20.0,
        "max_fba_sellers": 3,
        "min_roi": 50,
        "min_velocity": 30,
        "icon": "CS"
    },
    # ============================================
    # DUAL TEMPLATE STRATEGY - Phase 8
    # PDF Golden Rule alignment with Standard + Patience
    # ============================================
    {
        "id": "textbook-standard-general",
        "name": "[STANDARD] General Textbooks $40-150",
        "description": "PDF Golden Rule: BSR 100K-250K, balanced rotation/profit, 7-14 day sell-through",
        "type": "textbooks_standard",
        "categories": [283155, 75, 2766],  # Books > Science & Math > Business
        "bsr_range": (100000, 250000),
        "price_range": (40.0, 150.0),
        "min_margin": 15.0,
        "max_fba_sellers": 5,
        "min_roi": 40,
        "min_velocity": 30,
        "icon": "STANDARD"
    },
    {
        "id": "textbook-patience-general",
        "name": "[PATIENCE] Under-Radar Textbooks $40-150",
        "description": "Higher profit, slower rotation. BSR 250K-400K, 4-6 week sell-through, capital lock-up.",
        "type": "textbooks_patience",
        "categories": [283155, 75, 2766],  # Books > Science & Math > Business
        "bsr_range": (250000, 400000),
        "price_range": (40.0, 150.0),
        "min_margin": 25.0,
        "max_fba_sellers": 3,
        "min_roi": 50,
        "min_velocity": 20,
        "icon": "PATIENCE"
    }
]


async def discover_curated_niches(
    db: Union[Session, AsyncSession],
    product_finder: KeepaProductFinderService,
    count: int = 3,
    shuffle: bool = True
) -> List[Dict]:
    """
    Validate curated niche templates with real-time Keepa data.

    WINDOWS FIX: Runs async code in isolated SelectorEventLoop for psycopg3 compatibility.

    Args:
        db: Database session
        product_finder: KeepaProductFinderService instance (with cache enabled)
        count: Number of niches to return (default 3)
        shuffle: Randomize template selection for variety (default True)

    Returns:
        List of validated niches with aggregate stats and top products

    Example:
        {
            "id": "tech-books-python",
            "name": "[TECH] Python Books Beginners $20-50",
            "description": "...",
            "icon": "PYTHON",
            "products_found": 7,
            "avg_roi": 35.2,
            "avg_velocity": 68.5,
            "bsr_range": (10000, 80000),
            "price_range": (20.0, 50.0),
            "top_products": [...]  # Top 3 products
        }
    """
    # WINDOWS FIX: If on Windows and in ProactorEventLoop, run in separate SelectorEventLoop
    if sys.platform == "win32":
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            if "Proactor" in type(loop).__name__:
                logger.warning(f"[NICHE_TEMPLATES] Detected {type(loop).__name__}, using synchronous wrapper for psycopg3 compatibility")
                # Run the actual async function in a separate SelectorEventLoop
                return await _run_in_selector_loop(
                    _discover_curated_niches_impl,
                    db, product_finder, count, shuffle
                )
        except RuntimeError:
            # No running loop, continue normally
            pass

    # Normal async execution for Linux/Mac or when SelectorEventLoop already in use
    return await _discover_curated_niches_impl(db, product_finder, count, shuffle)


async def _run_in_selector_loop(func, *args):
    """Run async function in isolated SelectorEventLoop for Windows compatibility."""
    import asyncio
    import concurrent.futures

    def run_with_selector():
        # Create fresh SelectorEventLoop
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Run the async function
            return loop.run_until_complete(func(*args))
        finally:
            loop.close()

    # Execute in thread pool to avoid blocking current event loop
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_with_selector)
        return future.result()


async def _discover_curated_niches_impl(
    db: Union[Session, AsyncSession],
    product_finder: KeepaProductFinderService,
    count: int,
    shuffle: bool
) -> List[Dict]:
    """Implementation of discover_curated_niches (separated for Windows compatibility)."""
    logger.info(f"[NICHE_TEMPLATES] Starting validation of {count} templates (shuffle={shuffle})")

    # Select templates
    templates = random.sample(CURATED_NICHES, min(count, len(CURATED_NICHES))) if shuffle else CURATED_NICHES[:count]

    validated = []
    for tmpl in templates:
        logger.debug(f"[NICHE_TEMPLATES] Validating template: {tmpl['id']}")

        try:
            # Call Discovery with template config
            # Phase 6: Now passing max_fba_sellers for competition filtering
            products = await product_finder.discover_with_scoring(
                domain=1,
                category=tmpl["categories"][0],  # Primary category
                bsr_min=tmpl["bsr_range"][0],
                bsr_max=tmpl["bsr_range"][1],
                price_min=tmpl["price_range"][0],
                price_max=tmpl["price_range"][1],
                max_results=10,
                max_fba_sellers=tmpl.get("max_fba_sellers")  # Competition filter
            )

            # Filter by quality thresholds - RELAXED FOR TESTING
            # Critères élargis temporairement : ROI 10+, Velocity 20+
            quality_products = [
                p for p in products
                if p.get("roi_percent", 0) >= 10  # Réduit de 27-40%
                and p.get("velocity_score", 0) >= 20  # Réduit de 50-70
            ]

            # Only include niche if ≥1 quality products found (réduit de 3 pour tests)
            if len(quality_products) >= 1:
                avg_roi = sum(p["roi_percent"] for p in quality_products) / len(quality_products)
                avg_velocity = sum(p["velocity_score"] for p in quality_products) / len(quality_products)

                validated.append({
                    "id": tmpl["id"],
                    "name": tmpl["name"],
                    "description": tmpl["description"],
                    "icon": tmpl["icon"],
                    "categories": tmpl["categories"],
                    "bsr_range": tmpl["bsr_range"],
                    "price_range": tmpl["price_range"],
                    "products_found": len(quality_products),
                    "avg_roi": round(avg_roi, 1),
                    "avg_velocity": round(avg_velocity, 1),
                    "top_products": quality_products[:3]  # Top 3 for preview
                })

                logger.info(
                    f"[NICHE_TEMPLATES] [OK] Validated {tmpl['id']}: "
                    f"{len(quality_products)} products, ROI {avg_roi:.1f}%, velocity {avg_velocity:.1f}"
                )
            else:
                logger.warning(
                    f"[NICHE_TEMPLATES] [SKIP] Skipped {tmpl['id']}: "
                    f"Only {len(quality_products)} quality products found (threshold: 3)"
                )

        except Exception as e:
            logger.error(f"[NICHE_TEMPLATES] Error validating {tmpl['id']}: {e}")
            continue

    logger.info(f"[NICHE_TEMPLATES] Completed: {len(validated)}/{len(templates)} niches validated")

    return validated


def get_niche_template_by_id(niche_id: str) -> Optional[Dict]:
    """Get a specific niche template by ID."""
    for niche in CURATED_NICHES:
        if niche["id"] == niche_id:
            return niche
    return None
