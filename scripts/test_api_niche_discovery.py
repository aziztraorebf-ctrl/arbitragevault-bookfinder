#!/usr/bin/env python3
"""
Test API Niche Discovery - Phase 1 KISS
========================================

Test des endpoints API sans appels Keepa réels.
"""

import sys
from pathlib import Path

# Ajouter le chemin du backend au PYTHONPATH
backend_path = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_path))

def test_api_integration():
    """Test d'intégration API basique."""
    print("🔌 TEST INTÉGRATION API NICHE DISCOVERY")
    print("=" * 50)
    
    try:
        # Test import application
        from app.main import app
        print("✅ FastAPI app importée avec succès")
        
        # Test import router
        from app.routers.niche_discovery import router
        print("✅ Niche Discovery router importé")
        print(f"   Prefix: {router.prefix}")
        print(f"   Tags: {router.tags}")
        
        # Test routes enregistrées
        routes = [route.path for route in app.routes]
        niche_routes = [r for r in routes if 'niche' in r]
        print(f"✅ Routes Niche Discovery: {len(niche_routes)}")
        for route in niche_routes:
            print(f"   • {route}")
        
        # Test modèles
        from app.models.niche import NicheAnalysisRequest, NicheAnalysisResponse
        print("✅ Modèles Pydantic importés")
        
        # Test services  
        from app.services.niche_discovery_service import NicheDiscoveryService
        from app.services.niche_scoring_service import NicheScoringService
        print("✅ Services importés")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur intégration: {e}")
        return False

def main():
    """Test principal."""
    success = test_api_integration()
    
    if success:
        print("\n🎯 INTÉGRATION API: RÉUSSIE")
        print("Prêt pour tests E2E avec Keepa API")
    else:
        print("\n❌ INTÉGRATION API: ÉCHOUÉE")
    
    return success

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1)