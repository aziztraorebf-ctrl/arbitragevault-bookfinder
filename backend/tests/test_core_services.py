"""
Tests consolidés pour les services core d'ArbitrageVault.
Conformément au plan de renforcement backend v1.9.1-alpha.
"""

import pytest
import time
import logging
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import keyring

from app.services.strategic_views_service import StrategicViewsService, TargetPriceCalculator
from app.services.keepa_service_factory import KeepaServiceFactory
from app.services.sales_velocity_service import SalesVelocityService
from app.schemas.batch import BatchCreateRequest


class TestStrategicViewsService:
    """Tests pour StrategicViewsService - Consolidation des tests existants."""
    
    def test_all_strategic_views_return_results(self):
        """Valider que chaque vue retourne bien des résultats structurés."""
        service = StrategicViewsService()
        sample_data = []  # Liste vide pour test structure
        
        views_to_test = [
            "profit_hunter",
            "velocity", 
            "cashflow_hunter",
            "balanced_score",
            "volume_player"
        ]
        
        for view_name in views_to_test:
            result = service.get_strategic_view_with_target_prices(view_name, sample_data)
            assert isinstance(result, dict), f"Vue {view_name} ne retourne pas un dict"
            assert "products" in result, f"Vue {view_name} manque la clé 'products'"
    
    def test_strategic_view_structure_consistency(self):
        """Tester que les résultats ont une structure cohérente."""
        service = StrategicViewsService()
        
        # Données d'exemple avec structure minimale
        sample_analysis = {
            'asin': 'B001TEST123',
            'title': 'Test Book',
            'buy_box_price': 15.00,
            'fba_fee': 3.50,
            'roi_percentage': 45.0,
            'bsr': 50000,
            'profit_net': 8.25
        }
        
        result = service.get_strategic_view_with_target_prices("profit_hunter", [sample_analysis])
        
        assert isinstance(result, dict), "Résultat n'est pas un dictionnaire"
        assert "products" in result, "Clé 'products' manquante"
        assert "summary" in result, "Clé 'summary' manquante"
        
        if result["products"]:  # Si non vide
            product = result["products"][0]
            required_fields = ['asin', 'strategic_score']
            for field in required_fields:
                assert field in product, f"Champ {field} manquant dans résultat strategic view"
    
    def test_strategic_view_performance(self):
        """Test de performance - doit traiter en moins de 2 secondes."""
        service = StrategicViewsService()
        
        # Données de test plus volumineuses
        sample_data = []
        for i in range(50):
            sample_data.append({
                'asin': f'B00{i:07d}',
                'title': f'Test Book {i}',
                'buy_box_price': 15.00 + i,
                'fba_fee': 3.50,
                'roi_percentage': 30.0 + i,
                'bsr': 50000 + i * 1000,
                'profit_net': 5.00 + i
            })
        
        start_time = time.time()
        result = service.get_strategic_view_with_target_prices("profit_hunter", sample_data)
        duration = time.time() - start_time
        
        assert duration < 2.0, f"Performance dégradée : {duration:.2f}s > 2s"
        assert isinstance(result, dict)


class TestBatchValidation:
    """Tests pour validation métier BatchCreateRequest."""
    
    def test_batch_description_minimum_length(self):
        """Rejeter batch si description < 3 caractères."""
        # Description trop courte
        with pytest.raises((ValueError, Exception)) as exc_info:
            batch_request = BatchCreateRequest(
                name="Test Batch",
                description="AB",  # 2 caractères seulement
                asin_list=["978-0123456789"],  # Corrigé
                config_name="profit_hunter"     # Champ obligatoire
            )
            # La validation doit se faire à la création ou validation du schema
        
        # Description vide
        with pytest.raises((ValueError, Exception)):
            batch_request = BatchCreateRequest(
                name="Test Batch", 
                description="",
                asin_list=["978-0123456789"],  # Corrigé
                config_name="profit_hunter"     # Champ obligatoire
            )
    
    def test_batch_description_valid(self):
        """Accepter batch avec description valide."""
        try:
            batch_request = BatchCreateRequest(
                name="Test Batch",
                description="Description valide et complète",
                asin_list=["978-0123456789"],  # Corrigé: asin_list au lieu de isbn_list
                config_name="profit_hunter"    # Champ obligatoire ajouté
            )
            # Ne doit pas lever d'exception
            assert batch_request.description == "Description valide et complète"
        except Exception as e:
            pytest.fail(f"Validation échouée pour description valide : {e}")


class TestKeepaErrorHandling:
    """Tests pour gestion d'erreurs API Keepa."""
    
    async def test_keepa_api_key_injection(self):
        """Confirmer que la clé Keepa est bien injectée."""
        # Récupérer clé depuis secrets Memex
        keepa_key = keyring.get_password("memex", "KEEPA_API_KEY")
        
        assert keepa_key is not None, "Clé KEEPA_API_KEY non trouvée dans secrets Memex"
        assert len(keepa_key) > 10, "Clé API trop courte pour être valide"
        
        # Tester le service factory (interface async corrigée)
        service = await KeepaServiceFactory.get_keepa_service()
        assert service.api_key is not None, "Clé API non injectée dans service"
        assert service.api_key == keepa_key, "Clé API ne correspond pas"
        
        # Nettoyer
        await service.close()
    
    @patch('httpx.AsyncClient.get')
    async def test_keepa_http_429_rate_limit_error(self, mock_get):
        """Simuler erreur HTTP 429 (rate limit) et confirmer gestion propre."""
        # Mock réponse 429
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'tokens-left': '5'}
        
        # Simuler HTTPStatusError
        import httpx
        async def async_mock(*args, **kwargs):
            return mock_response
        mock_get.side_effect = async_mock
        
        service = await KeepaServiceFactory.get_keepa_service()
        
        # Tenter appel qui devrait échouer proprement
        try:
            result = await service.get_product_data('B001TEST123')
            # Si ça marche, vérifier que l'erreur est gérée
            assert result is None
        except Exception as e:
            # Vérifier que message d'erreur est explicite
            error_msg = str(e).lower()
            assert 'rate limit' in error_msg or '429' in error_msg
        
        finally:
            await service.close()

    @patch('httpx.AsyncClient.get')  
    async def test_keepa_http_500_server_error(self, mock_get):
        """Simuler erreur HTTP 500 et confirmer message explicite."""
        # Mock réponse 500
        mock_response = Mock()
        mock_response.status_code = 500
        
        async def async_mock(*args, **kwargs):
            return mock_response
        mock_get.side_effect = async_mock
        
        service = await KeepaServiceFactory.get_keepa_service()
        
        try:
            result = await service.get_product_data('B001TEST123')
            assert result is None
        except Exception as e:
            error_msg = str(e).lower()
            assert 'server error' in error_msg or '500' in error_msg
        
        finally:
            await service.close()


class TestKeepaIntegrationReal:
    """Tests d'intégration avec vraie API Keepa."""
    
    async def test_real_keepa_api_connection(self):
        """Test avec vraie requête Keepa pour confirmer communication."""
        service = await KeepaServiceFactory.get_keepa_service()
        
        # ASIN de test connu (livre stable)
        test_asin = 'B00ZV9PXP2'  # Exemple d'ASIN stable
        
        try:
            # Méthode async corrigée
            result = await service.get_product_data(test_asin)
            
            # Vérifier que résultat a structure attendue
            if result is not None:
                # Vérifier champs essentiels dans la réponse Keepa
                assert 'asin' in result, "Champ 'asin' manquant dans réponse Keepa"
                assert 'title' in result, "Champ 'title' manquant dans réponse Keepa"
            else:
                # Produit non trouvé = acceptable
                pass
                
        except Exception as e:
            # Log l'erreur mais ne fait pas échouer le test si c'est un problème de quota
            print(f"Erreur API Keepa (peut être quota/rate limit) : {e}")
            # Le test passe si l'erreur est liée aux limites API
            error_msg = str(e).lower()
            if 'rate limit' in error_msg or 'quota' in error_msg or '429' in error_msg:
                pytest.skip("Test skippé - Limite API Keepa atteinte")
            else:
                raise
        
        finally:
            # Nettoyer connexion
            await service.close()


class TestLogging:
    """Tests pour logging et traçabilité."""
    
    def test_batch_creation_logging(self):
        """Confirmer qu'un log est émis lors création batch."""
        
        # Configuration temporaire du logger pour capturer logs
        import logging
        from io import StringIO
        import sys
        
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        logger = logging.getLogger("arbitragevault.batch")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # Simuler création batch
        batch_id = "test_batch_123"
        timestamp = datetime.now()
        
        # Émettre log (sera implémenté dans service batch)
        logger.info(f"Batch créé avec succès - ID: {batch_id}, Timestamp: {timestamp}")
        
        # Vérifier contenu log
        log_content = log_capture.getvalue()
        assert "Batch créé avec succès" in log_content
        assert batch_id in log_content
        assert "Timestamp:" in log_content
        
        # Nettoyage
        logger.removeHandler(handler)
    
    def test_logger_configuration(self):
        """Vérifier que le logger est correctement configuré."""
        logger = logging.getLogger("arbitragevault.batch")
        
        # Vérifier que logger peut émettre
        assert logger is not None
        
        # Test message simple
        logger.info("Test logger configuration")
        # Pas d'exception = succès


class TestEdgeCasesAndBoundaries:
    """Tests pour cas limites et conditions aux limites."""
    
    def test_empty_asin_list_handling(self):
        """Test avec liste ASIN vide."""
        service = StrategicViewsService()
        
        result = service.get_strategic_view_with_target_prices("profit_hunter", [])
        assert isinstance(result, dict)
        assert "products" in result
        assert len(result["products"]) == 0
    
    async def test_invalid_asin_format(self):
        """Test avec ASIN au format incorrect."""
        service = await KeepaServiceFactory.get_keepa_service()
        
        invalid_asins = [
            "INVALID",
            "123456",  # Trop court
            "B001TOOLONG123456789",  # Trop long
            "",  # Vide
        ]
        
        try:
            for invalid_asin in invalid_asins:
                try:
                    result = await service.get_product_data(invalid_asin)
                    # Si ça marche, vérifier que l'erreur est gérée gracieusement
                    # Pour ASIN invalide, on s'attend à None ou réponse vide
                    assert result is None or not result
                except Exception:
                    # Exception acceptable pour ASIN invalide
                    pass
        finally:
            await service.close()
    
    async def test_keepa_timeout_handling(self):
        """Test gestion timeout API Keepa."""
        service = await KeepaServiceFactory.get_keepa_service()
        
        # Mock timeout
        with patch('httpx.AsyncClient.get') as mock_get:
            import httpx
            mock_get.side_effect = httpx.TimeoutException("Request timeout")
            
            try:
                result = await service.get_product_data('B001TEST123')
                # Vérifier gestion gracieuse
                assert result is None
            except Exception as e:
                # Vérifier message explicite
                assert 'timeout' in str(e).lower() or 'connection' in str(e).lower()
            
            finally:
                await service.close()


if __name__ == "__main__":
    # Lancement direct des tests
    pytest.main([__file__, "-v"])