"""
Category Analyzer Service - Analyse des catégories Keepa
========================================================

Service pour analyser les catégories Keepa et extraire les métriques
nécessaires à la découverte de niches.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from statistics import mean, median

from app.models.niche import NicheMetrics, NicheAnalysisCriteria, CategoryOverview
from app.services.keepa_service import KeepaService

logger = logging.getLogger(__name__)


class CategoryAnalyzer:
    """Analyseur de catégories pour la découverte de niches."""
    
    def __init__(self, keepa_service: KeepaService):
        self.keepa_service = keepa_service
        
        # Catégories prédéfinies pour analyse (Phase 1 KISS)
        self.target_categories = {
            # Medical & Health
            3738: "Health, Fitness & Dieting > Medical Books",
            3854: "Health, Fitness & Dieting > Nutrition",
            3783: "Health, Fitness & Dieting > Psychology & Counseling",
            
            # Professional & Technical
            4142: "Engineering & Transportation > Engineering",
            4108: "Engineering & Transportation > Automotive",
            3546: "Computers & Technology > Programming",
            3570: "Computers & Technology > Databases & Big Data",
            
            # Education & Certification
            4254: "Education & Teaching > Higher & Continuing Education",
            4277: "Education & Teaching > Test Preparation",
            
            # Business & Finance
            2578: "Business & Money > Accounting",
            2602: "Business & Money > Economics",
            2654: "Business & Money > Real Estate",
            
            # Science & Research
            69838: "Science & Math > Chemistry",
            69847: "Science & Math > Physics",
            69892: "Science & Math > Mathematics",
            
            # Legal & Law
            2649: "Business & Money > Law",
            
            # Specialized Hobbies
            4736: "Crafts, Hobbies & Home > Crafts & Hobbies",
            4808: "Sports & Outdoors > Individual Sports"
        }
    
    async def analyze_category(
        self, 
        category_id: int, 
        criteria: NicheAnalysisCriteria
    ) -> Optional[NicheMetrics]:
        """
        Analyse une catégorie spécifique et calcule ses métriques.
        
        Args:
            category_id: ID de la catégorie Keepa
            criteria: Critères d'analyse
            
        Returns:
            NicheMetrics ou None si analyse échoue
        """
        try:
            logger.info(f"Analyse catégorie {category_id} - {self.target_categories.get(category_id, 'Unknown')}")
            
            # Récupérer échantillon de produits de cette catégorie
            products = await self._get_category_sample(category_id, criteria.sample_size)
            
            if not products or len(products) < 5:  # Minimum 5 produits pour analyse
                logger.warning(f"Échantillon insuffisant pour catégorie {category_id}: {len(products) if products else 0} produits")
                return None
            
            # Calculer métriques
            metrics = await self._calculate_category_metrics(products, criteria)
            
            logger.info(f"Catégorie {category_id} analysée: {metrics.total_products} produits, score potentiel basé sur {metrics.viable_products} viables")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Erreur analyse catégorie {category_id}: {e}")
            return None
    
    async def _get_category_sample(self, category_id: int, sample_size: int) -> List[Dict]:
        """
        Récupère un échantillon de produits d'une catégorie.
        
        Note: Phase 1 KISS utilise des produits pré-sélectionnés.
        Phase 2+ utilisera le Keepa Product Finder API.
        """
        try:
            # PHASE 1 KISS: Simuler échantillon avec des ASINs prédéfinis par catégorie
            # En production Phase 2+, utiliser: await self.keepa_service.find_products({category: category_id})
            
            sample_products = []
            
            # Utiliser un échantillon d'ASINs représentatifs par catégorie
            sample_asins = self._get_sample_asins_for_category(category_id)
            
            for asin in sample_asins[:sample_size]:
                try:
                    product_data = await self.keepa_service.get_product_data(asin)
                    if product_data:
                        sample_products.append(product_data)
                        
                    # Rate limiting - pause entre requêtes
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"Échec récupération produit {asin}: {e}")
                    continue
            
            logger.info(f"Échantillon catégorie {category_id}: {len(sample_products)} produits récupérés")
            return sample_products
            
        except Exception as e:
            logger.error(f"Erreur récupération échantillon catégorie {category_id}: {e}")
            return []
    
    def _get_sample_asins_for_category(self, category_id: int) -> List[str]:
        """
        Retourne des ASINs d'échantillon pour une catégorie (Phase 1 KISS).
        
        En Phase 2+, ceci sera remplacé par l'API Keepa Product Finder.
        """
        # ASINs d'échantillon par catégorie (livres représentatifs)
        category_samples = {
            # Medical Books
            3738: [
                "1496300149", "1451193408", "1608311481", "1496347889", "1451113404",
                "1608311945", "1496386299", "149634825X", "1608311473", "1451193394"
            ],
            # Nutrition
            3854: [
                "1260013316", "1284198936", "1264260776", "1264286635", "1260013308",
                "1284198944", "1264286643", "1264260784", "1284212033", "1260013324"
            ],
            # Engineering
            4142: [
                "0134484207", "0134318412", "0134496388", "0134496351", "0134318420",
                "0134484215", "013449637X", "0134496362", "0134318439", "0134496346"
            ],
            # Programming
            3546: [
                "0135957052", "0135166306", "0135166314", "0135957060", "0135166322",
                "0135957079", "0135166330", "0135957087", "0135166349", "0135166357"
            ],
            # Business Accounting
            2578: [
                "1260247821", "1260247813", "1260247805", "1260247796", "1260247788",
                "1260247770", "1260247762", "1260247754", "1260247746", "1260247738"
            ]
        }
        
        # Retourner échantillon pour la catégorie, ou échantillon générique
        return category_samples.get(category_id, [
            "1250301696", "0316769487", "1984818644", "0525559477", "0593229231",
            "1668001225", "0063257084", "1368041108", "0593230574", "0593299019"
        ])
    
    async def _calculate_category_metrics(
        self, 
        products: List[Dict], 
        criteria: NicheAnalysisCriteria
    ) -> NicheMetrics:
        """Calcule les métriques d'une catégorie à partir de l'échantillon."""
        
        # Listes pour calculs statistiques
        seller_counts = []
        bsr_values = []
        prices = []
        price_stabilities = []
        profit_margins = []
        viable_count = 0
        
        for product in products:
            try:
                # Nombre de vendeurs (approximé via disponibilité)
                sellers = self._estimate_seller_count(product)
                seller_counts.append(sellers)
                
                # BSR moyen
                bsr = self._extract_bsr(product)
                if bsr and bsr > 0:
                    bsr_values.append(bsr)
                
                # Prix actuel
                price = self._extract_current_price(product)
                if price and price > 0:
                    prices.append(price)
                
                # Stabilité prix (via historique CSV)
                stability = self._calculate_price_stability(product)
                if stability is not None:
                    price_stabilities.append(stability)
                
                # Marge profit estimée
                margin = self._estimate_profit_margin(product, criteria)
                if margin is not None:
                    profit_margins.append(margin)
                
                # Produit viable selon critères ?
                if self._is_product_viable(product, criteria):
                    viable_count += 1
                    
            except Exception as e:
                logger.warning(f"Erreur analyse produit {product.get('asin', 'Unknown')}: {e}")
                continue
        
        # Calculs statistiques finaux
        return NicheMetrics(
            avg_sellers=mean(seller_counts) if seller_counts else 0.0,
            avg_bsr=mean(bsr_values) if bsr_values else 0.0,
            avg_price=mean(prices) if prices else 0.0,
            price_stability=mean(price_stabilities) if price_stabilities else 0.0,
            profit_margin=mean(profit_margins) if profit_margins else 0.0,
            total_products=len(products),
            viable_products=viable_count,
            competition_level=""  # Sera calculé par le scoring service
        )
    
    def _estimate_seller_count(self, product: Dict) -> float:
        """Estime le nombre de vendeurs basé sur les données Keepa."""
        # Méthode KISS: utiliser availabilityAmazon et offres actuelles
        # En production, utiliser les données d'offres live si disponibles
        
        base_sellers = 1.0  # Au moins un vendeur si le produit existe
        
        # Amazon = +1 vendeur
        if product.get('availabilityAmazon', -1) >= 0:
            base_sellers += 1.0
        
        # Estimer vendeurs additionnels via historique prix
        csv_data = product.get('csv', [])
        if csv_data and len(csv_data) > 1:
            # csv[1] = Prix NEW (non-Amazon), csv[2] = Prix USED
            new_prices = csv_data[1] if len(csv_data) > 1 else []
            used_prices = csv_data[2] if len(csv_data) > 2 else []
            
            # Si prix NEW récents, +1-3 vendeurs estimés
            if new_prices and len(new_prices) > 0:
                recent_new = [x for x in new_prices[-10:] if x and x > 0]
                if recent_new:
                    base_sellers += min(2.0, len(recent_new) / 5)
            
            # Si prix USED récents, +0.5 vendeur estimé
            if used_prices and len(used_prices) > 0:
                recent_used = [x for x in used_prices[-10:] if x and x > 0]
                if recent_used:
                    base_sellers += 0.5
        
        return min(base_sellers, 10.0)  # Cap à 10 vendeurs max
    
    def _extract_bsr(self, product: Dict) -> Optional[int]:
        """Extrait le BSR principal du produit en utilisant la structure officielle."""
        # Méthode 1: Utiliser le champ 'SALES' du CSV (le plus fiable)
        csv_data = product.get('csv', [])
        if csv_data and len(csv_data) > 3:
            sales_history = csv_data[3]
            if sales_history and len(sales_history) >= 2:
                # Itérer à l'envers pour trouver le dernier BSR valide
                for i in range(len(sales_history) - 1, 0, -2):
                    bsr = sales_history[i]
                    if bsr is not None and bsr > 0:
                        return bsr

        # Méthode 2: Fallback sur salesRanks et salesRankReference
        main_bsr_category = product.get('salesRankReference')
        sales_ranks = product.get('salesRanks', {})

        if main_bsr_category and main_bsr_category != -1 and sales_ranks and str(main_bsr_category) in sales_ranks:
            bsr_history = sales_ranks[str(main_bsr_category)]
            if bsr_history and len(bsr_history) >= 2:
                return bsr_history[-1]

        if sales_ranks:
            for category_id, bsr_history in sales_ranks.items():
                if bsr_history and len(bsr_history) >= 2:
                    return bsr_history[-1]
        
        return None
    
    def _extract_current_price(self, product: Dict) -> Optional[float]:
        """Extrait le prix actuel du produit en dollars."""
        csv_data = product.get('csv', [])
        if not csv_data or len(csv_data) == 0:
            return None

        # csv[0] = Prix Amazon, format [time, price, time, price, ...]
        amazon_prices_history = csv_data[0]
        if not amazon_prices_history or len(amazon_prices_history) < 2:
            return None

        # Itérer à l'envers pour trouver le dernier prix valide
        for i in range(len(amazon_prices_history) - 1, 0, -2):
            price_in_cents = amazon_prices_history[i]
            if price_in_cents is not None and price_in_cents > 0:
                return price_in_cents / 100.0  # Conversion centimes -> dollars
        
        return None
    
    def _calculate_price_stability(self, product: Dict) -> Optional[float]:
        """Calcule la stabilité prix (0-1) basée sur l'historique CSV."""
        csv_data = product.get('csv', [])
        if not csv_data or len(csv_data) == 0:
            return None
        
        amazon_prices_history = csv_data[0]
        if not amazon_prices_history or len(amazon_prices_history) < 10: # Au moins 5 points de données
            return None
        
        # Extraire les 20 derniers prix valides
        valid_prices = []
        for i in range(len(amazon_prices_history) - 1, 0, -2):
            price = amazon_prices_history[i]
            if price is not None and price > 0:
                valid_prices.append(price / 100.0) # Convertir en dollars
            if len(valid_prices) >= 20:
                break
        
        if len(valid_prices) < 5:
            return None
        
        # Calculer coefficient de variation (inversé pour stabilité)
        try:
            avg_price = mean(valid_prices)
            if avg_price == 0: return 0.0

            price_std = (sum((p - avg_price) ** 2 for p in valid_prices) / len(valid_prices)) ** 0.5
            coefficient_variation = price_std / avg_price
            
            # Stabilité = 1 - coefficient_variation (borné entre 0 et 1)
            stability = max(0.0, min(1.0, 1.0 - coefficient_variation))
            return stability
            
        except (ZeroDivisionError, ValueError):
            return None
    
    def _estimate_profit_margin(self, product: Dict, criteria: NicheAnalysisCriteria) -> Optional[float]:
        """Estime la marge profit potentielle avec des calculs plus réalistes."""
        current_price = self._extract_current_price(product)
        if not current_price or current_price <= 0:
            return None

        # Estimation KISS des coûts basée sur le prix de vente
        # En Phase 2+, utiliser un calculateur de frais FBA plus précis
        
        # Frais Amazon estimés : ~15% du prix de vente + frais fixes FBA
        referral_fee = current_price * 0.15
        fba_fees = 3.50  # Estimation moyenne pour un livre standard
        total_fees = referral_fee + fba_fees
        
        # Coût d'achat estimé : 40-60% du prix de vente pour être rentable
        # Utilisons 50% comme estimation de base
        estimated_cost = current_price * 0.50
        
        # Profit net estimé
        net_profit = current_price - total_fees - estimated_cost
        
        # Marge en % du coût d'achat (ROI)
        if estimated_cost > 0:
            margin_percent = (net_profit / estimated_cost) * 100
            return margin_percent
        
        return 0.0
    
    def _is_product_viable(self, product: Dict, criteria: NicheAnalysisCriteria) -> bool:
        """Détermine si un produit respecte les critères de viabilité."""
        try:
            # BSR dans la plage
            bsr = self._extract_bsr(product)
            if not bsr or not (criteria.bsr_range[0] <= bsr <= criteria.bsr_range[1]):
                return False
            
            # Nombre de vendeurs acceptable
            sellers = self._estimate_seller_count(product)
            if sellers > criteria.max_sellers:
                return False
            
            # Marge profit suffisante
            margin = self._estimate_profit_margin(product, criteria)
            if not margin or margin < criteria.min_margin_percent:
                return False
            
            # Stabilité prix suffisante
            stability = self._calculate_price_stability(product)
            if not stability or stability < criteria.min_price_stability:
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Erreur évaluation viabilité produit: {e}")
            return False
    
    def get_available_categories(self) -> List[CategoryOverview]:
        """Retourne la liste des catégories disponibles pour analyse."""
        categories = []
        
        for cat_id, cat_name in self.target_categories.items():
            categories.append(CategoryOverview(
                category_id=cat_id,
                category_name=cat_name,
                parent_category="Books" if "Books" in cat_name else "Other",
                estimated_products=100,  # Estimation pour Phase 1
                last_analyzed=None,
                is_eligible=True
            ))
        
        return categories
    
    def get_recommended_categories(self) -> List[int]:
        """Retourne les catégories recommandées pour débuter (Phase 1)."""
        # Sélection basée sur expérience métier
        return [
            3738,  # Medical Books
            4142,  # Engineering
            3546,  # Programming
            2578,  # Accounting
            4277   # Test Preparation
        ]