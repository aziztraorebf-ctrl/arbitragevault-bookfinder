"""
Keepa Data Adapter - Harmonise les données entre tests et production.
================================================================

Permet aux tests d'utiliser des données simplifiées tout en 
supportant les vraies données Keepa en production.
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class KeepaDataAdapter:
    """Adaptateur pour harmoniser structure test vs production."""
    
    @staticmethod
    def create_test_product(
        asin: str, 
        title: str = "Test Product", 
        is_amazon: bool = False,
        availability_amazon: int = -1,
        roi_percentage: float = 30.0
    ) -> Dict[str, Any]:
        """
        Crée un produit test avec structure hybride (test + Keepa).
        
        Args:
            asin: ASIN du produit
            title: Titre du produit
            is_amazon: Pour compatibilité tests (isAmazon)
            availability_amazon: Pour production Keepa (-1=non dispo, 0=en stock, >0=délai)
            roi_percentage: ROI pour tests
            
        Returns:
            Dict avec structure hybride test/Keepa
        """
        return {
            # Champs tests (compatibilité)
            'asin': asin,
            'title': title,
            'isAmazon': is_amazon,
            'roi_percentage': roi_percentage,
            
            # Champs Keepa production (vraie structure)
            'availabilityAmazon': availability_amazon if not is_amazon else 0,
            'csv': [[] for _ in range(30)],  # Structure CSV vide mais présente
            'buyBoxSellerIdHistory': [1] if is_amazon else [],  # Amazon = seller_id 1
            'domainId': 1,
            'hasReviews': False,
            'isAdultProduct': False,
            'lastUpdate': 1234567890,
        }
    
    @staticmethod
    def normalize_product_for_amazon_detection(product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalise un produit pour détection Amazon cohérente.
        
        Convertit les données test vers structure Keepa si nécessaire.
        """
        if not product:
            return product
            
        normalized = product.copy()
        
        # Si c'est des données test avec isAmazon, synchroniser avec availabilityAmazon
        if 'isAmazon' in normalized and 'availabilityAmazon' not in normalized:
            is_amazon = normalized['isAmazon']
            normalized['availabilityAmazon'] = 0 if is_amazon else -1
            logger.debug(f"Normalisé isAmazon={is_amazon} -> availabilityAmazon={normalized['availabilityAmazon']}")
            
        # Si pas de structure CSV, ajouter structure vide
        if 'csv' not in normalized:
            normalized['csv'] = [[] for _ in range(30)]
            
        # Si pas de buyBoxSellerIdHistory mais isAmazon=True, ajouter Amazon
        if 'buyBoxSellerIdHistory' not in normalized and normalized.get('isAmazon', False):
            normalized['buyBoxSellerIdHistory'] = [1]  # 1 = Amazon seller_id
            
        return normalized
    
    @staticmethod
    def create_keepa_realistic_data(
        asin: str,
        title: str = None,
        amazon_available: bool = False,
        amazon_recent_prices: bool = False
    ) -> Dict[str, Any]:
        """
        Crée des données réalistes au format Keepa pour tests avancés.
        
        Args:
            asin: ASIN du produit
            title: Titre (peut être None comme en vrai)
            amazon_available: Amazon disponible maintenant
            amazon_recent_prices: Amazon avait des prix récents
            
        Returns:
            Dict au format Keepa réaliste
        """
        # Structure de base Keepa
        product = {
            'asin': asin,
            'title': title,
            'availabilityAmazon': 0 if amazon_available else -1,
            'csv': [[] for _ in range(30)],
            'buyBoxSellerIdHistory': [],
            'domainId': 1,
            'hasReviews': bool(title),  # Si pas de titre, probablement pas de reviews
            'isAdultProduct': False,
            'isEligibleForSuperSaverShipping': False,
            'isEligibleForTradeIn': False,
            'isRedirectASIN': False,
            'isSNS': False,
            'lastUpdate': 1234567890,
            'trackingSince': 1234567890,
            'productType': 4,  # 4 = Books selon doc Keepa
            'rootCategory': 1000,  # 1000 = Books
        }
        
        # Ajouter historique prix Amazon si demandé
        if amazon_recent_prices:
            # csv[0] = prix Amazon
            product['csv'][0] = [
                1234567880, 1999,  # timestamp, prix en centimes
                1234567890, 2099,
                1234567900, 1899,
            ]
            
        # Ajouter Buy Box history si Amazon disponible
        if amazon_available:
            product['buyBoxSellerIdHistory'] = [1, 2, 1, 3, 1]  # Amazon (1) apparaît souvent
            
        return product


class TestDataFactory:
    """Factory pour créer des jeux de données test cohérents."""
    
    @staticmethod
    def create_mixed_product_set() -> List[Dict[str, Any]]:
        """Crée un set mixte pour tester filtrage Amazon."""
        adapter = KeepaDataAdapter()
        
        return [
            # Produit normal, pas Amazon
            adapter.create_test_product(
                asin='B001NORMAL1',
                title='Livre Normal 1',
                is_amazon=False,
                availability_amazon=-1,
                roi_percentage=45.0
            ),
            
            # Produit Amazon direct (disponible maintenant)
            adapter.create_test_product(
                asin='B002AMAZON1', 
                title='Livre Amazon Direct',
                is_amazon=True,
                availability_amazon=0,
                roi_percentage=60.0
            ),
            
            # Produit normal 2
            adapter.create_test_product(
                asin='B003NORMAL2',
                title='Livre Normal 2', 
                is_amazon=False,
                availability_amazon=-1,
                roi_percentage=35.0
            ),
            
            # Produit Amazon avec délai
            adapter.create_test_product(
                asin='B004AMAZON2',
                title='Livre Amazon Délai',
                is_amazon=True,
                availability_amazon=3,  # 3 jours délai
                roi_percentage=50.0
            ),
        ]
    
    @staticmethod 
    def create_keepa_realistic_set() -> List[Dict[str, Any]]:
        """Crée un set au format Keepa réaliste pour tests production."""
        adapter = KeepaDataAdapter()
        
        return [
            # Livre sans Amazon
            adapter.create_keepa_realistic_data(
                asin='B001REAL001',
                title='Chemistry Textbook',
                amazon_available=False,
                amazon_recent_prices=False
            ),
            
            # Livre avec Amazon disponible
            adapter.create_keepa_realistic_data(
                asin='B002REAL002', 
                title='Biology Handbook',
                amazon_available=True,
                amazon_recent_prices=True
            ),
            
            # Livre titre null (réaliste Keepa)
            adapter.create_keepa_realistic_data(
                asin='B003REAL003',
                title=None,
                amazon_available=False,
                amazon_recent_prices=True  # Avait Amazon avant
            ),
        ]