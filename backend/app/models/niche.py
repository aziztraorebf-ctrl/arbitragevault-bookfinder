"""
Niche Market Discovery - Data Models
===================================

Modèles Pydantic pour la découverte de niches de marché.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class NicheAnalysisCriteria(BaseModel):
    """Critères d'analyse pour la découverte de niches."""
    
    bsr_range: tuple[int, int] = Field(
        default=(10000, 50000),
        description="Plage BSR optimale (min, max)"
    )
    max_sellers: int = Field(
        default=3,
        description="Nombre maximum de vendeurs par produit"
    )
    min_margin_percent: float = Field(
        default=30.0,
        description="Marge profit minimum en pourcentage"
    )
    min_price_stability: float = Field(
        default=0.75,
        description="Stabilité prix minimum (0-1)"
    )
    sample_size: int = Field(
        default=100,
        description="Taille échantillon produits par catégorie"
    )


class NicheMetrics(BaseModel):
    """Métriques calculées pour une niche."""
    
    avg_sellers: float = Field(description="Nombre moyen de vendeurs")
    avg_bsr: float = Field(description="BSR moyen")
    avg_price: float = Field(description="Prix moyen en dollars")
    price_stability: float = Field(description="Stabilité prix (0-1)")
    profit_margin: float = Field(description="Marge profit moyenne (%)")
    total_products: int = Field(description="Nombre total de produits analysés")
    viable_products: int = Field(description="Produits viables selon critères")
    competition_level: str = Field(description="Niveau concurrence (Low/Medium/High)")


class DiscoveredNiche(BaseModel):
    """Niche découverte avec métriques et score."""
    
    category_name: str = Field(description="Nom lisible de la catégorie")
    category_id: int = Field(description="ID catégorie Keepa")
    metrics: NicheMetrics = Field(description="Métriques calculées")
    niche_score: float = Field(description="Score global (1-10)")
    confidence_level: str = Field(description="Niveau confiance (High/Medium/Low)")
    sample_quality: str = Field(description="Qualité échantillon données")
    
    # Données pour debugging/transparence
    analysis_timestamp: datetime = Field(default_factory=datetime.now)
    criteria_used: NicheAnalysisCriteria = Field(description="Critères utilisés pour l'analyse")


class NicheAnalysisRequest(BaseModel):
    """Requête d'analyse de niches."""
    
    criteria: NicheAnalysisCriteria = Field(default_factory=NicheAnalysisCriteria)
    target_categories: Optional[List[int]] = Field(
        default=None,
        description="Catégories spécifiques à analyser (optionnel)"
    )
    max_results: int = Field(
        default=10,
        description="Nombre maximum de niches à retourner"
    )


class NicheAnalysisResponse(BaseModel):
    """Réponse d'analyse de niches."""
    
    discovered_niches: List[DiscoveredNiche] = Field(description="Niches découvertes")
    total_categories_analyzed: int = Field(description="Nombre de catégories analysées")
    analysis_duration_seconds: float = Field(description="Durée de l'analyse")
    criteria_used: NicheAnalysisCriteria = Field(description="Critères appliqués")
    
    # Métriques globales
    avg_niche_score: float = Field(description="Score moyen des niches trouvées")
    best_niche_score: float = Field(description="Meilleur score trouvé")
    analysis_quality: str = Field(description="Qualité globale de l'analyse")


class CategoryOverview(BaseModel):
    """Aperçu d'une catégorie Keepa."""
    
    category_id: int = Field(description="ID catégorie Keepa")
    category_name: str = Field(description="Nom de la catégorie")
    parent_category: Optional[str] = Field(description="Catégorie parente")
    estimated_products: Optional[int] = Field(description="Nombre estimé de produits")
    last_analyzed: Optional[datetime] = Field(description="Dernière analyse")
    is_eligible: bool = Field(description="Éligible pour analyse niche")


class CategoriesListResponse(BaseModel):
    """Liste des catégories disponibles pour analyse."""
    
    categories: List[CategoryOverview] = Field(description="Catégories disponibles")
    total_eligible: int = Field(description="Nombre de catégories éligibles")
    recommended_categories: List[CategoryOverview] = Field(
        description="Catégories recommandées pour débuter"
    )


# Types utilitaires pour export
class NicheExportData(BaseModel):
    """Données formatées pour export CSV."""
    
    category_name: str
    niche_score: float
    avg_sellers: float
    avg_bsr: int
    profit_margin: float
    price_stability: float
    viable_products: int
    competition_level: str
    confidence_level: str
    
    # Paramètres pour AutoSourcing
    recommended_bsr_min: int
    recommended_bsr_max: int
    recommended_max_sellers: int
    recommended_min_margin: float