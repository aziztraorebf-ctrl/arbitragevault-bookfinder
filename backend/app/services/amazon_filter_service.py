"""
Amazon Filter Service - Simple et efficace
Élimine les produits où Amazon est vendeur direct (isAmazon = true)
"""

from typing import Dict, List, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AmazonFilterService:
    """Service pour filtrer les produits Amazon avec métriques complètes."""
    
    def __init__(self):
        """Initialiser le service avec configuration par défaut."""
        self.enabled = True  # Peut être désactivé par config admin
        
    def filter_amazon_products(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Filtre les produits Amazon avec transparence totale.
        
        Args:
            products: Liste des produits à filtrer
            
        Returns:
            Dict avec produits filtrés + métriques détaillées
        """
        if not self.enabled:
            logger.info("Amazon Filter désactivé - aucun filtrage appliqué")
            return {
                'products': products,
                'total_input': len(products),
                'amazon_filtered': 0,
                'final_count': len(products),
                'filter_impact': "Filtrage désactivé",
                'filter_enabled': False
            }
        
        # Logique de filtrage simple et claire
        filtered_products = []
        amazon_count = 0
        amazon_products_details = []
        
        for product in products:
            if self._is_amazon_seller(product):
                amazon_count += 1
                # Garder trace des produits éliminés pour transparence
                amazon_products_details.append({
                    'asin': product.get('asin', 'Unknown'),
                    'title': product.get('title', 'Unknown Title')[:50] + '...' if len(product.get('title', '')) > 50 else product.get('title', 'Unknown Title'),
                    'reason': 'Amazon vendeur direct'
                })
                continue  # Éliminer ce produit
                
            filtered_products.append(product)
        
        # Métriques complètes pour business intelligence
        filter_rate = (amazon_count / len(products) * 100) if products else 0
        
        result = {
            'products': filtered_products,
            'total_input': len(products),
            'amazon_filtered': amazon_count,
            'final_count': len(filtered_products),
            'filter_rate_percentage': round(filter_rate, 1),
            'filter_impact': f"{amazon_count} produit{'s' if amazon_count != 1 else ''} Amazon éliminé{'s' if amazon_count != 1 else ''}",
            'filter_enabled': True,
            'filtered_at': datetime.now().isoformat(),
            'amazon_products_eliminated': amazon_products_details[:10]  # Max 10 pour éviter surcharge
        }
        
        # Logging pour analytics
        logger.info(f"Amazon Filter appliqué: {amazon_count}/{len(products)} produits éliminés ({filter_rate:.1f}%)")
        
        # Alerte si taux de filtrage très élevé (peut indiquer un problème)
        if filter_rate > 70:
            logger.warning(f"Taux de filtrage Amazon élevé: {filter_rate:.1f}% - Vérifier la qualité des données")
        
        return result
    
    def _is_amazon_seller(self, product: Dict[str, Any]) -> bool:
        """
        Détermine si Amazon est le vendeur principal.
        
        Logique simple : vérifie le flag isAmazon dans les données Keepa.
        
        Args:
            product: Dictionnaire produit avec données Keepa
            
        Returns:
            True si Amazon est vendeur, False sinon
        """
        # Vérification principale : flag isAmazon de Keepa
        is_amazon = product.get('isAmazon', False)
        
        # Log pour debugging si nécessaire
        if is_amazon:
            asin = product.get('asin', 'Unknown')
            title = product.get('title', 'Unknown')[:30]
            logger.debug(f"Produit Amazon détecté: {asin} - {title}")
        
        return is_amazon
    
    def get_filter_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques du service pour monitoring.
        
        Returns:
            Dict avec état et configuration du filtre
        """
        return {
            'service_name': 'AmazonFilterService',
            'version': '1.0.0',
            'enabled': self.enabled,
            'filter_criteria': 'isAmazon flag from Keepa API',
            'description': 'Élimine les produits où Amazon est vendeur direct'
        }
    
    def set_enabled(self, enabled: bool) -> None:
        """
        Active/désactive le filtre (pour configuration admin).
        
        Args:
            enabled: True pour activer, False pour désactiver
        """
        self.enabled = enabled
        status = "activé" if enabled else "désactivé"
        logger.info(f"Amazon Filter {status}")


# Fonction utilitaire pour usage direct
def filter_amazon_products_simple(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Fonction utilitaire pour filtrage simple sans métriques.
    
    Args:
        products: Liste des produits
        
    Returns:
        Liste des produits non-Amazon
    """
    service = AmazonFilterService()
    result = service.filter_amazon_products(products)
    return result['products']