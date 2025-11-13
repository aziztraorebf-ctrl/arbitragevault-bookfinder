#!/usr/bin/env python3
"""
Test end-to-end du workflow AutoSourcing avec vraie intégration.
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

import asyncio
import keyring
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.autosourcing_service import AutoSourcingService  
from app.services.keepa_service import KeepaService

async def test_autosourcing_workflow():
    """Test complet du workflow AutoSourcing."""
    print("=== TEST WORKFLOW AUTOSOURCING COMPLET ===")
    
    # Setup
    keepa_key = keyring.get_password('memex', 'KEEPA_API_KEY')
    if not keepa_key:
        print("❌ No Keepa API key found")
        return
    
    # Base de données
    database_url = "sqlite:///./autosourcing.db"
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Services
    keepa_service = KeepaService(api_key=keepa_key, concurrency=1)
    
    try:
        # Test avec une session de base de données
        with SessionLocal() as db:
            # Créer le service AutoSourcing  
            autosourcing_service = AutoSourcingService(db, keepa_service)
            
            print("\n1. ✅ Services initialisés")
            
            # Configuration de découverte
            discovery_config = {
                "categories": ["Books", "Textbooks"],
                "price_range": {"min": 10, "max": 100},
                "bsr_range": {"max": 50000},
                "max_results": 5
            }
            
            # Configuration de scoring
            scoring_config = {
                "roi_min": 25.0,
                "velocity_min": 60.0,
                "confidence_min": 70.0
            }
            
            print("\n2. 🚀 Lancement recherche AutoSourcing...")
            print(f"   Critères: {discovery_config}")
            print(f"   Scoring: {scoring_config}")
            
            # Lancer la recherche
            job = await autosourcing_service.run_custom_search(
                discovery_config=discovery_config,
                scoring_config=scoring_config,
                profile_name="Test Integration",
                profile_id=None
            )
            
            print(f"\n3. ✅ Job complété: {job.id}")
            print(f"   Status: {job.status}")
            print(f"   Testés: {job.total_tested}")
            print(f"   Sélectionnés: {job.total_selected}")
            print(f"   Durée: {job.duration_ms}ms")
            
            # Récupérer les résultats
            if job.total_selected > 0:
                print(f"\n4. 📊 Résultats:")
                for i, pick in enumerate(job.picks[:3], 1):
                    print(f"   {i}. {pick.title}")
                    print(f"      ASIN: {pick.asin}")
                    print(f"      ROI: {pick.roi_percentage}%")
                    print(f"      Prix: ${pick.current_price}")
                    print(f"      Rating: {pick.overall_rating}")
                    print()
            else:
                print("\n4. ⚠️ Aucun résultat sélectionné")
            
            print("✅ TEST WORKFLOW COMPLET RÉUSSI")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await keepa_service.close()

if __name__ == "__main__":
    asyncio.run(test_autosourcing_workflow())