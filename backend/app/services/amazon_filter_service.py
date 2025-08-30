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
    
    def __init__(self, detection_level: str = "smart"):
        """
        Initialiser le service avec configuration par défaut.
        
        Args:
            detection_level: "safe" (direct seulement) ou "smart" (Amazon présent)
        """
        self.enabled = True  # Peut être désactivé par config admin
        self.detection_level = detection_level  # "safe" ou "smart"
        
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
            is_amazon, reason = self._detect_amazon_presence(product)
            if is_amazon:
                amazon_count += 1
                # Garder trace des produits éliminés pour transparence
                amazon_products_details.append({
                    'asin': product.get('asin', 'Unknown'),
                    'title': product.get('title', 'Unknown Title')[:50] + '...' if len(product.get('title', '')) > 50 else product.get('title', 'Unknown Title'),
                    'reason': reason
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
    
    def _detect_amazon_presence(self, product: Dict[str, Any]) -> tuple[bool, str]:
        """
        Détecte si Amazon est présent sur ce listing (approche KISS).
        
        Args:
            product: Dictionnaire produit avec données Keepa
            
        Returns:
            Tuple (is_amazon_present, reason)
        """
        asin = product.get('asin', 'Unknown')
        
        if self.detection_level == "safe":
            # NIVEAU SAFE : Amazon vendeur direct seulement
            is_amazon_direct = product.get('isAmazon', False)
            if is_amazon_direct:
                logger.debug(f"Amazon Direct détecté: {asin}")
                return True, "Amazon vendeur direct"
            return False, "Amazon non détecté (niveau safe)"
        
        elif self.detection_level == "smart":
            # NIVEAU SMART : Amazon présent sur listing (recommandé KISS)
            
            # 1. Amazon vendeur direct
            if product.get('isAmazon', False):
                logger.debug(f"Amazon Direct détecté: {asin}")
                return True, "Amazon vendeur direct"
            
            # 2. Amazon dans les offres récentes (données Keepa)
            recent_offers = product.get('offerCSV', [])
            if recent_offers:
                # Prendre les 5 dernières offres pour éviter données obsolètes
                last_5_offers = recent_offers[-5:] if len(recent_offers) >= 5 else recent_offers
                
                for offer in last_5_offers:
                    if len(offer) > 2 and offer[2] == 1:  # seller_id = 1 = Amazon
                        logger.debug(f"Amazon vendeur actif détecté: {asin}")
                        return True, "Amazon vendeur actif"
            
            # 3. Amazon dans Buy Box history récente
            buy_box_history = product.get('buyBoxSellerIdHistory', [])
            if buy_box_history:
                # Prendre les 10 dernières entrées Buy Box
                recent_buy_box = buy_box_history[-10:] if len(buy_box_history) >= 10 else buy_box_history
                
                if 1 in recent_buy_box:  # Amazon seller_id = 1
                    logger.debug(f"Amazon en Buy Box récemment: {asin}")
                    return True, "Amazon en Buy Box récemment"
            
            # Pas d'Amazon détecté
            return False, "Amazon non détecté sur ce listing"
        
        else:
            # Fallback sur niveau safe si configuration inconnue
            logger.warning(f"Detection level inconnu: {self.detection_level}, fallback sur 'safe'")
            return self._detect_amazon_presence_safe(product)
    
    def _detect_amazon_presence_safe(self, product: Dict[str, Any]) -> tuple[bool, str]:
        """Méthode fallback pour niveau safe."""
        is_amazon_direct = product.get('isAmazon', False)
        if is_amazon_direct:
            return True, "Amazon vendeur direct"
        return False, "Amazon non détecté (niveau safe)"
    
    def get_filter_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques du service pour monitoring.
        
        Returns:
            Dict avec état et configuration du filtre
        """
        detection_descriptions = {
            'safe': 'Élimine les produits Amazon Direct seulement',
            'smart': 'Élimine TOUS produits avec Amazon vendeur (recommandé)'
        }
        
        return {
            'service_name': 'AmazonFilterService',
            'version': '2.0.0-KISS',
            'enabled': self.enabled,
            'detection_level': self.detection_level,
            'filter_criteria': f'{self.detection_level} level detection',
            'description': detection_descriptions.get(self.detection_level, 'Configuration inconnue')
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
    
    def set_detection_level(self, level: str) -> None:
        """
        Configure le niveau de détection Amazon.
        
        Args:
            level: "safe" (Amazon Direct seulement) ou "smart" (Amazon présent)
        """
        if level not in ["safe", "smart"]:
            raise ValueError(f"Niveau détection invalide: {level}. Utiliser 'safe' ou 'smart'")
        
        old_level = self.detection_level
        self.detection_level = level
        logger.info(f"Amazon Filter niveau changé: {old_level} → {level}")
    
    def get_detection_level(self) -> str:
        """Retourne le niveau de détection actuel."""
        return self.detection_level


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