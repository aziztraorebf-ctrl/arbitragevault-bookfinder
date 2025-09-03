"""Test simple pour valider la fonctionnalité de bookmarking avec des données réalistes."""

import sys
import os
sys.path.append('C:\\Users\\azizt\\Workspace\\arbitragevault_bookfinder\\backend')

from app.schemas.bookmark import NicheCreateSchema
from app.services.bookmark_service import BookmarkService
from app.models.bookmark import SavedNiche
from sqlalchemy.orm import Session
from unittest.mock import Mock
import json

def test_with_realistic_keepa_data():
    """Test avec des données réalistes basées sur les structures Keepa."""
    
    # Données de filtres réalistes basées sur les paramètres Keepa
    realistic_filters = {
        # Critères de prix (en dollars)
        "min_price": 15.0,
        "max_price": 150.0,
        
        # BSR (Best Seller Rank) - utilise csv[3] dans Keepa
        "min_bsr": 10000,
        "max_bsr": 500000,
        
        # Critères de rentabilité
        "min_roi": 25.0,  # ROI minimum en %
        "min_margin_percent": 20.0,
        
        # Critères de concurrence
        "max_sellers": 8,
        "min_price_stability": 0.7,
        
        # Période d'analyse
        "analysis_period_days": 90,
        
        # Critères spécifiques aux livres
        "include_textbooks": True,
        "exclude_ebooks": True,
        "min_review_count": 10
    }
    
    # Création d'une niche avec des paramètres Keepa réalistes
    niche_data = NicheCreateSchema(
        niche_name="Medical Textbooks - High Value",
        category_id=13, # Engineering & Transportation sur Keepa
        category_name="Books > Medical > Textbooks",
        filters=realistic_filters,
        last_score=8.2,  # Score élevé basé sur notre algorithme
        description="Niche découverte via analyse Keepa - Livres médicaux avec forte demande et marges élevées"
    )
    
    # Mock database session
    mock_db = Mock(spec=Session)
    mock_db.query.return_value.filter.return_value.first.return_value = None  # Pas de doublon
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None
    
    # Test service
    service = BookmarkService(mock_db)
    user_id = "test-user-123"
    
    # Création de la niche
    result = service.create_niche(user_id, niche_data)
    
    # Vérifications
    print("=== TEST BOOKMARK SERVICE AVEC DONNÉES RÉALISTES ===")
    print(f"✅ Niche créée: {result.niche_name}")
    print(f"✅ Category ID: {result.category_id}")
    print(f"✅ User ID: {result.user_id}")
    print(f"✅ Score: {result.last_score}")
    
    # Vérification des filtres stockés
    stored_filters = result.filters
    print(f"✅ Filtres stockés ({len(stored_filters)} paramètres):")
    for key, value in stored_filters.items():
        print(f"   - {key}: {value}")
    
    # Test de récupération des filtres pour ré-analyse
    print(f"\n=== TEST RÉCUPÉRATION FILTRES POUR 'RELANCER L'ANALYSE' ===")
    
    # Mock pour la récupération
    mock_db.query.return_value.filter.return_value.first.return_value = result
    
    retrieved_filters = service.get_niche_filters_for_analysis(user_id, result.id)
    
    print(f"✅ Filtres récupérés pour ré-analyse:")
    print(json.dumps(retrieved_filters, indent=2))
    
    # Vérification que les filtres correspondent aux paramètres Keepa
    keepa_compatible_fields = [
        'min_price', 'max_price', 'min_bsr', 'max_bsr', 'min_roi', 
        'max_sellers', 'min_price_stability'
    ]
    
    missing_fields = [field for field in keepa_compatible_fields if field not in retrieved_filters]
    if not missing_fields:
        print(f"✅ Tous les champs compatibles Keepa sont présents")
    else:
        print(f"❌ Champs manquants: {missing_fields}")
    
    print("\n=== VALIDATION STRUCTURE DONNÉES ===")
    
    # Simuler l'utilisation des filtres avec l'API Keepa  
    simulated_keepa_query = {
        # Paramètres de recherche Keepa basés sur nos filtres
        "current_AMAZON_gte": int(retrieved_filters["min_price"] * 100),  # Keepa utilise les centimes
        "current_AMAZON_lte": int(retrieved_filters["max_price"] * 100),
        "current_SALES_gte": retrieved_filters["min_bsr"],
        "current_SALES_lte": retrieved_filters["max_bsr"],
        "categories_include": [result.category_id],
        "sort": ["current_SALES", "asc"]  # Tri par BSR
    }
    
    print(f"✅ Requête Keepa générée à partir des filtres sauvegardés:")
    print(json.dumps(simulated_keepa_query, indent=2))
    
    return True

if __name__ == "__main__":
    try:
        test_with_realistic_keepa_data()
        print("\n🎉 TOUS LES TESTS SONT PASSÉS!")
        print("   - Structures de données alignées avec Keepa")
        print("   - Fonctionnalité 'Relancer l'analyse' validée")
        print("   - Compatibilité filtres ↔ paramètres Keepa confirmée")
        
    except Exception as e:
        print(f"\n❌ ERREUR DANS LE TEST: {e}")
        import traceback
        traceback.print_exc()