"""
Niche Scoring Service - Calcul des scores de niches
===================================================

Service pour calculer les scores et rankings des niches découvertes.
Utilise un algorithme KISS basé sur les métriques clés business.
"""

import logging
from typing import Dict, List, Tuple
from app.models.niche import NicheMetrics, NicheAnalysisCriteria

logger = logging.getLogger(__name__)


class NicheScoringService:
    """Service de scoring pour les niches de marché."""
    
    def __init__(self):
        # Poids des facteurs dans le calcul du score (total = 1.0)
        self.scoring_weights = {
            'competition': 0.30,      # Faible concurrence = meilleur score
            'profitability': 0.25,    # Marge profit élevée
            'stability': 0.20,        # Stabilité prix
            'market_size': 0.15,      # Taille marché (BSR)
            'viability': 0.10         # % produits viables
        }
        
        # Seuils pour classification
        self.competition_thresholds = {
            'low': 2.5,      # ≤2.5 vendeurs moyen = Low competition
            'medium': 5.0    # >2.5 et ≤5.0 = Medium, >5.0 = High
        }
        
        self.confidence_thresholds = {
            'high': 50,      # ≥50 produits analysés = High confidence
            'medium': 20     # 20-49 = Medium, <20 = Low
        }
    
    def calculate_niche_score(
        self, 
        metrics: NicheMetrics, 
        criteria: NicheAnalysisCriteria
    ) -> Tuple[float, str, str]:
        """
        Calcule le score global d'une niche (1-10).
        
        Args:
            metrics: Métriques calculées de la niche
            criteria: Critères d'analyse utilisés
            
        Returns:
            Tuple (score, confidence_level, quality_assessment)
        """
        try:
            # 1. Score Competition (0-10) - Inversé : moins de vendeurs = meilleur score
            competition_score = self._score_competition(metrics.avg_sellers)
            
            # 2. Score Profitability (0-10)
            profitability_score = self._score_profitability(metrics.profit_margin)
            
            # 3. Score Stability (0-10)
            stability_score = self._score_stability(metrics.price_stability)
            
            # 4. Score Market Size (0-10) - BSR optimal dans la plage demandée
            market_size_score = self._score_market_size(metrics.avg_bsr, criteria.bsr_range)
            
            # 5. Score Viability (0-10) - % de produits viables
            viability_score = self._score_viability(metrics.viable_products, metrics.total_products)
            
            # Calcul score pondéré final
            weighted_score = (
                competition_score * self.scoring_weights['competition'] +
                profitability_score * self.scoring_weights['profitability'] +
                stability_score * self.scoring_weights['stability'] +
                market_size_score * self.scoring_weights['market_size'] +
                viability_score * self.scoring_weights['viability']
            )
            
            # Arrondir à 1 décimale
            final_score = round(weighted_score, 1)
            
            # Déterminer niveau de confiance basé sur taille échantillon
            confidence_level = self._determine_confidence_level(metrics.total_products)
            
            # Évaluation qualité globale
            quality_assessment = self._assess_quality(metrics, final_score)
            
            logger.debug(
                f"Niche scoring - Final: {final_score}, "
                f"Competition: {competition_score}, Profit: {profitability_score}, "
                f"Stability: {stability_score}, Market: {market_size_score}, "
                f"Viability: {viability_score}"
            )
            
            return final_score, confidence_level, quality_assessment
            
        except Exception as e:
            logger.error(f"Erreur calcul score niche: {e}")
            return 0.0, "Low", "Error in scoring"
    
    def _score_competition(self, avg_sellers: float) -> float:
        """Score competition (0-10) - Moins de vendeurs = meilleur score."""
        if avg_sellers <= 1.0:
            return 10.0
        elif avg_sellers <= 2.0:
            return 9.0
        elif avg_sellers <= 3.0:
            return 8.0
        elif avg_sellers <= 4.0:
            return 6.0
        elif avg_sellers <= 5.0:
            return 4.0
        elif avg_sellers <= 7.0:
            return 2.0
        else:
            return 1.0
    
    def _score_profitability(self, profit_margin: float) -> float:
        """Score profitability (0-10) basé sur marge profit %."""
        if profit_margin >= 50.0:
            return 10.0
        elif profit_margin >= 40.0:
            return 9.0
        elif profit_margin >= 35.0:
            return 8.0
        elif profit_margin >= 30.0:
            return 7.0
        elif profit_margin >= 25.0:
            return 5.0
        elif profit_margin >= 20.0:
            return 3.0
        elif profit_margin >= 15.0:
            return 2.0
        else:
            return 1.0
    
    def _score_stability(self, price_stability: float) -> float:
        """Score stability (0-10) basé sur stabilité prix."""
        if price_stability >= 0.95:
            return 10.0
        elif price_stability >= 0.90:
            return 9.0
        elif price_stability >= 0.85:
            return 8.0
        elif price_stability >= 0.80:
            return 7.0
        elif price_stability >= 0.75:
            return 6.0
        elif price_stability >= 0.70:
            return 4.0
        elif price_stability >= 0.60:
            return 2.0
        else:
            return 1.0
    
    def _score_market_size(self, avg_bsr: float, bsr_range: Tuple[int, int]) -> float:
        """Score market size (0-10) - BSR dans la plage optimale."""
        bsr_min, bsr_max = bsr_range
        bsr_center = (bsr_min + bsr_max) / 2
        
        # Score maximum si BSR proche du centre de la plage
        if bsr_min <= avg_bsr <= bsr_max:
            # Distance relative du centre (0 = au centre, 1 = aux extrémités)
            distance_from_center = abs(avg_bsr - bsr_center) / (bsr_max - bsr_min) * 2
            return max(6.0, 10.0 - (distance_from_center * 4))
        
        # Pénalité si en dehors de la plage
        if avg_bsr < bsr_min:
            # BSR trop bon (marché trop petit)
            if avg_bsr > bsr_min * 0.5:
                return 4.0
            else:
                return 2.0
        else:
            # BSR trop élevé (marché trop saturé)
            if avg_bsr < bsr_max * 2:
                return 3.0
            else:
                return 1.0
    
    def _score_viability(self, viable_products: int, total_products: int) -> float:
        """Score viability (0-10) basé sur % produits viables."""
        if total_products == 0:
            return 0.0
        
        viability_ratio = viable_products / total_products
        
        if viability_ratio >= 0.80:
            return 10.0
        elif viability_ratio >= 0.70:
            return 9.0
        elif viability_ratio >= 0.60:
            return 8.0
        elif viability_ratio >= 0.50:
            return 7.0
        elif viability_ratio >= 0.40:
            return 6.0
        elif viability_ratio >= 0.30:
            return 4.0
        elif viability_ratio >= 0.20:
            return 2.0
        else:
            return 1.0
    
    def _determine_confidence_level(self, sample_size: int) -> str:
        """Détermine le niveau de confiance basé sur la taille d'échantillon."""
        if sample_size >= self.confidence_thresholds['high']:
            return "High"
        elif sample_size >= self.confidence_thresholds['medium']:
            return "Medium"
        else:
            return "Low"
    
    def _assess_quality(self, metrics: NicheMetrics, score: float) -> str:
        """Évalue la qualité globale de l'analyse."""
        if score >= 8.0 and metrics.total_products >= 30:
            return "Excellent"
        elif score >= 7.0 and metrics.total_products >= 20:
            return "Good"
        elif score >= 6.0:
            return "Fair"
        elif score >= 4.0:
            return "Poor"
        else:
            return "Very Poor"
    
    def classify_competition_level(self, avg_sellers: float) -> str:
        """Classifie le niveau de concurrence."""
        if avg_sellers <= self.competition_thresholds['low']:
            return "Low"
        elif avg_sellers <= self.competition_thresholds['medium']:
            return "Medium"
        else:
            return "High"
    
    def rank_niches(self, scored_niches: List[Tuple]) -> List[Tuple]:
        """
        Trie les niches par score décroissant.
        
        Args:
            scored_niches: Liste de tuples (niche_data, score, confidence, quality)
            
        Returns:
            Liste triée par score décroissant
        """
        return sorted(scored_niches, key=lambda x: x[1], reverse=True)
    
    def get_scoring_explanation(self) -> Dict:
        """Retourne l'explication du système de scoring."""
        return {
            "scoring_weights": self.scoring_weights,
            "factors": {
                "competition": "Nombre moyen de vendeurs (moins = mieux)",
                "profitability": "Marge profit moyenne en %",
                "stability": "Stabilité des prix (0-1)",
                "market_size": "BSR moyen dans plage optimale",
                "viability": "% de produits respectant les critères"
            },
            "score_scale": "1-10 (10 = meilleure niche)",
            "confidence_levels": {
                "High": f"≥{self.confidence_thresholds['high']} produits analysés",
                "Medium": f"{self.confidence_thresholds['medium']}-{self.confidence_thresholds['high']-1} produits",
                "Low": f"<{self.confidence_thresholds['medium']} produits"
            }
        }