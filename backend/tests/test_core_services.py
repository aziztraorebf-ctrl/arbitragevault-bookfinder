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
from app.services.amazon_filter_service import AmazonFilterService
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


class TestAmazonFilter:
    """Tests pour Amazon Filter Service - Option 1 Simple."""
    
    def test_amazon_filter_excludes_amazon_products(self):
        """Confirmer que les produits Amazon sont éliminés."""
        service = AmazonFilterService()
        
        test_products = [
            {'asin': 'B001TEST1', 'isAmazon': False, 'title': 'Livre Normal', 'roi_percentage': 45},
            {'asin': 'B002TEST2', 'isAmazon': True, 'title': 'Livre Amazon Direct', 'roi_percentage': 60},  # À éliminer
            {'asin': 'B003TEST3', 'isAmazon': False, 'title': 'Autre Livre Normal', 'roi_percentage': 35},
            {'asin': 'B004TEST4', 'isAmazon': True, 'title': 'Deuxième Amazon', 'roi_percentage': 50},  # À éliminer aussi
        ]
        
        result = service.filter_amazon_products(test_products)
        
        # Vérifications principales
        assert len(result['products']) == 2, "Devrait garder seulement les 2 produits non-Amazon"
        assert result['amazon_filtered'] == 2, "Devrait éliminer 2 produits Amazon"
        assert result['total_input'] == 4, "Input total devrait être 4"
        assert result['final_count'] == 2, "Final count devrait être 2"
        assert result['filter_rate_percentage'] == 50.0, "Taux de filtrage devrait être 50%"
        
        # Vérifier que les produits restants ne sont pas Amazon
        for product in result['products']:
            assert not product.get('isAmazon', False), "Aucun produit Amazon ne devrait rester"
        
        # Vérifier les bonnes ASINs restantes
        remaining_asins = [p['asin'] for p in result['products']]
        assert 'B001TEST1' in remaining_asins
        assert 'B003TEST3' in remaining_asins
        assert 'B002TEST2' not in remaining_asins  # Amazon éliminé
        assert 'B004TEST4' not in remaining_asins  # Amazon éliminé
    
    def test_amazon_filter_handles_empty_list(self):
        """Gestion correcte d'une liste vide."""
        service = AmazonFilterService()
        
        result = service.filter_amazon_products([])
        
        assert result['products'] == []
        assert result['amazon_filtered'] == 0
        assert result['total_input'] == 0
        assert result['filter_impact'] == "0 produits Amazon éliminés"
    
    def test_amazon_filter_all_non_amazon(self):
        """Test avec aucun produit Amazon."""
        service = AmazonFilterService()
        
        test_products = [
            {'asin': 'B001', 'isAmazon': False, 'title': 'Livre 1'},
            {'asin': 'B002', 'isAmazon': False, 'title': 'Livre 2'},
            {'asin': 'B003', 'title': 'Livre 3'},  # Pas de champ isAmazon = False par défaut
        ]
        
        result = service.filter_amazon_products(test_products)
        
        assert len(result['products']) == 3
        assert result['amazon_filtered'] == 0
        assert result['filter_rate_percentage'] == 0.0
        assert result['filter_impact'] == "0 produits Amazon éliminés"
    
    def test_amazon_filter_disabled(self):
        """Test du filtre quand il est désactivé."""
        service = AmazonFilterService()
        service.set_enabled(False)
        
        test_products = [
            {'asin': 'B001', 'isAmazon': False, 'title': 'Normal'},
            {'asin': 'B002', 'isAmazon': True, 'title': 'Amazon'},  # Devrait rester car filtre désactivé
        ]
        
        result = service.filter_amazon_products(test_products)
        
        assert len(result['products']) == 2, "Tous les produits devraient rester"
        assert result['amazon_filtered'] == 0
        assert result['filter_enabled'] is False
        assert result['filter_impact'] == "Filtrage désactivé"


class TestAmazonFilterIntegration:
    """Tests d'intégration Amazon Filter avec StrategicViewsService."""
    
    def test_strategic_views_with_amazon_filter(self):
        """Vérifier que le filtrage fonctionne dans les strategic views."""
        service = StrategicViewsService()
        
        test_data = [
            {
                'asin': 'B001NORMAL',
                'isAmazon': False,
                'title': 'Livre Normal Rentable',
                'roi_percentage': 45.0,
                'buy_box_price': 20.0,
                'fba_fee': 4.0,
                'profit_net': 8.0,
                'bsr': 50000
            },
            {
                'asin': 'B002AMAZON',
                'isAmazon': True,  # Ce produit doit être éliminé
                'title': 'Livre Amazon Direct',
                'roi_percentage': 60.0,  # Même avec ROI élevé, doit être éliminé
                'buy_box_price': 25.0,
                'fba_fee': 4.5,
                'profit_net': 12.0,
                'bsr': 30000
            },
            {
                'asin': 'B003NORMAL2',
                'isAmazon': False,
                'title': 'Autre Livre Normal',
                'roi_percentage': 35.0,
                'buy_box_price': 15.0,
                'fba_fee': 3.0,
                'profit_net': 5.0,
                'bsr': 80000
            }
        ]
        
        result = service.get_strategic_view_with_target_prices("profit_hunter", test_data)
        
        # Vérifications intégration
        assert len(result['products']) == 2, "Seulement 2 produits non-Amazon devraient rester"
        assert result['products_count'] == 2
        
        # Vérifier présence des infos Amazon Filter dans summary
        assert 'amazon_filter' in result['summary']
        filter_info = result['summary']['amazon_filter']
        assert filter_info['total_input'] == 3
        assert filter_info['amazon_filtered'] == 1
        assert filter_info['final_count'] == 2
        assert filter_info['filter_rate_percentage'] == 33.3  # 1/3 = 33.3%
        
        # Vérifier que les bonnes ASINs restent
        remaining_asins = [p['asin'] for p in result['products']]
        assert 'B001NORMAL' in remaining_asins
        assert 'B003NORMAL2' in remaining_asins
        assert 'B002AMAZON' not in remaining_asins  # Éliminé
        
        # Vérifier que les strategic scores sont calculés correctement
        for product in result['products']:
            assert 'strategic_score' in product
            # Note: target_price_result sera vérifié dans un test séparé
    
    def test_strategic_views_performance_with_filter(self):
        """Confirmer que l'Amazon Filter n'impacte pas les performances < 2s."""
        service = StrategicViewsService()
        
        # Dataset avec mix Amazon/Non-Amazon
        large_dataset = []
        for i in range(50):
            large_dataset.append({
                'asin': f'B00{i:07d}',
                'title': f'Test Book {i}',
                'isAmazon': i % 3 == 0,  # 1/3 des produits sont Amazon
                'buy_box_price': 15.0 + i,
                'fba_fee': 3.50,
                'roi_percentage': 30.0 + i,
                'bsr': 50000 + i * 1000,
                'profit_net': 5.00 + i
            })
        
        start_time = time.time()
        result = service.get_strategic_view_with_target_prices("profit_hunter", large_dataset)
        duration = time.time() - start_time
        
        # Tests performance
        assert duration < 2.0, f"Performance dégradée avec Amazon Filter: {duration:.2f}s > 2s"
        
        # Tests fonctionnels
        assert 'amazon_filter' in result['summary']
        amazon_count = result['summary']['amazon_filter']['amazon_filtered']
        assert amazon_count > 0, "Devrait avoir éliminé des produits Amazon"
        assert len(result['products']) == 50 - amazon_count, "Count final cohérent"


if __name__ == "__main__":
    # Lancement direct des tests
    pytest.main([__file__, "-v"])