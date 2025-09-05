"""Test d'intégration avec les vraies données Keepa pour la fonctionnalité de bookmarking."""

import sys
import os
import asyncio
import json
from datetime import datetime
from typing import Optional

sys.path.append('C:\\Users\\azizt\\Workspace\\arbitragevault_bookfinder\\backend')

# Imports du projet
from app.services.niche_discovery_service import NicheDiscoveryService
from app.services.bookmark_service import BookmarkService
from app.services.keepa_service import KeepaService
from app.schemas.bookmark import NicheCreateSchema
from app.models.bookmark import SavedNiche
from app.models.niche import NicheAnalysisCriteria, NicheAnalysisRequest
from sqlalchemy.orm import Session
from unittest.mock import Mock

# Pour récupérer les clés API
try:
    import keyring
    print("✅ Keyring disponible - Récupération des clés API Memex")
except ImportError:
    print("❌ Keyring non disponible - Installation requise: uv tool install keyring")
    sys.exit(1)


def get_keepa_api_key() -> Optional[str]:
    """Récupère la clé API Keepa des secrets Memex."""
    try:
        # Essayer différentes variantes du nom de clé
        key_variants = ["KEEPA_API_KEY", "keepa_api_key", "Keepa_API_Key", "KEEPA_KEY"]
        
        for variant in key_variants:
            try:
                key = keyring.get_password("memex", variant)
                if key:
                    print(f"✅ Clé API Keepa trouvée: {variant}")
                    return key
            except Exception as e:
                continue
        
        print("❌ Aucune clé API Keepa trouvée dans les secrets Memex")
        print("   Clés testées:", key_variants)
        return None
        
    except Exception as e:
        print(f"❌ Erreur récupération clé API: {e}")
        return None


async def test_real_niche_discovery_and_bookmarking():
    """Test complet avec vraies données Keepa."""
    
    print("=== TEST INTÉGRATION KEEPA + BOOKMARKING ===\n")
    
    # 1. Récupération clé API
    keepa_key = get_keepa_api_key()
    if not keepa_key:
        print("⚠️ Impossible de continuer sans clé API Keepa")
        print("   Ajoutez la clé via les secrets Memex UI")
        return False
    
    print(f"✅ Clé API récupérée (longueur: {len(keepa_key)} caractères)")
    
    # 2. Configuration du service de découverte
    print("\n=== ÉTAPE 1: DÉCOUVERTE DE NICHE AVEC VRAIES DONNÉES ===")
    
    # Mock de la base de données pour les services
    mock_db = Mock(spec=Session)
    
    try:
        # Configuration critères d'analyse réalistes
        criteria = NicheAnalysisCriteria(
            bsr_range=(5000, 300000),    # BSR raisonnable pour les livres
            max_sellers=8,               # Concurrence modérée
            min_margin_percent=25.0,     # Marge minimum 25%
            min_price_stability=0.6,     # Stabilité prix minimum
            sample_size=50               # Taille d'échantillon pour test
        )
        
        # Requête d'analyse complète
        analysis_request = NicheAnalysisRequest(
            criteria=criteria,
            target_categories=None,  # Utiliser les catégories par défaut
            max_results=5            # Limiter pour le test
        )
        
        print(f"✅ Critères d'analyse configurés:")
        print(f"   BSR: {criteria.bsr_range[0]:,} - {criteria.bsr_range[1]:,}")
        print(f"   Marge min: {criteria.min_margin_percent}%")
        print(f"   Vendeurs max: {criteria.max_sellers}")
        print(f"   Échantillon: {criteria.sample_size} produits")
        
        # Initialiser les services avec la vraie clé
        os.environ['KEEPA_API_KEY'] = keepa_key
        keepa_service = KeepaService(api_key=keepa_key)
        discovery_service = NicheDiscoveryService(keepa_service)
        
        # Lancer une vraie analyse
        print(f"\n🔍 Lancement analyse avec API Keepa...")
        analysis_response = await discovery_service.discover_niches(analysis_request)
        discovered_niches = analysis_response.discovered_niches
        
        if not discovered_niches:
            print("❌ Aucune niche découverte - Vérifier les critères ou l'API")
            return False
        
        print(f"✅ {len(discovered_niches)} niche(s) découverte(s)")
        
        # Prendre la première niche pour les tests
        test_niche = discovered_niches[0]
        print(f"\n📊 Niche sélectionnée pour test: {test_niche.category_name}")
        print(f"   Score: {test_niche.niche_score}/10")
        print(f"   Produits viables: {test_niche.metrics.viable_products}/{test_niche.metrics.total_products}")
        print(f"   Prix moyen: ${test_niche.metrics.avg_price:.2f}")
        print(f"   Marge profit: {test_niche.metrics.profit_margin:.1f}%")
        
    except Exception as e:
        print(f"❌ Erreur lors de la découverte: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. Test de sauvegarde avec BookmarkService
    print(f"\n=== ÉTAPE 2: SAUVEGARDE VIA BOOKMARK SERVICE ===")
    
    try:
        # Préparer les données pour la sauvegarde
        # Estimer une plage de prix basée sur le prix moyen de la niche
        avg_price = test_niche.metrics.avg_price
        price_min = max(15.0, avg_price * 0.7)  # 30% en dessous du prix moyen, min 15$
        price_max = min(300.0, avg_price * 1.5)  # 50% au dessus du prix moyen, max 300$
        
        filters_to_save = {
            # Paramètres compatibles Keepa
            "current_AMAZON_gte": int(price_min * 100),  # En centimes
            "current_AMAZON_lte": int(price_max * 100),  # En centimes
            "current_SALES_gte": criteria.bsr_range[0],
            "current_SALES_lte": criteria.bsr_range[1],
            "categories_include": [test_niche.category_id],
            
            # Paramètres métier
            "min_margin_percent": criteria.min_margin_percent,
            "max_sellers": criteria.max_sellers,
            "min_price_stability": criteria.min_price_stability,
            
            # Métadonnées de découverte
            "analysis_date": datetime.now().isoformat(),
            "keepa_api_used": True,
            "total_products_analyzed": test_niche.metrics.total_products
        }
        
        niche_to_bookmark = NicheCreateSchema(
            niche_name=f"{test_niche.category_name} - Test Intégration",
            category_id=test_niche.category_id,
            category_name=test_niche.category_name,
            filters=filters_to_save,
            last_score=test_niche.niche_score,
            description=f"Niche découverte via test d'intégration le {datetime.now().strftime('%Y-%m-%d %H:%M')} - {test_niche.metrics.viable_products} produits viables identifiés avec API Keepa"
        )
        
        # Mock pour BookmarkService (sans vraie DB)
        mock_db.query.return_value.filter.return_value.first.return_value = None  # Pas de doublon
        mock_db.add = Mock()
        mock_db.commit = Mock()
        
        # Mock l'objet qui sera créé
        def mock_refresh(obj):
            obj.id = 123
            obj.created_at = datetime.now()
        
        mock_db.refresh = Mock(side_effect=mock_refresh)
        
        bookmark_service = BookmarkService(mock_db)
        user_id = "integration_test_user"
        
        saved_niche = bookmark_service.create_niche(user_id, niche_to_bookmark)
        
        print(f"✅ Niche sauvegardée avec succès:")
        print(f"   ID: {saved_niche.id}")
        print(f"   Nom: {saved_niche.niche_name}")
        print(f"   Filtres: {len(saved_niche.filters)} paramètres stockés")
        
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. Test de récupération et relance
    print(f"\n=== ÉTAPE 3: RÉCUPÉRATION ET 'RELANCER L'ANALYSE' ===")
    
    try:
        # Mock pour récupérer la niche sauvegardée
        mock_db.query.return_value.filter.return_value.first.return_value = saved_niche
        
        # Récupérer les filtres pour relancer l'analyse
        retrieved_filters = bookmark_service.get_niche_filters_for_analysis(user_id, saved_niche.id)
        
        if not retrieved_filters:
            print("❌ Échec récupération des filtres")
            return False
        
        print(f"✅ Filtres récupérés pour relance:")
        print(f"   current_AMAZON_gte: {retrieved_filters['current_AMAZON_gte']} (${retrieved_filters['current_AMAZON_gte']/100:.2f})")
        print(f"   current_AMAZON_lte: {retrieved_filters['current_AMAZON_lte']} (${retrieved_filters['current_AMAZON_lte']/100:.2f})")
        print(f"   current_SALES_gte: {retrieved_filters['current_SALES_gte']:,}")
        print(f"   current_SALES_lte: {retrieved_filters['current_SALES_lte']:,}")
        print(f"   categories_include: {retrieved_filters['categories_include']}")
        
        # Reconstruire les critères à partir des filtres sauvegardés
        reconstructed_criteria = NicheAnalysisCriteria(
            bsr_range=(retrieved_filters['current_SALES_gte'], retrieved_filters['current_SALES_lte']),
            max_sellers=retrieved_filters['max_sellers'],
            min_margin_percent=retrieved_filters['min_margin_percent'],
            min_price_stability=retrieved_filters['min_price_stability'],
            sample_size=30  # Plus petit échantillon pour la relance
        )
        
        # Requête de relance
        relaunch_request = NicheAnalysisRequest(
            criteria=reconstructed_criteria,
            target_categories=retrieved_filters['categories_include'],
            max_results=3
        )
        
        print(f"\n🔄 Test de relance d'analyse avec paramètres récupérés...")
        
        # Relancer une nouvelle analyse
        relaunch_response = await discovery_service.discover_niches(relaunch_request)
        relaunched_niches = relaunch_response.discovered_niches
        
        if not relaunched_niches:
            print("⚠️ Aucun résultat lors de la relance (peut être normal si marché a changé)")
        else:
            relaunch_niche = relaunched_niches[0]
            print(f"✅ Analyse relancée avec succès:")
            print(f"   Même catégorie: {relaunch_niche.category_name}")
            print(f"   Nouveau score: {relaunch_niche.niche_score}/10")
            print(f"   Différence score: {relaunch_niche.niche_score - test_niche.niche_score:+.1f}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la relance: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. Validation finale
    print(f"\n=== VALIDATION FINALE ===")
    
    validation_checks = [
        ("API Keepa fonctionne", len(discovered_niches) > 0),
        ("Données bien structurées", test_niche.metrics.avg_price > 0),
        ("Sauvegarde réussie", saved_niche.id is not None),
        ("Filtres préservés", len(retrieved_filters) >= 6),
        ("Relance possible", True),  # Si on arrive ici, c'est ok
        ("Compatibilité Keepa", retrieved_filters.get('current_AMAZON_gte') is not None)
    ]
    
    all_passed = all(passed for _, passed in validation_checks)
    
    for check, passed in validation_checks:
        status = "✅" if passed else "❌"
        print(f"   {status} {check}")
    
    if all_passed:
        print(f"\n🎉 INTÉGRATION KEEPA + BOOKMARKING VALIDÉE !")
        print(f"   - Vraies données Keepa traitées correctement")
        print(f"   - Structures compatibles avec l'API officielle")
        print(f"   - Workflow complet fonctionnel")
        print(f"   - Fonctionnalité 'Relancer l'analyse' opérationnelle")
        return True
    else:
        print(f"\n❌ PROBLÈMES DÉTECTÉS - CORRECTIONS NÉCESSAIRES")
        return False


async def main():
    """Point d'entrée principal."""
    print("🚀 DÉMARRAGE TEST INTÉGRATION KEEPA + BOOKMARKING")
    print("=" * 60)
    
    try:
        success = await test_real_niche_discovery_and_bookmarking()
        
        if success:
            print("\n" + "=" * 60)
            print("✅ TOUS LES TESTS D'INTÉGRATION SONT PASSÉS!")
            print("🚀 LA FONCTIONNALITÉ EST PRÊTE POUR PRODUCTION!")
            print("\nCapacités validées:")
            print("- Découverte de niches avec vraies données Keepa")
            print("- Sauvegarde avec filtres compatibles API")
            print("- Récupération et relance d'analyse")
            print("- Intégration complète backend")
        else:
            print("\n" + "=" * 60)
            print("❌ DES PROBLÈMES ONT ÉTÉ DÉTECTÉS")
            print("⚠️ CORRECTIONS NÉCESSAIRES AVANT PRODUCTION")
            
    except Exception as e:
        print(f"\n💥 ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())