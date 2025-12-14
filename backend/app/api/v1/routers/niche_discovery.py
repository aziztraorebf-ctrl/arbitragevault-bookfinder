"""
Niche Discovery API Routes
==========================

Routes API pour la découverte de niches de marché.
Phase 1 KISS: Endpoints simples pour analyse et export.
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import Response

from app.models.niche import (
    NicheAnalysisRequest, 
    NicheAnalysisResponse, 
    CategoriesListResponse,
    NicheExportData
)
from app.services.niche_discovery_service import NicheDiscoveryService
from app.services.keepa_service_factory import get_keepa_service
from app.core.auth import get_current_user
from app.models.user import User

# Setup
router = APIRouter(prefix="/api/niche-discovery", tags=["niche-discovery"])
logger = logging.getLogger(__name__)


def get_niche_discovery_service() -> NicheDiscoveryService:
    """Dependency injection pour NicheDiscoveryService."""
    keepa_service = get_keepa_service()
    return NicheDiscoveryService(keepa_service)


@router.post("/analyze", response_model=NicheAnalysisResponse)
async def analyze_niches(
    request: NicheAnalysisRequest,
    service: NicheDiscoveryService = Depends(get_niche_discovery_service),
    current_user: User = Depends(get_current_user)
):
    """
    Analyse les niches de marché selon les critères fournis.
    
    - **criteria**: Critères d'analyse (BSR, vendeurs, marge, etc.)
    - **target_categories**: Catégories spécifiques à analyser (optionnel)
    - **max_results**: Nombre maximum de niches à retourner (défaut: 10)
    
    Returns:
        - Liste des niches découvertes avec scores et métriques
        - Statistiques d'analyse
        - Recommandations pour AutoSourcing
    """
    try:
        logger.info(f"Analyse niches demandée par utilisateur {current_user.email}")
        
        # Validation basique
        if request.criteria.bsr_range[0] >= request.criteria.bsr_range[1]:
            raise HTTPException(
                status_code=400, 
                detail="BSR range invalide: min doit être < max"
            )
        
        if request.criteria.max_sellers <= 0:
            raise HTTPException(
                status_code=400, 
                detail="Nombre maximum de vendeurs doit être > 0"
            )
        
        if request.max_results <= 0 or request.max_results > 50:
            raise HTTPException(
                status_code=400, 
                detail="max_results doit être entre 1 et 50"
            )
        
        # Exécuter analyse
        response = await service.discover_niches(request)
        
        logger.info(f"Analyse terminée: {len(response.discovered_niches)} niches trouvées "
                   f"en {response.analysis_duration_seconds}s")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur analyse niches: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur interne lors de l'analyse: {str(e)}"
        )


@router.get("/categories", response_model=CategoriesListResponse)
async def get_available_categories(
    service: NicheDiscoveryService = Depends(get_niche_discovery_service),
    current_user: User = Depends(get_current_user)
):
    """
    Retourne les catégories disponibles pour l'analyse de niches.
    
    Returns:
        - Liste des catégories éligibles
        - Catégories recommandées pour débuter
        - Statistiques globales
    """
    try:
        logger.info(f"Liste catégories demandée par {current_user.email}")
        
        response = await service.get_available_categories()
        
        logger.debug(f"Catégories retournées: {len(response.categories)} total, "
                    f"{len(response.recommended_categories)} recommandées")
        
        return response
        
    except Exception as e:
        logger.error(f"Erreur récupération catégories: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur récupération catégories: {str(e)}"
        )


@router.post("/export/csv")
async def export_niches_csv(
    discovered_niches: List[Dict[str, Any]],
    service: NicheDiscoveryService = Depends(get_niche_discovery_service),
    current_user: User = Depends(get_current_user)
):
    """
    Exporte les niches découvertes au format CSV.
    
    - **discovered_niches**: Liste des niches à exporter (format JSON)
    
    Returns:
        - Fichier CSV téléchargeable
        - Headers optimisés pour Excel
    """
    try:
        logger.info(f"Export CSV demandé par {current_user.email} - "
                   f"{len(discovered_niches)} niches")
        
        if not discovered_niches:
            raise HTTPException(
                status_code=400, 
                detail="Aucune niche à exporter"
            )
        
        # Convertir en objets DiscoveredNiche (parsing basique pour Phase 1)
        from app.models.niche import DiscoveredNiche
        niche_objects = []
        
        for niche_data in discovered_niches:
            try:
                niche_obj = DiscoveredNiche.parse_obj(niche_data)
                niche_objects.append(niche_obj)
            except Exception as parse_error:
                logger.warning(f"Erreur parsing niche: {parse_error}")
                continue
        
        if not niche_objects:
            raise HTTPException(
                status_code=400, 
                detail="Aucune niche valide à exporter"
            )
        
        # Générer données d'export
        export_data = await service.export_niches_data(niche_objects)
        
        # Créer CSV
        csv_content = _generate_csv_content(export_data)
        
        # Headers pour téléchargement
        filename = f"niches_discovery_{current_user.id}_{int(time.time())}.csv"
        headers = {
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "text/csv; charset=utf-8"
        }
        
        logger.info(f"Export CSV généré: {filename} ({len(export_data)} niches)")
        
        return Response(
            content=csv_content,
            headers=headers,
            media_type="text/csv"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur export CSV: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur génération CSV: {str(e)}"
        )


@router.get("/stats")
async def get_service_stats(
    service: NicheDiscoveryService = Depends(get_niche_discovery_service),
    current_user: User = Depends(get_current_user)
):
    """
    Retourne les statistiques du service Niche Discovery.
    
    Returns:
        - Configuration système
        - Métriques cache
        - Informations sur l'algorithme de scoring
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(
                status_code=403, 
                detail="Accès réservé aux administrateurs"
            )
        
        stats = service.get_service_stats()
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur stats service: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur récupération stats: {str(e)}"
        )


# Fonctions utilitaires

def _generate_csv_content(export_data: List[NicheExportData]) -> str:
    """Génère le contenu CSV à partir des données d'export."""
    import csv
    import io
    
    output = io.StringIO()
    
    # Headers CSV
    fieldnames = [
        "Category Name",
        "Niche Score",
        "Avg Sellers",
        "Avg BSR", 
        "Profit Margin (%)",
        "Price Stability",
        "Viable Products",
        "Competition Level",
        "Confidence Level",
        "Recommended BSR Min",
        "Recommended BSR Max", 
        "Recommended Max Sellers",
        "Recommended Min Margin (%)"
    ]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    # Données
    for niche in export_data:
        writer.writerow({
            "Category Name": niche.category_name,
            "Niche Score": niche.niche_score,
            "Avg Sellers": round(niche.avg_sellers, 1),
            "Avg BSR": niche.avg_bsr,
            "Profit Margin (%)": round(niche.profit_margin, 1),
            "Price Stability": round(niche.price_stability, 2),
            "Viable Products": niche.viable_products,
            "Competition Level": niche.competition_level,
            "Confidence Level": niche.confidence_level,
            "Recommended BSR Min": niche.recommended_bsr_min,
            "Recommended BSR Max": niche.recommended_bsr_max,
            "Recommended Max Sellers": niche.recommended_max_sellers,
            "Recommended Min Margin (%)": niche.recommended_min_margin
        })
    
    return output.getvalue()


# Import time pour filename timestamp
import time