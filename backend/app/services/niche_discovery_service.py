"""
Niche Discovery Service - Service principal de découverte de niches
==================================================================

Service orchestrant la découverte de niches de marché rentables
avec faible concurrence pour optimiser le taux de réussite d'arbitrage.

Phase 1 KISS: Analyse de catégories prédéfinies avec métriques simples.
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
import time

from app.models.niche import (
    NicheAnalysisRequest, 
    NicheAnalysisResponse, 
    DiscoveredNiche,
    CategoryOverview,
    CategoriesListResponse,
    NicheExportData
)
from app.services.keepa_service import KeepaService
from app.services.category_analyzer import CategoryAnalyzer
from app.services.niche_scoring_service import NicheScoringService

logger = logging.getLogger(__name__)


class NicheDiscoveryService:
    """Service principal de découverte de niches de marché."""
    
    def __init__(self, keepa_service: KeepaService):
        self.keepa_service = keepa_service
        self.category_analyzer = CategoryAnalyzer(keepa_service)
        self.scoring_service = NicheScoringService()
        
        # Cache simple pour éviter re-calculs fréquents
        self._analysis_cache = {}
        self._cache_ttl = 3600  # 1 heure en secondes
    
    async def discover_niches(self, request: NicheAnalysisRequest) -> NicheAnalysisResponse:
        """
        Découvre et classe les meilleures niches selon les critères.
        
        Args:
            request: Critères d'analyse et paramètres
            
        Returns:
            NicheAnalysisResponse avec niches découvertes et classées
        """
        start_time = time.time()
        
        try:
            logger.info(f"Début découverte niches - Critères: BSR {request.criteria.bsr_range}, "
                       f"Vendeurs max: {request.criteria.max_sellers}, "
                       f"Marge min: {request.criteria.min_margin_percent}%")
            
            # Déterminer catégories à analyser
            target_categories = await self._determine_target_categories(request)
            
            if not target_categories:
                logger.warning("Aucune catégorie cible trouvée pour l'analyse")
                return self._create_empty_response(request, start_time)
            
            # Analyser catégories en parallèle (avec limite concurrence)
            discovered_niches = await self._analyze_categories_parallel(
                target_categories, 
                request.criteria
            )
            
            # Filtrer et classer les résultats
            filtered_niches = self._filter_and_rank_niches(
                discovered_niches, 
                request.max_results
            )
            
            # Créer réponse finale
            analysis_duration = time.time() - start_time
            response = self._create_analysis_response(
                filtered_niches,
                len(target_categories),
                analysis_duration,
                request.criteria
            )
            
            logger.info(f"Découverte terminée - {len(filtered_niches)} niches trouvées "
                       f"en {analysis_duration:.2f}s")
            
            return response
            
        except Exception as e:
            logger.error(f"Erreur découverte niches: {e}")
            return self._create_error_response(request, start_time, str(e))
    
    async def get_available_categories(self) -> CategoriesListResponse:
        """Retourne les catégories disponibles pour analyse."""
        try:
            categories = self.category_analyzer.get_available_categories()
            recommended_ids = self.category_analyzer.get_recommended_categories()
            
            recommended_categories = [
                cat for cat in categories 
                if cat.category_id in recommended_ids
            ]
            
            return CategoriesListResponse(
                categories=categories,
                total_eligible=len(categories),
                recommended_categories=recommended_categories
            )
            
        except Exception as e:
            logger.error(f"Erreur récupération catégories: {e}")
            return CategoriesListResponse(
                categories=[],
                total_eligible=0,
                recommended_categories=[]
            )
    
    async def export_niches_data(self, discovered_niches: List[DiscoveredNiche]) -> List[NicheExportData]:
        """Formate les niches pour export CSV."""
        export_data = []
        
        for niche in discovered_niches:
            export_data.append(NicheExportData(
                category_name=niche.category_name,
                niche_score=niche.niche_score,
                avg_sellers=niche.metrics.avg_sellers,
                avg_bsr=int(niche.metrics.avg_bsr),
                profit_margin=niche.metrics.profit_margin,
                price_stability=niche.metrics.price_stability,
                viable_products=niche.metrics.viable_products,
                competition_level=niche.metrics.competition_level,
                confidence_level=niche.confidence_level,
                
                # Paramètres recommandés pour AutoSourcing
                recommended_bsr_min=int(niche.criteria_used.bsr_range[0]),
                recommended_bsr_max=int(niche.criteria_used.bsr_range[1]),
                recommended_max_sellers=niche.criteria_used.max_sellers,
                recommended_min_margin=niche.criteria_used.min_margin_percent
            ))
        
        return export_data
    
    async def _determine_target_categories(self, request: NicheAnalysisRequest) -> List[int]:
        """Détermine les catégories à analyser selon la requête."""
        if request.target_categories:
            # Catégories spécifiques demandées
            return request.target_categories
        else:
            # Utiliser catégories recommandées par défaut (Phase 1 KISS)
            return self.category_analyzer.get_recommended_categories()
    
    async def _analyze_categories_parallel(
        self, 
        category_ids: List[int], 
        criteria
    ) -> List[DiscoveredNiche]:
        """Analyse les catégories en parallèle avec limite de concurrence."""
        
        discovered_niches = []
        semaphore = asyncio.Semaphore(3)  # Max 3 catégories simultanées
        
        async def analyze_single_category(category_id: int) -> Optional[DiscoveredNiche]:
            async with semaphore:
                try:
                    # Vérifier cache d'abord
                    cached_result = self._get_cached_analysis(category_id, criteria)
                    if cached_result:
                        logger.debug(f"Utilisation cache pour catégorie {category_id}")
                        return cached_result
                    
                    # Analyser catégorie
                    metrics = await self.category_analyzer.analyze_category(category_id, criteria)
                    if not metrics:
                        return None
                    
                    # Calculer score et classements
                    score, confidence, quality = self.scoring_service.calculate_niche_score(
                        metrics, criteria
                    )
                    
                    # Niveau de concurrence
                    competition_level = self.scoring_service.classify_competition_level(
                        metrics.avg_sellers
                    )
                    metrics.competition_level = competition_level
                    
                    # Créer niche découverte
                    category_name = self.category_analyzer.target_categories.get(
                        category_id, f"Category {category_id}"
                    )
                    
                    niche = DiscoveredNiche(
                        category_name=category_name,
                        category_id=category_id,
                        metrics=metrics,
                        niche_score=score,
                        confidence_level=confidence,
                        sample_quality=quality,
                        criteria_used=criteria
                    )
                    
                    # Mettre en cache
                    self._cache_analysis(category_id, criteria, niche)
                    
                    return niche
                    
                except Exception as e:
                    logger.error(f"Erreur analyse catégorie {category_id}: {e}")
                    return None
        
        # Lancer analyses en parallèle
        tasks = [analyze_single_category(cat_id) for cat_id in category_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrer résultats valides
        for result in results:
            if isinstance(result, DiscoveredNiche):
                discovered_niches.append(result)
            elif isinstance(result, Exception):
                logger.warning(f"Tâche échouée: {result}")
        
        return discovered_niches
    
    def _filter_and_rank_niches(
        self, 
        discovered_niches: List[DiscoveredNiche], 
        max_results: int
    ) -> List[DiscoveredNiche]:
        """Filtre et classe les niches découvertes."""
        
        # Filtrer niches avec score minimum (≥4.0 pour être "viable")
        viable_niches = [
            niche for niche in discovered_niches 
            if niche.niche_score >= 4.0
        ]
        
        # Trier par score décroissant
        ranked_niches = sorted(
            viable_niches, 
            key=lambda n: n.niche_score, 
            reverse=True
        )
        
        # Limiter résultats
        return ranked_niches[:max_results]
    
    def _create_analysis_response(
        self,
        discovered_niches: List[DiscoveredNiche],
        total_categories: int,
        duration: float,
        criteria
    ) -> NicheAnalysisResponse:
        """Crée la réponse d'analyse finale."""
        
        # Métriques globales
        avg_score = sum(n.niche_score for n in discovered_niches) / len(discovered_niches) if discovered_niches else 0.0
        best_score = max((n.niche_score for n in discovered_niches), default=0.0)
        
        # Évaluation qualité globale
        if avg_score >= 7.0 and len(discovered_niches) >= 5:
            analysis_quality = "Excellent"
        elif avg_score >= 6.0 and len(discovered_niches) >= 3:
            analysis_quality = "Good"
        elif avg_score >= 5.0:
            analysis_quality = "Fair"
        else:
            analysis_quality = "Poor"
        
        return NicheAnalysisResponse(
            discovered_niches=discovered_niches,
            total_categories_analyzed=total_categories,
            analysis_duration_seconds=round(duration, 2),
            criteria_used=criteria,
            avg_niche_score=round(avg_score, 1),
            best_niche_score=round(best_score, 1),
            analysis_quality=analysis_quality
        )
    
    def _create_empty_response(self, request: NicheAnalysisRequest, start_time: float) -> NicheAnalysisResponse:
        """Crée une réponse vide en cas d'absence de données."""
        duration = time.time() - start_time
        
        return NicheAnalysisResponse(
            discovered_niches=[],
            total_categories_analyzed=0,
            analysis_duration_seconds=round(duration, 2),
            criteria_used=request.criteria,
            avg_niche_score=0.0,
            best_niche_score=0.0,
            analysis_quality="No Data"
        )
    
    def _create_error_response(self, request: NicheAnalysisRequest, start_time: float, error: str) -> NicheAnalysisResponse:
        """Crée une réponse d'erreur."""
        duration = time.time() - start_time
        
        return NicheAnalysisResponse(
            discovered_niches=[],
            total_categories_analyzed=0,
            analysis_duration_seconds=round(duration, 2),
            criteria_used=request.criteria,
            avg_niche_score=0.0,
            best_niche_score=0.0,
            analysis_quality=f"Error: {error}"
        )
    
    def _get_cached_analysis(self, category_id: int, criteria) -> Optional[DiscoveredNiche]:
        """Récupère analyse en cache si valide."""
        cache_key = f"{category_id}_{hash(str(criteria))}"
        
        if cache_key in self._analysis_cache:
            cached_data, timestamp = self._analysis_cache[cache_key]
            
            # Vérifier TTL
            if time.time() - timestamp < self._cache_ttl:
                return cached_data
            else:
                # Supprimer entrée expirée
                del self._analysis_cache[cache_key]
        
        return None
    
    def _cache_analysis(self, category_id: int, criteria, niche: DiscoveredNiche):
        """Met en cache une analyse."""
        cache_key = f"{category_id}_{hash(str(criteria))}"
        self._analysis_cache[cache_key] = (niche, time.time())
        
        # Nettoyage cache si trop volumineux
        if len(self._analysis_cache) > 50:
            self._cleanup_cache()
    
    def _cleanup_cache(self):
        """Nettoie le cache des entrées expirées."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self._analysis_cache.items()
            if current_time - timestamp >= self._cache_ttl
        ]
        
        for key in expired_keys:
            del self._analysis_cache[key]
        
        logger.debug(f"Cache nettoyé: {len(expired_keys)} entrées supprimées")
    
    def get_service_stats(self) -> Dict:
        """Retourne les statistiques du service."""
        return {
            "service_name": "NicheDiscoveryService",
            "version": "1.0.0-KISS",
            "cache_entries": len(self._analysis_cache),
            "available_categories": len(self.category_analyzer.target_categories),
            "scoring_system": self.scoring_service.get_scoring_explanation(),
            "phase": "Phase 1 KISS - Predefined categories analysis"
        }