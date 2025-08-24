#!/usr/bin/env python3
"""
Test AutoSourcing end-to-end avec vraie intégration Keepa
"""
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.services.autosourcing_service import AutoSourcingService
from app.models.autosourcing import DiscoveryRequest, SearchConfig
import tempfile

async def test_autosourcing_with_real_keepa():
    """Test complet du workflow AutoSourcing avec vraie API Keepa"""
    
    print("🚀 Test AutoSourcing avec Keepa réel")
    
    # Configuration DB temporaire
    temp_db = tempfile.mktemp(suffix='.db')
    database_url = f"sqlite+aiosqlite:///{temp_db}"
    
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Création des tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Base de données initialisée")
    
    # Test du service AutoSourcing
    async with async_session() as db:
        autosourcing_service = AutoSourcingService(db)
        
        # Configuration de recherche
        search_config = SearchConfig(
            categories=["Books"],
            price_range_min=10.0,
            price_range_max=50.0,
            bsr_threshold=100000,
            profit_margin_min=0.20,
            roi_threshold=0.30
        )
        
        # Requête de découverte
        discovery_request = DiscoveryRequest(
            name="Test Keepa Integration",
            search_config=search_config,
            max_products=5
        )
        
        print("📡 Lancement découverte produits...")
        
        try:
            # Appel au service avec session async correcte
            result = await autosourcing_service.discover_products(discovery_request)
            
            print(f"✅ Découverte terminée!")
            print(f"  Request ID: {result.id}")
            print(f"  Status: {result.status}")
            print(f"  Produits trouvés: {len(result.discovered_products)}")
            
            # Affichage des premiers résultats
            for i, product in enumerate(result.discovered_products[:3]):
                print(f"\n📚 Produit {i+1}:")
                print(f"  ASIN: {product.asin}")
                print(f"  Score: {product.score:.2f}")
                print(f"  Profit potentiel: ${product.profit_estimate:.2f}")
                print(f"  ROI: {product.roi_estimate:.1%}")
                
            await db.commit()
            
        except Exception as e:
            print(f"❌ Erreur service AutoSourcing: {e}")
            print(f"Type: {type(e)}")
            import traceback
            traceback.print_exc()
    
    await engine.dispose()
    os.unlink(temp_db)
    print("\n🎉 Test AutoSourcing terminé!")

if __name__ == "__main__":
    asyncio.run(test_autosourcing_with_real_keepa())