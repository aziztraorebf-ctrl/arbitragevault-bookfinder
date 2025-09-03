"""Test debug simple pour identifier le problème."""

import sys
import os
sys.path.append('C:\\Users\\azizt\\Workspace\\arbitragevault_bookfinder\\backend')

from app.schemas.bookmark import NicheCreateSchema
from app.services.bookmark_service import BookmarkService
from app.models.bookmark import SavedNiche
from sqlalchemy.orm import Session
from unittest.mock import Mock
from fastapi import HTTPException

def test_duplicate_name_debug():
    """Reproduire le test en échec pour diagnostiquer."""
    
    # Données de test
    user_id = "test-user-id"
    
    sample_niche_data = NicheCreateSchema(
        niche_name="Engineering Textbooks",
        category_id=13,
        category_name="Engineering & Transportation",
        filters={
            "min_price": 20.0,
            "max_price": 200.0,
            "max_bsr": 500000,
            "min_roi": 30.0
        },
        last_score=7.4,
        description="High-margin engineering textbooks"
    )

    # Existing niche mock
    existing_niche = SavedNiche(
        id="existing-niche-id",
        user_id=user_id,
        niche_name="Engineering Textbooks",
        category_id=13,
        category_name="Engineering & Transportation",
        filters={
            "min_price": 20.0,
            "max_price": 200.0,
            "max_bsr": 500000,
            "min_roi": 30.0
        },
        last_score=7.4,
        description="High-margin engineering textbooks"
    )
    
    # Mock database
    mock_db = Mock(spec=Session)
    
    # Configure le mock pour simuler qu'une niche existe déjà
    mock_query = Mock()
    mock_filter = Mock()
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = existing_niche  # Retourne la niche existante
    mock_db.query.return_value = mock_query
    
    # Test service
    service = BookmarkService(mock_db)
    
    print("=== TEST DEBUG: DUPLICATION DE NOM ===")
    
    try:
        # Cette opération devrait lever HTTPException avec status_code 409
        result = service.create_niche(user_id, sample_niche_data)
        print(f"❌ PROBLÈME: Création réussie alors qu'elle devrait échouer")
        print(f"   Résultat: {result}")
        return False
        
    except HTTPException as e:
        print(f"✅ HTTPException correctement levée")
        print(f"   Status Code: {e.status_code}")
        print(f"   Detail: {e.detail}")
        
        if e.status_code == 409 and "already exists" in str(e.detail):
            print(f"✅ Exception conforme aux attentes")
            return True
        else:
            print(f"❌ Exception inattendue")
            return False
            
    except Exception as e:
        print(f"❌ Exception non-HTTPException: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    try:
        success = test_duplicate_name_debug()
        if success:
            print("\n🎉 TEST DEBUG RÉUSSI - Le service fonctionne correctement")
        else:
            print("\n❌ PROBLÈME IDENTIFIÉ")
    except Exception as e:
        print(f"\n💥 ERREUR INATTENDUE: {e}")
        import traceback
        traceback.print_exc()