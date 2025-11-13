"""
Tests unitaires pour Niche Discovery Service
============================================

Tests Phase 1 KISS pour validation de la logique de scoring et analyse.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from app.models.niche import NicheAnalysisCriteria, NicheMetrics
from app.services.niche_scoring_service import NicheScoringService
from app.services.category_analyzer import CategoryAnalyzer


class TestNicheScoringService:
    """Tests pour le service de scoring des niches."""
    
    def setup_method(self):
        """Setup pour chaque test."""
        self.scoring_service = NicheScoringService()
        self.default_criteria = NicheAnalysisCriteria(
            bsr_range=(10000, 50000),
            max_sellers=3,
            min_margin_percent=30.0,
            min_price_stability=0.75
        )
    
    def test_competition_scoring(self):
        """Test scoring basé sur concurrence."""
        # Faible concurrence = score élevé
        assert self.scoring_service._score_competition(1.0) == 10.0  # Score parfait pour 1 vendeur
        assert self.scoring_service._score_competition(2.5) == 8.0
        assert self.scoring_service._score_competition(5.0) == 4.0
        assert self.scoring_service._score_competition(10.0) == 1.0
    
    def test_profitability_scoring(self):
        """Test scoring basé sur profitabilité."""
        assert self.scoring_service._score_profitability(50.0) == 10.0
        assert self.scoring_service._score_profitability(35.0) == 8.0
        assert self.scoring_service._score_profitability(25.0) == 5.0
        assert self.scoring_service._score_profitability(10.0) == 1.0
    
    def test_stability_scoring(self):
        """Test scoring basé sur stabilité prix."""
        assert self.scoring_service._score_stability(0.95) == 10.0
        assert self.scoring_service._score_stability(0.85) == 8.0
        assert self.scoring_service._score_stability(0.75) == 6.0
        assert self.scoring_service._score_stability(0.50) == 1.0
    
    def test_market_size_scoring(self):
        """Test scoring basé sur taille de marché (BSR)."""
        # BSR au centre de la plage = score optimal
        center_bsr = (10000 + 50000) / 2  # 30000
        score_center = self.scoring_service._score_market_size(center_bsr, (10000, 50000))
        assert score_center == 10.0
        
        # BSR aux limites = score acceptable
        score_min = self.scoring_service._score_market_size(10000, (10000, 50000))
        score_max = self.scoring_service._score_market_size(50000, (10000, 50000))
        assert 6.0 <= score_min <= 10.0
        assert 6.0 <= score_max <= 10.0
        
        # BSR hors plage = score pénalisé
        score_too_low = self.scoring_service._score_market_size(5000, (10000, 50000))
        score_too_high = self.scoring_service._score_market_size(100000, (10000, 50000))
        assert score_too_low < 5.0
        assert score_too_high < 5.0
    
    def test_viability_scoring(self):
        """Test scoring basé sur viabilité produits."""
        assert self.scoring_service._score_viability(80, 100) == 10.0  # 80% viable
        assert self.scoring_service._score_viability(50, 100) == 7.0   # 50% viable
        assert self.scoring_service._score_viability(20, 100) == 2.0   # 20% viable
        assert self.scoring_service._score_viability(0, 100) == 1.0    # 0% viable
        
        # Cas limite: pas de produits
        assert self.scoring_service._score_viability(0, 0) == 0.0
    
    def test_overall_niche_scoring(self):
        """Test scoring global d'une niche."""
        # Niche excellente
        excellent_metrics = NicheMetrics(
            avg_sellers=1.5,      # Faible concurrence
            avg_bsr=25000,        # BSR optimal
            avg_price=35.0,
            price_stability=0.90, # Très stable
            profit_margin=45.0,   # Marge excellente
            total_products=100,
            viable_products=80,   # 80% viables
            competition_level=""
        )
        
        score, confidence, quality = self.scoring_service.calculate_niche_score(
            excellent_metrics, self.default_criteria
        )
        
        assert score >= 8.5  # Score excellent attendu
        assert confidence == "High"  # 100 produits = high confidence
        assert quality in ["Excellent", "Good"]
        
        # Niche médiocre
        poor_metrics = NicheMetrics(
            avg_sellers=8.0,      # Haute concurrence
            avg_bsr=25000,
            avg_price=15.0,
            price_stability=0.60, # Instable
            profit_margin=15.0,   # Marge faible
            total_products=10,    # Petit échantillon
            viable_products=2,    # 20% viables seulement
            competition_level=""
        )
        
        score, confidence, quality = self.scoring_service.calculate_niche_score(
            poor_metrics, self.default_criteria
        )
        
        assert score <= 4.0  # Score faible attendu
        assert confidence == "Low"  # 10 produits = low confidence
    
    def test_competition_classification(self):
        """Test classification niveau de concurrence."""
        assert self.scoring_service.classify_competition_level(2.0) == "Low"
        assert self.scoring_service.classify_competition_level(4.0) == "Medium"
        assert self.scoring_service.classify_competition_level(8.0) == "High"


class TestCategoryAnalyzer:
    """Tests pour l'analyseur de catégories."""
    
    def setup_method(self):
        """Setup pour chaque test."""
        self.mock_keepa_service = Mock()
        self.analyzer = CategoryAnalyzer(self.mock_keepa_service)
        self.criteria = NicheAnalysisCriteria()
    
    def test_available_categories(self):
        """Test récupération catégories disponibles."""
        categories = self.analyzer.get_available_categories()
        
        assert len(categories) > 0
        assert all(cat.is_eligible for cat in categories)
        assert all(cat.category_id > 0 for cat in categories)
        assert all(cat.category_name for cat in categories)
    
    def test_recommended_categories(self):
        """Test catégories recommandées."""
        recommended = self.analyzer.get_recommended_categories()
        
        assert len(recommended) >= 3  # Au moins quelques recommandations
        assert all(isinstance(cat_id, int) for cat_id in recommended)
        
        # Vérifier que les recommandées sont dans les disponibles
        available_ids = [cat.category_id for cat in self.analyzer.get_available_categories()]
        assert all(rec_id in available_ids for rec_id in recommended)
    
    def test_sample_asins_generation(self):
        """Test génération ASINs d'échantillon."""
        # Test avec catégorie connue
        medical_asins = self.analyzer._get_sample_asins_for_category(3738)
        assert len(medical_asins) >= 5
        assert all(isinstance(asin, str) for asin in medical_asins)
        assert all(len(asin) == 10 for asin in medical_asins)  # Format ASIN standard
        
        # Test avec catégorie inconnue (fallback)
        unknown_asins = self.analyzer._get_sample_asins_for_category(99999)
        assert len(unknown_asins) >= 5
    
    def test_seller_count_estimation(self):
        """Test estimation nombre de vendeurs."""
        # Produit avec Amazon disponible
        product_with_amazon = {
            'asin': 'TEST123456',
            'availabilityAmazon': 0,  # En stock
            'csv': [
                [100, 200, 150, 180],  # Prix Amazon
                [120, 220, 170, 200],  # Prix NEW
                [80, 160, 130, 150]    # Prix USED
            ]
        }
        
        sellers = self.analyzer._estimate_seller_count(product_with_amazon)
        assert sellers >= 2.0  # Amazon + au moins un autre
        assert sellers <= 10.0  # Cap maximum
        
        # Produit sans Amazon
        product_no_amazon = {
            'asin': 'TEST789012',
            'availabilityAmazon': -1,  # Pas disponible
            'csv': []
        }
        
        sellers_no_amazon = self.analyzer._estimate_seller_count(product_no_amazon)
        assert sellers_no_amazon >= 1.0  # Au moins un vendeur de base
    
    def test_bsr_extraction(self):
        """Test extraction BSR."""
        # Via salesRanks
        product_with_ranks = {
            'salesRanks': {1000: 25000, 2345: 5000},
            'salesRankReference': 30000
        }
        
        bsr = self.analyzer._extract_bsr(product_with_ranks)
        assert bsr in [25000, 5000]  # Un des BSR disponibles
        
        # Fallback sur salesRankReference
        product_with_ref = {
            'salesRanks': {},
            'salesRankReference': 40000
        }
        
        bsr_ref = self.analyzer._extract_bsr(product_with_ref)
        assert bsr_ref == 40000
        
        # Pas de BSR valide
        product_no_bsr = {
            'salesRanks': {},
            'salesRankReference': 0
        }
        
        bsr_none = self.analyzer._extract_bsr(product_no_bsr)
        assert bsr_none is None
    
    def test_price_extraction(self):
        """Test extraction prix actuel."""
        product_with_price = {
            'csv': [
                [1500, 1600, 1550, 1580, None, 1590]  # Prix en centimes
            ]
        }
        
        price = self.analyzer._extract_current_price(product_with_price)
        assert price == 15.90  # Dernier prix valide en dollars
        
        # Pas de prix valide
        product_no_price = {
            'csv': [[None, None, 0]]
        }
        
        price_none = self.analyzer._extract_current_price(product_no_price)
        assert price_none is None
    
    def test_price_stability_calculation(self):
        """Test calcul stabilité prix."""
        # Prix très stables
        stable_prices = [1500] * 10  # Prix identiques
        product_stable = {
            'csv': [stable_prices]
        }
        
        stability = self.analyzer._calculate_price_stability(product_stable)
        assert stability >= 0.95  # Très stable
        
        # Prix volatiles
        volatile_prices = [1000, 2000, 1200, 1800, 1100, 1900, 1300]
        product_volatile = {
            'csv': [volatile_prices]
        }
        
        volatility = self.analyzer._calculate_price_stability(product_volatile)
        assert volatility < 0.8  # Instable
        
        # Pas assez de données
        product_insufficient = {
            'csv': [[1500, 1600]]  # Seulement 2 prix
        }
        
        stability_none = self.analyzer._calculate_price_stability(product_insufficient)
        assert stability_none is None


class TestIntegrationScenarios:
    """Tests d'intégration pour scénarios réels."""
    
    def test_realistic_niche_scoring(self):
        """Test avec données réalistes simulant vraie niche."""
        scoring_service = NicheScoringService()
        criteria = NicheAnalysisCriteria(
            bsr_range=(15000, 40000),
            max_sellers=3,
            min_margin_percent=25.0,
            min_price_stability=0.70
        )
        
        # Simule "Medical Textbooks" niche
        medical_niche_metrics = NicheMetrics(
            avg_sellers=2.3,      # Faible concurrence
            avg_bsr=28000,        # Dans la plage optimale
            avg_price=85.50,      # Prix élevé typique
            price_stability=0.82, # Stable (audience captive)
            profit_margin=34.5,   # Bonne marge
            total_products=45,    # Échantillon moyen
            viable_products=31,   # 69% viables
            competition_level=""
        )
        
        score, confidence, quality = scoring_service.calculate_niche_score(
            medical_niche_metrics, criteria
        )
        
        # Attentes pour une vraie bonne niche
        assert score >= 7.0  # Score solide
        assert confidence == "Medium"  # 45 produits
        assert quality in ["Good", "Excellent"]
        
        # Simule "General Fiction" (mauvaise niche)
        fiction_niche_metrics = NicheMetrics(
            avg_sellers=12.8,     # Très haute concurrence
            avg_bsr=28000,
            avg_price=12.99,      # Prix bas
            price_stability=0.55, # Très instable
            profit_margin=8.2,    # Marge insuffisante
            total_products=200,   # Grand échantillon
            viable_products=15,   # Seulement 7.5% viables
            competition_level=""
        )
        
        score_bad, confidence_bad, quality_bad = scoring_service.calculate_niche_score(
            fiction_niche_metrics, criteria
        )
        
        assert score_bad <= 3.0  # Score faible
        assert confidence_bad == "High"  # 200 produits
        assert quality_bad in ["Poor", "Very Poor"]
        
        # La bonne niche doit avoir un meilleur score
        assert score > score_bad


if __name__ == "__main__":
    pytest.main([__file__])