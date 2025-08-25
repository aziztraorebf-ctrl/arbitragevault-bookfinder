#!/usr/bin/env python3
"""
AutoScheduler Metrics & Monitoring System
Tracks performance, token usage, and tier distribution for AutoScheduler
"""
import json
import os
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import structlog

logger = structlog.get_logger()

@dataclass
class DailyMetrics:
    """Métriques quotidiennes pour l'AutoScheduler"""
    date: str
    runs_completed: int = 0
    products_discovered: int = 0
    tokens_consumed: int = 0
    tier_distribution: Dict[str, int] = None
    efficiency_ratio: float = 0.0  # tokens per product
    top_opportunity_score: float = 0.0
    bsr_range_coverage: Dict[str, int] = None
    avg_profit_per_tier: Dict[str, float] = None
    last_successful_run: Optional[str] = None
    errors_count: int = 0
    
    def __post_init__(self):
        if self.tier_distribution is None:
            self.tier_distribution = {"HOT": 0, "TOP": 0, "WATCH": 0, "OTHER": 0}
        if self.bsr_range_coverage is None:
            self.bsr_range_coverage = {"0-50k": 0, "50k-150k": 0, "150k+": 0}
        if self.avg_profit_per_tier is None:
            self.avg_profit_per_tier = {"HOT": 0.0, "TOP": 0.0, "WATCH": 0.0}

class AutoSchedulerMetrics:
    """
    Gestionnaire de métriques pour AutoScheduler.
    Sauvegarde et track les performances quotidiennes.
    """
    
    def __init__(self, metrics_dir: str = "data/metrics"):
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.current_date = date.today().isoformat()
        self.metrics_file = self.metrics_dir / f"autoscheduler_{self.current_date}.json"
        
        # Charger métriques existantes ou créer nouvelles
        self.daily_metrics = self._load_daily_metrics()
    
    def _load_daily_metrics(self) -> DailyMetrics:
        """Charge les métriques du jour ou crée nouvelles métriques"""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return DailyMetrics(**data)
            except Exception as e:
                logger.warning(f"Impossible de charger métriques existantes: {e}")
        
        return DailyMetrics(date=self.current_date)
    
    def _save_metrics(self):
        """Sauvegarde les métriques sur disque"""
        try:
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.daily_metrics), f, indent=2, ensure_ascii=False)
            logger.info(f"Métriques sauvegardées: {self.metrics_file}")
        except Exception as e:
            logger.error(f"Erreur sauvegarde métriques: {e}")
    
    def record_run_start(self, hour: int, expected_products: int):
        """Enregistre le début d'un run AutoScheduler"""
        logger.info(f"📊 AutoScheduler run démarré à {hour}h - {expected_products} produits attendus")
    
    def record_run_completion(self, products: List[Dict], tokens_used: int, hour: int):
        """
        Enregistre la completion d'un run AutoScheduler.
        
        Args:
            products: Liste des produits découverts avec tiers
            tokens_used: Nombre de tokens Keepa consommés
            hour: Heure du run
        """
        # Mise à jour compteurs généraux
        self.daily_metrics.runs_completed += 1
        self.daily_metrics.products_discovered += len(products)
        self.daily_metrics.tokens_consumed += tokens_used
        self.daily_metrics.last_successful_run = datetime.now().isoformat()
        
        # Calcul efficiency ratio
        if self.daily_metrics.products_discovered > 0:
            self.daily_metrics.efficiency_ratio = (
                self.daily_metrics.tokens_consumed / self.daily_metrics.products_discovered
            )
        
        # Analyse des tiers et profits
        self._analyze_products(products)
        
        # Analyse BSR coverage
        self._analyze_bsr_coverage(products)
        
        # Sauvegarde
        self._save_metrics()
        
        logger.info(f"✅ Run {hour}h terminé: {len(products)} produits, {tokens_used} tokens")
    
    def _analyze_products(self, products: List[Dict]):
        """Analyse la distribution des tiers et profits"""
        tier_profits = {"HOT": [], "TOP": [], "WATCH": [], "OTHER": []}
        max_score = 0.0
        
        for product in products:
            tier = product.get('priority_tier', 'OTHER')
            profit = product.get('profit_net', 0.0)
            score = product.get('roi_percentage', 0.0)
            
            # Update tier count
            if tier in self.daily_metrics.tier_distribution:
                self.daily_metrics.tier_distribution[tier] += 1
            
            # Collect profits for average
            if tier in tier_profits:
                tier_profits[tier].append(profit)
            
            # Track max score
            max_score = max(max_score, score)
        
        # Calculate average profits per tier
        for tier, profits in tier_profits.items():
            if profits and tier in self.daily_metrics.avg_profit_per_tier:
                self.daily_metrics.avg_profit_per_tier[tier] = sum(profits) / len(profits)
        
        # Update top opportunity score
        self.daily_metrics.top_opportunity_score = max(self.daily_metrics.top_opportunity_score, max_score)
    
    def _analyze_bsr_coverage(self, products: List[Dict]):
        """Analyse la couverture des plages BSR"""
        for product in products:
            bsr = product.get('bsr', 0)
            
            if bsr <= 50000:
                self.daily_metrics.bsr_range_coverage["0-50k"] += 1
            elif bsr <= 150000:
                self.daily_metrics.bsr_range_coverage["50k-150k"] += 1
            else:
                self.daily_metrics.bsr_range_coverage["150k+"] += 1
    
    def record_error(self, error_type: str, error_message: str):
        """Enregistre une erreur lors du run"""
        self.daily_metrics.errors_count += 1
        self._save_metrics()
        
        logger.error(f"❌ AutoScheduler error: {error_type} - {error_message}")
    
    def check_token_budget(self, budget_limit: int) -> bool:
        """
        Vérifie si le budget tokens quotidien est dépassé.
        
        Args:
            budget_limit: Limite quotidienne de tokens
            
        Returns:
            True si budget OK, False si dépassé
        """
        remaining = budget_limit - self.daily_metrics.tokens_consumed
        
        if remaining <= 0:
            logger.warning(f"🚫 Budget tokens épuisé: {self.daily_metrics.tokens_consumed}/{budget_limit}")
            return False
        
        logger.info(f"💰 Budget tokens: {remaining}/{budget_limit} restants")
        return True
    
    def get_daily_summary(self) -> Dict[str, Any]:
        """Retourne un résumé des métriques du jour"""
        return {
            "date": self.daily_metrics.date,
            "runs_completed": self.daily_metrics.runs_completed,
            "products_discovered": self.daily_metrics.products_discovered,
            "tokens_consumed": self.daily_metrics.tokens_consumed,
            "efficiency": f"{self.daily_metrics.efficiency_ratio:.1f} tokens/product",
            "tier_distribution": self.daily_metrics.tier_distribution,
            "top_opportunity": f"{self.daily_metrics.top_opportunity_score:.1f}% ROI",
            "bsr_coverage": self.daily_metrics.bsr_range_coverage,
            "avg_profit_per_tier": {
                k: f"${v:.2f}" for k, v in self.daily_metrics.avg_profit_per_tier.items()
            },
            "errors_count": self.daily_metrics.errors_count,
            "last_run": self.daily_metrics.last_successful_run
        }
    
    def log_daily_summary(self):
        """Log le résumé quotidien pour monitoring"""
        summary = self.get_daily_summary()
        
        logger.info("📊 RÉSUMÉ QUOTIDIEN AutoScheduler", extra={
            "summary": summary
        })
        
        return summary