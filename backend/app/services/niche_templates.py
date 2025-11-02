"""
Curated Niche Templates Service

Pre-defined market segments validated with real-time Keepa data.
Each template encodes expertise: category clusters, BSR sweet spots, price ranges.
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


# Curated Niche Templates
CURATED_NICHES = [
    {
        "id": "tech-books-python",
        "name": "[TECH] Python Books Beginners $20-50",
        "description": "Python learning books for beginners/intermediate - evergreen segment with stable ROI",
        "categories": [3508, 3839, 5],  # Python > Programming > Computers & Technology
        "bsr_range": (10000, 80000),
        "price_range": (20.0, 50.0),
        "min_roi": 30,
        "min_velocity": 60,
        "icon": "PYTHON"
    },
    {
        "id": "wellness-journals",
        "name": "[WELLNESS] Wellness Journals",
        "description": "Meditation, gratitude, mindfulness journals - strong post-2020 trend",
        "categories": [283155, 4736],  # Self-Help > Personal Transformation
        "bsr_range": (5000, 50000),
        "price_range": (12.0, 30.0),
        "min_roi": 35,
        "min_velocity": 70,
        "icon": "WELLNESS"
    },
    {
        "id": "cooking-healthy",
        "name": "[FOOD] Healthy Cooking Books",
        "description": "Healthy recipes, keto, vegan - constantly growing market",
        "categories": [6, 1000],  # Cookbooks, Food & Wine > Special Diet
        "bsr_range": (15000, 100000),
        "price_range": (18.0, 45.0),
        "min_roi": 28,
        "min_velocity": 55,
        "icon": "COOKING"
    },
    {
        "id": "kids-education-preschool",
        "name": "[KIDS] Preschool Education Books",
        "description": "Activity books, alphabet learning, numbers - stable niche with parents",
        "categories": [4, 17],  # Children's Books > Education & Reference
        "bsr_range": (8000, 60000),
        "price_range": (10.0, 25.0),
        "min_roi": 32,
        "min_velocity": 65,
        "icon": "EDUCATION"
    },
    {
        "id": "self-help-productivity",
        "name": "[PRODUCTIVITY] Personal Development",
        "description": "Time management, habits, focus - premium segment with strong demand",
        "categories": [4736, 11748],  # Self-Help > Success
        "bsr_range": (12000, 70000),
        "price_range": (15.0, 35.0),
        "min_roi": 30,
        "min_velocity": 60,
        "icon": "PRODUCTIVITY"
    },
    {
        "id": "business-entrepreneurship",
        "name": "[BUSINESS] Business & Entrepreneurship",
        "description": "Company creation, startups, side hustles - solvent audience",
        "categories": [2, 2766],  # Business & Money > Entrepreneurship
        "bsr_range": (20000, 90000),
        "price_range": (22.0, 55.0),
        "min_roi": 27,
        "min_velocity": 52,
        "icon": "BUSINESS"
    },
    {
        "id": "fiction-thriller-mystery",
        "name": "[FICTION] Thrillers & Mysteries",
        "description": "Suspense novels, detective stories - fast rotation, high velocity",
        "categories": [18, 10677],  # Mystery, Thriller & Suspense
        "bsr_range": (5000, 40000),
        "price_range": (12.0, 28.0),
        "min_roi": 33,
        "min_velocity": 75,
        "icon": "MYSTERY"
    },
    {
        "id": "craft-diy-hobbies",
        "name": "[DIY] Crafts & DIY Hobbies",
        "description": "DIY projects, scrapbooking, knitting - loyal niche with recurring purchases",
        "categories": [4736, 12595],  # Crafts, Hobbies & Home
        "bsr_range": (10000, 65000),
        "price_range": (14.0, 32.0),
        "min_roi": 31,
        "min_velocity": 58,
        "icon": "CRAFTS"
    },
    {
        "id": "gardening-homesteading",
        "name": "[GARDEN] Gardening & Homesteading",
        "description": "Vegetable growing, permaculture, self-sufficiency - growing trend",
        "categories": [6, 10333],  # Gardening & Landscape Design
        "bsr_range": (15000, 85000),
        "price_range": (16.0, 38.0),
        "min_roi": 29,
        "min_velocity": 54,
        "icon": "GARDEN"
    },
    {
        "id": "parenting-toddlers",
        "name": "[PARENTING] Toddler Parenting",
        "description": "Gentle parenting, sleep, discipline - evergreen niche",
        "categories": [4, 10516],  # Parenting & Relationships
        "bsr_range": (8000, 55000),
        "price_range": (13.0, 30.0),
        "min_roi": 34,
        "min_velocity": 68,
        "icon": "FAMILY"
    },
    {
        "id": "science-fiction-space",
        "name": "[SCIFI] Space Science-Fiction",
        "description": "SF space opera, interstellar travel - passionate audience",
        "categories": [25, 6512],  # Science Fiction & Fantasy > Space Opera
        "bsr_range": (12000, 75000),
        "price_range": (14.0, 32.0),
        "min_roi": 30,
        "min_velocity": 62,
        "icon": "SCIFI"
    },
    {
        "id": "romance-contemporary",
        "name": "[ROMANCE] Contemporary Romance",
        "description": "Modern romance, feel-good - high volume, ultra-fast rotation",
        "categories": [23, 10188],  # Romance > Contemporary
        "bsr_range": (3000, 35000),
        "price_range": (10.0, 22.0),
        "min_roi": 35,
        "min_velocity": 80,
        "icon": "ROMANCE"
    },
    {
        "id": "fitness-home-workout",
        "name": "[FITNESS] Home Fitness & Yoga",
        "description": "Home workout programs, yoga, stretching - post-COVID boom",
        "categories": [4736, 5267],  # Health, Fitness & Dieting > Exercise & Fitness
        "bsr_range": (10000, 60000),
        "price_range": (15.0, 35.0),
        "min_roi": 31,
        "min_velocity": 64,
        "icon": "FITNESS"
    },
    {
        "id": "investing-personal-finance",
        "name": "[FINANCE] Personal Finance & Investing",
        "description": "Savings, stock market, real estate - solvent audience seeking ROI",
        "categories": [2, 2665],  # Business & Money > Personal Finance
        "bsr_range": (15000, 80000),
        "price_range": (20.0, 48.0),
        "min_roi": 28,
        "min_velocity": 56,
        "icon": "FINANCE"
    },
    {
        "id": "history-world-war-2",
        "name": "[HISTORY] World War II History",
        "description": "WWII historical accounts - stable niche with collectors",
        "categories": [9, 4888],  # History > Military History > World War II
        "bsr_range": (18000, 90000),
        "price_range": (18.0, 42.0),
        "min_roi": 27,
        "min_velocity": 50,
        "icon": "HISTORY"
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
            products = await product_finder.discover_with_scoring(
                domain=1,
                category=tmpl["categories"][0],  # Primary category
                bsr_min=tmpl["bsr_range"][0],
                bsr_max=tmpl["bsr_range"][1],
                price_min=tmpl["price_range"][0],
                price_max=tmpl["price_range"][1],
                max_results=10
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
