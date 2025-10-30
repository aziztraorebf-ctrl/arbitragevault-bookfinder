"""
Curated Niche Templates Service

Pre-defined market segments validated with real-time Keepa data.
Each template encodes expertise: category clusters, BSR sweet spots, price ranges.
"""

import random
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.keepa_product_finder import KeepaProductFinderService
from app.core.logging import get_logger

logger = get_logger(__name__)


# 🎯 Curated Niche Templates
CURATED_NICHES = [
    {
        "id": "tech-books-python",
        "name": "📚 Livres Python Débutants $20-50",
        "description": "Livres apprentissage Python pour débutants/intermédiaires - segment evergreen avec ROI stable",
        "categories": [3508, 3839, 5],  # Python > Programming > Computers & Technology
        "bsr_range": (10000, 80000),
        "price_range": (20.0, 50.0),
        "min_roi": 30,
        "min_velocity": 60,
        "icon": "🐍"
    },
    {
        "id": "wellness-journals",
        "name": "🧘 Journaux Bien-Être",
        "description": "Cahiers méditation, gratitude, mindfulness - tendance forte post-2020",
        "categories": [283155, 4736],  # Self-Help > Personal Transformation
        "bsr_range": (5000, 50000),
        "price_range": (12.0, 30.0),
        "min_roi": 35,
        "min_velocity": 70,
        "icon": "✨"
    },
    {
        "id": "cooking-healthy",
        "name": "🥗 Livres Cuisine Santé",
        "description": "Recettes saines, keto, vegan - marché en croissance constante",
        "categories": [6, 1000],  # Cookbooks, Food & Wine > Special Diet
        "bsr_range": (15000, 100000),
        "price_range": (18.0, 45.0),
        "min_roi": 28,
        "min_velocity": 55,
        "icon": "🍳"
    },
    {
        "id": "kids-education-preschool",
        "name": "🎨 Livres Éducatifs Préscolaire",
        "description": "Livres d'activités, apprentissage alphabet, chiffres - niche stable avec parents",
        "categories": [4, 17],  # Children's Books > Education & Reference
        "bsr_range": (8000, 60000),
        "price_range": (10.0, 25.0),
        "min_roi": 32,
        "min_velocity": 65,
        "icon": "📖"
    },
    {
        "id": "self-help-productivity",
        "name": "⚡ Développement Personnel - Productivité",
        "description": "Time management, habits, focus - segment premium avec forte demande",
        "categories": [4736, 11748],  # Self-Help > Success
        "bsr_range": (12000, 70000),
        "price_range": (15.0, 35.0),
        "min_roi": 30,
        "min_velocity": 60,
        "icon": "🎯"
    },
    {
        "id": "business-entrepreneurship",
        "name": "💼 Business & Entrepreneuriat",
        "description": "Création entreprise, startups, side hustles - audience solvable",
        "categories": [2, 2766],  # Business & Money > Entrepreneurship
        "bsr_range": (20000, 90000),
        "price_range": (22.0, 55.0),
        "min_roi": 27,
        "min_velocity": 52,
        "icon": "🚀"
    },
    {
        "id": "fiction-thriller-mystery",
        "name": "🔍 Thrillers & Mystères",
        "description": "Romans suspense, polars - rotation rapide, forte vélocité",
        "categories": [18, 10677],  # Mystery, Thriller & Suspense
        "bsr_range": (5000, 40000),
        "price_range": (12.0, 28.0),
        "min_roi": 33,
        "min_velocity": 75,
        "icon": "📕"
    },
    {
        "id": "craft-diy-hobbies",
        "name": "✂️ Crafts & DIY Loisirs",
        "description": "Projets DIY, scrapbooking, tricot - niche loyale avec achats récurrents",
        "categories": [4736, 12595],  # Crafts, Hobbies & Home
        "bsr_range": (10000, 65000),
        "price_range": (14.0, 32.0),
        "min_roi": 31,
        "min_velocity": 58,
        "icon": "🎨"
    },
    {
        "id": "gardening-homesteading",
        "name": "🌱 Jardinage & Homesteading",
        "description": "Culture légumes, permaculture, autosuffisance - tendance croissante",
        "categories": [6, 10333],  # Gardening & Landscape Design
        "bsr_range": (15000, 85000),
        "price_range": (16.0, 38.0),
        "min_roi": 29,
        "min_velocity": 54,
        "icon": "🌿"
    },
    {
        "id": "parenting-toddlers",
        "name": "👶 Parentalité Tout-Petits",
        "description": "Éducation bienveillante, sommeil, discipline - niche evergreen",
        "categories": [4, 10516],  # Parenting & Relationships
        "bsr_range": (8000, 55000),
        "price_range": (13.0, 30.0),
        "min_roi": 34,
        "min_velocity": 68,
        "icon": "👨‍👩‍👧"
    },
    {
        "id": "science-fiction-space",
        "name": "🚀 Science-Fiction Spatiale",
        "description": "SF space opera, voyages interstellaires - audience passionnée",
        "categories": [25, 6512],  # Science Fiction & Fantasy > Space Opera
        "bsr_range": (12000, 75000),
        "price_range": (14.0, 32.0),
        "min_roi": 30,
        "min_velocity": 62,
        "icon": "🛸"
    },
    {
        "id": "romance-contemporary",
        "name": "💕 Romance Contemporaine",
        "description": "Romances modernes, feel-good - volume élevé, rotation ultra-rapide",
        "categories": [23, 10188],  # Romance > Contemporary
        "bsr_range": (3000, 35000),
        "price_range": (10.0, 22.0),
        "min_roi": 35,
        "min_velocity": 80,
        "icon": "💖"
    },
    {
        "id": "fitness-home-workout",
        "name": "🏋️ Fitness Maison & Yoga",
        "description": "Programmes home workout, yoga, stretching - post-COVID boom",
        "categories": [4736, 5267],  # Health, Fitness & Dieting > Exercise & Fitness
        "bsr_range": (10000, 60000),
        "price_range": (15.0, 35.0),
        "min_roi": 31,
        "min_velocity": 64,
        "icon": "💪"
    },
    {
        "id": "investing-personal-finance",
        "name": "💰 Finances Personnelles & Investissement",
        "description": "Épargne, bourse, immobilier - audience solvable cherchant ROI",
        "categories": [2, 2665],  # Business & Money > Personal Finance
        "bsr_range": (15000, 80000),
        "price_range": (20.0, 48.0),
        "min_roi": 28,
        "min_velocity": 56,
        "icon": "📈"
    },
    {
        "id": "history-world-war-2",
        "name": "⚔️ Histoire - Seconde Guerre Mondiale",
        "description": "Récits historiques WWII - niche stable avec collectionneurs",
        "categories": [9, 4888],  # History > Military History > World War II
        "bsr_range": (18000, 90000),
        "price_range": (18.0, 42.0),
        "min_roi": 27,
        "min_velocity": 50,
        "icon": "📜"
    }
]


async def discover_curated_niches(
    db: Session,
    product_finder: KeepaProductFinderService,
    count: int = 3,
    shuffle: bool = True
) -> List[Dict]:
    """
    Validate curated niche templates with real-time Keepa data.

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
            "name": "📚 Livres Python Débutants $20-50",
            "description": "...",
            "icon": "🐍",
            "products_found": 7,
            "avg_roi": 35.2,
            "avg_velocity": 68.5,
            "bsr_range": (10000, 80000),
            "price_range": (20.0, 50.0),
            "top_products": [...]  # Top 3 products
        }
    """
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

            # Filter by quality thresholds
            quality_products = [
                p for p in products
                if p.get("roi_percent", 0) >= tmpl["min_roi"]
                and p.get("velocity_score", 0) >= tmpl["min_velocity"]
            ]

            # Only include niche if ≥3 quality products found
            if len(quality_products) >= 3:
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
                    f"[NICHE_TEMPLATES] ✅ Validated {tmpl['id']}: "
                    f"{len(quality_products)} products, ROI {avg_roi:.1f}%, velocity {avg_velocity:.1f}"
                )
            else:
                logger.warning(
                    f"[NICHE_TEMPLATES] ❌ Skipped {tmpl['id']}: "
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
