"""Test de débogage pour la sauvegarde des bookmarks."""

import sys
import os
import asyncio
from datetime import datetime
from unittest.mock import Mock, MagicMock

sys.path.append('C:\\Users\\azizt\\Workspace\\arbitragevault_bookfinder\\backend')

from app.services.bookmark_service import BookmarkService
from app.schemas.bookmark import NicheCreateSchema
from app.models.bookmark import SavedNiche
from sqlalchemy.orm import Session

try:
    import keyring
except ImportError:
    print("❌ Keyring requis: uv tool install keyring")
    sys.exit(1)


def test_bookmark_save_mock():
    """Test spécifique de la sauvegarde avec mock détaillé."""
    
    print("=== DEBUG SAUVEGARDE BOOKMARK ===\n")
    
    # Configuration du mock plus détaillée
    mock_db = Mock(spec=Session)
    
    # Mock pour vérifier qu'il n'y a pas de doublon
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    # Mock pour l'ajout
    mock_saved_niche = SavedNiche(
        id=123,
        niche_name="Test Niche - Integration",
        category_id=4142,
        category_name="Engineering & Transportation > Engineering",
        filters={
            "current_AMAZON_gte": 10556,
            "current_AMAZON_lte": 22621,
            "current_SALES_gte": 5000,
            "current_SALES_lte": 300000,
            "categories_include": [4142],
            "min_margin_percent": 25.0,
            "max_sellers": 8,
            "min_price_stability": 0.6,
            "analysis_date": datetime.now().isoformat(),
            "keepa_api_used": True,
            "total_products_analyzed": 15
        },
        last_score=7.7,
        description="Test niche pour intégration Keepa",
        user_id="integration_test_user",
        created_at=datetime.now()
    )
    
    # Configuration des mocks
    mock_db.add = Mock()
    mock_db.commit = Mock()
    mock_db.refresh = Mock(side_effect=lambda obj: setattr(obj, 'id', 123))
    
    try:
        # Initialisation du service
        bookmark_service = BookmarkService(mock_db)
        user_id = "integration_test_user"
        
        # Création du schéma
        niche_to_create = NicheCreateSchema(
            niche_name="Test Niche - Integration", 
            category_id=4142,
            category_name="Engineering & Transportation > Engineering",
            filters={
                "current_AMAZON_gte": 10556,
                "current_AMAZON_lte": 22621,
                "current_SALES_gte": 5000,
                "current_SALES_lte": 300000,
                "categories_include": [4142],
                "min_margin_percent": 25.0,
                "max_sellers": 8,
                "min_price_stability": 0.6,
                "analysis_date": datetime.now().isoformat(),
                "keepa_api_used": True,
                "total_products_analyzed": 15
            },
            last_score=7.7,
            description="Test niche pour intégration Keepa"
        )
        
        print("✅ Schéma de création configuré")
        
        # Tentative de création
        print("🔍 Tentative de création de la niche...")
        result = bookmark_service.create_niche(user_id, niche_to_create)
        
        if result:
            print(f"✅ Sauvegarde réussie!")
            print(f"   ID: {result.id}")
            print(f"   Nom: {result.niche_name}")
            print(f"   User ID: {result.user_id}")
            return True
        else:
            print("❌ Résultat de création est None")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("🔧 DEBUG BOOKMARK SAVE")
    print("=" * 40)
    
    success = test_bookmark_save_mock()
    
    if success:
        print("\n✅ SAUVEGARDE FONCTIONNE!")
    else:
        print("\n❌ PROBLÈME AVEC SAUVEGARDE")


if __name__ == "__main__":
    main()