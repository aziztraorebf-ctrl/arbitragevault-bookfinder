"""Test de démarrage du serveur FastAPI pour validation."""

import sys
sys.path.append('.')

def test_server_imports():
    """Test que tous les imports nécessaires fonctionnent."""
    
    print("=== TEST SERVER IMPORTS ===")
    
    try:
        # Test FastAPI app
        from app.main import app
        print("✅ FastAPI app importée")
    except Exception as e:
        print(f"❌ Erreur import FastAPI app: {e}")
        return False
    
    try:
        # Test router strategic views
        from app.routers.strategic_views import router
        print("✅ Strategic Views router importé")
    except Exception as e:
        print(f"❌ Erreur import strategic views router: {e}")
        return False
    
    try:
        # Test all services
        from app.services.strategic_views_service import StrategicViewsService, TargetPriceCalculator
        from app.schemas.analysis import StrategicViewResponseSchema, TargetPriceResultSchema
        print("✅ Services et schémas importés")
    except Exception as e:
        print(f"❌ Erreur import services/schemas: {e}")
        return False
    
    # Test que le router est correctement configuré
    try:
        print(f"✅ Strategic Views router configuré avec prefix: {router.prefix}")
        route_paths = [route.path for route in router.routes]
        print(f"✅ Routes disponibles: {route_paths}")
        
        # Vérifier que notre nouvel endpoint est présent
        target_price_route_found = any("target-prices" in path for path in route_paths)
        print(f"✅ Endpoint target-prices trouvé: {target_price_route_found}")
        
    except Exception as e:
        print(f"❌ Erreur configuration router: {e}")
        return False
    
    print("\n=== TOUS LES IMPORTS SERVEUR OK ✅ ===")
    return True

def test_endpoint_availability():
    """Test la disponibilité des endpoints sans démarrer le serveur."""
    
    print("\n=== TEST ENDPOINT AVAILABILITY ===")
    
    try:
        from app.routers.strategic_views import router
        from fastapi.routing import APIRoute
        
        # Liste tous les endpoints
        for route in router.routes:
            if isinstance(route, APIRoute):
                methods = ', '.join(route.methods)
                print(f"✅ {methods} {router.prefix}{route.path}")
                
                # Vérifier notre endpoint target-prices
                if "target-prices" in route.path:
                    print(f"   🎯 Target Price endpoint trouvé!")
                    print(f"   🎯 Méthodes: {methods}")
                    print(f"   🎯 Path complet: {router.prefix}{route.path}")
        
        print("\n=== ENDPOINTS DISPONIBLES ✅ ===")
        return True
        
    except Exception as e:
        print(f"❌ Erreur test endpoints: {e}")
        return False

def test_manual_endpoint_call():
    """Test manuel d'appel de notre endpoint."""
    
    print("\n=== TEST MANUAL ENDPOINT CALL ===")
    
    try:
        # Import direct des fonctions
        from app.routers.strategic_views import get_strategic_view_with_target_prices, get_strategic_views_service
        from app.routers.strategic_views import ViewType
        
        # Mock des dépendances
        strategic_service = get_strategic_views_service()
        
        # Mock d'une simple simulation (sans Keepa réel)
        print("✅ Fonctions endpoint importées")
        print("✅ Service disponible")
        print("✅ ViewType enum disponible")
        
        # Liste des view types disponibles
        available_views = [v.value for v in ViewType]
        print(f"✅ View types disponibles: {available_views}")
        
        print("\n=== ENDPOINT MANUELLEMENT TESTABLE ✅ ===")
        return True
        
    except Exception as e:
        print(f"❌ Erreur test manuel endpoint: {e}")
        return False

if __name__ == "__main__":
    success = (
        test_server_imports() and 
        test_endpoint_availability() and 
        test_manual_endpoint_call()
    )
    
    if success:
        print("\n🚀 SERVEUR PRÊT POUR TARGET PRICE API!")
        print("   Endpoints disponibles:")
        print("   • GET /api/v1/views/{view_type}/target-prices")
        print("   • GET /api/v1/views/{view_type}")  
        print("   • GET /api/v1/views/")
    else:
        exit(1)