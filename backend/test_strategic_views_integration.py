"""Tests d'intégration pour StrategicViewsService avec Target Price."""

import sys
sys.path.append('.')

def test_strategic_views_integration():
    """Test intégration du StrategicViewsService avec Target Price."""
    
    print("=== STRATEGIC VIEWS SERVICE INTEGRATION TESTS ===")
    
    # Mock des données produits typiques
    mock_products_data = [
        {
            "id": "B00EXAMPLE1",
            "isbn_or_asin": "B00EXAMPLE1",
            "buy_price": 15.00,
            "current_price": 15.00,
            "fba_fee": 3.50,
            "buybox_price": 28.50,
            "referral_fee_rate": 0.15,
            "storage_fee": 0.50,
            "roi_percentage": 45.0,
            "velocity_score": 0.75,
            "profit_estimate": 8.50,
            "competition_level": "MEDIUM",
            "price_volatility": 0.2,
            "demand_consistency": 0.8,
            "data_confidence": 0.9
        },
        {
            "id": "B00EXAMPLE2", 
            "isbn_or_asin": "B00EXAMPLE2",
            "buy_price": 22.00,
            "current_price": 22.00,
            "fba_fee": 4.20,
            "buybox_price": 35.00,
            "referral_fee_rate": 0.10,  # Textbook rate
            "storage_fee": 1.00,
            "roi_percentage": 25.0,
            "velocity_score": 0.60,
            "profit_estimate": 6.80,
            "competition_level": "HIGH",
            "price_volatility": 0.35,
            "demand_consistency": 0.65,
            "data_confidence": 0.75
        },
        {
            "id": "B00EXAMPLE3",
            "isbn_or_asin": "B00EXAMPLE3", 
            "buy_price": 8.00,
            "current_price": 8.00,
            "fba_fee": 2.80,
            "buybox_price": 18.50,
            "referral_fee_rate": 0.15,
            "storage_fee": 0.30,
            "roi_percentage": 65.0,
            "velocity_score": 0.90,
            "profit_estimate": 6.20,
            "competition_level": "LOW",
            "price_volatility": 0.15,
            "demand_consistency": 0.92,
            "data_confidence": 0.95
        }
    ]
    
    # Import et init service (simulation)
    try:
        from app.services.strategic_views_service import StrategicViewsService, TargetPriceCalculator
        service = StrategicViewsService()
        print("✅ StrategicViewsService importé et initialisé avec succès")
    except Exception as e:
        print(f"❌ Erreur import StrategicViewsService: {e}")
        return False
    
    # TEST 1: calculate_target_price_for_view
    print("\n--- TEST 1: calculate_target_price_for_view ---")
    try:
        target_price_result = service.calculate_target_price_for_view(
            "profit_hunter", 
            mock_products_data[0]
        )
        
        if target_price_result:
            print(f"✅ Target price calculé: ${target_price_result.target_price}")
            print(f"   ROI Target: {target_price_result.roi_target * 100}%")
            print(f"   Achievable: {target_price_result.is_achievable}")
        else:
            print("❌ Pas de résultat target price")
            return False
    except Exception as e:
        print(f"❌ Erreur calculate_target_price_for_view: {e}")
        return False
    
    # TEST 2: enrich_analysis_with_target_price  
    print("\n--- TEST 2: enrich_analysis_with_target_price ---")
    try:
        enriched_data = service.enrich_analysis_with_target_price(
            "velocity",
            mock_products_data[1]
        )
        
        if "target_price_result" in enriched_data:
            print("✅ Données enrichies avec target_price_result")
            print(f"   Target Price: ${enriched_data['target_price']}")
            print(f"   ROI Target: {enriched_data['roi_target'] * 100}%")
        else:
            print("❌ target_price_result manquant dans données enrichies")
            return False
    except Exception as e:
        print(f"❌ Erreur enrich_analysis_with_target_price: {e}")
        return False
    
    # TEST 3: get_strategic_view_with_target_prices
    print("\n--- TEST 3: get_strategic_view_with_target_prices ---")
    try:
        strategic_view_result = service.get_strategic_view_with_target_prices(
            "profit_hunter",
            mock_products_data
        )
        
        if strategic_view_result:
            print("✅ Vue stratégique générée avec target prices")
            print(f"   View: {strategic_view_result['view_name']}")
            print(f"   Products Count: {strategic_view_result['products_count']}")
            print(f"   ROI Target: {strategic_view_result['roi_target'] * 100}%")
            
            # Vérifier que tous les produits ont target_price_result
            products_with_target_price = sum(
                1 for p in strategic_view_result['products'] 
                if 'target_price_result' in p
            )
            print(f"   Products with Target Price: {products_with_target_price}/{len(strategic_view_result['products'])}")
            
            if products_with_target_price != len(strategic_view_result['products']):
                print("❌ Pas tous les produits ont target_price_result")
                return False
        else:
            print("❌ Pas de résultat vue stratégique")
            return False
    except Exception as e:
        print(f"❌ Erreur get_strategic_view_with_target_prices: {e}")
        return False
    
    # TEST 4: Toutes les vues stratégiques
    print("\n--- TEST 4: Toutes les vues stratégiques ---")
    strategic_views = ["profit_hunter", "velocity", "cashflow_hunter", "balanced_score", "volume_player"]
    
    for view_name in strategic_views:
        try:
            result = service.get_strategic_view_with_target_prices(
                view_name,
                [mock_products_data[0]]  # Test avec 1 produit
            )
            
            roi_target = result['roi_target']
            expected_roi = TargetPriceCalculator.ROI_TARGETS[view_name]
            
            if abs(roi_target - expected_roi) < 0.01:
                print(f"✅ {view_name}: ROI {roi_target * 100}%")
            else:
                print(f"❌ {view_name}: ROI mismatch {roi_target} != {expected_roi}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur {view_name}: {e}")
            return False
    
    # TEST 5: Summary statistics
    print("\n--- TEST 5: Summary Statistics ---")
    try:
        result = service.get_strategic_view_with_target_prices(
            "balanced_score",
            mock_products_data
        )
        
        summary = result['summary']
        required_fields = [
            'total_products', 'achievable_opportunities', 'achievable_percentage',
            'avg_target_price', 'avg_strategic_score', 'total_potential_profit'
        ]
        
        missing_fields = [field for field in required_fields if field not in summary]
        
        if not missing_fields:
            print("✅ Tous les champs summary présents")
            print(f"   Total Products: {summary['total_products']}")
            print(f"   Achievable: {summary['achievable_opportunities']} ({summary['achievable_percentage']:.1f}%)")
            print(f"   Avg Target Price: ${summary['avg_target_price']}")
        else:
            print(f"❌ Champs summary manquants: {missing_fields}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur summary statistics: {e}")
        return False
    
    print("\n=== TOUS LES TESTS D'INTÉGRATION PASSÉS ✅ ===")
    return True

if __name__ == "__main__":
    success = test_strategic_views_integration()
    if not success:
        exit(1)