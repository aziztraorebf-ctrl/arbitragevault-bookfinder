#!/usr/bin/env python3
"""
AutoScheduler Runner - AutoSourcing planifié pour ArbitrageVault
Exécute des recherches AutoSourcing automatiques selon horaire configuré.
"""
import os
import sys
import asyncio
import json
import tempfile
from datetime import datetime, time
from pathlib import Path
from typing import Dict, Any, List, Optional
import keyring

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from app.core.settings import get_settings
from app.core.database import get_async_session, Base, engine
from app.services.autosourcing_service import AutoSourcingService
from app.services.autoscheduler_metrics import AutoSchedulerMetrics
from app.models.autosourcing import DiscoveryRequest, SearchConfig, SavedProfile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

# Configuration logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)
logger = structlog.get_logger()

# Configuration AutoScheduler
SCHEDULE_CONFIG = {
    "enabled": os.getenv("AUTOSOURCING_ENABLED", "true").lower() == "true",
    "hours": json.loads(os.getenv("AUTOSOURCING_HOURS", "[8, 15, 20]")),
    "max_results": int(os.getenv("AUTOSOURCING_MAX_RESULTS", "45")),
    "token_budget_daily": int(os.getenv("AUTOSOURCING_TOKEN_BUDGET", "12000")),
    "bsr_max": int(os.getenv("AUTOSOURCING_BSR_MAX", "250000")),
    "profile_rotation": os.getenv("AUTOSOURCING_PROFILE_ROTATION", "true").lower() == "true",
    "lock_file": "/tmp/autoscheduler.lock"
}

class AutoSchedulerRunner:
    """Gestionnaire principal de l'AutoScheduler"""
    
    def __init__(self):
        self.metrics = AutoSchedulerMetrics()
        self.lock_file = Path(SCHEDULE_CONFIG["lock_file"])
        
    def is_running(self) -> bool:
        """Vérifie si l'AutoScheduler est déjà en cours d'exécution"""
        return self.lock_file.exists()
    
    def create_lock(self):
        """Crée le fichier de verrou"""
        try:
            self.lock_file.write_text(str(os.getpid()))
            logger.info("🔒 Lock file créé")
        except Exception as e:
            logger.error(f"Erreur création lock file: {e}")
            raise
    
    def remove_lock(self):
        """Supprime le fichier de verrou"""
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
                logger.info("🔓 Lock file supprimé")
        except Exception as e:
            logger.warning(f"Erreur suppression lock file: {e}")
    
    def should_run_now(self) -> bool:
        """Détermine si un run doit être exécuté maintenant"""
        # Lire configuration de contrôle dynamique
        control_config = self._load_control_config()
        
        # Vérification activation générale
        if not control_config.get("enabled", True):
            logger.info("AutoScheduler désactivé via contrôle")
            return False
        
        # Vérification date du jour
        today = datetime.now().date().isoformat()
        skip_dates = control_config.get("skip_dates", [])
        
        if today in skip_dates:
            logger.info(f"AutoScheduler en pause pour aujourd'hui ({today})")
            return False
        
        # Vérification pause jusqu'à date
        pause_until = control_config.get("pause_until")
        if pause_until and pause_until >= today:
            logger.info(f"AutoScheduler en pause jusqu'au {pause_until}")
            return False
        
        # Vérification horaire
        current_hour = datetime.now().hour
        scheduled_hours = control_config.get("scheduled_hours", SCHEDULE_CONFIG["hours"])
        
        should_run = current_hour in scheduled_hours

        if should_run:
            logger.info(f"[OK] Heure de run détectée: {current_hour}h (programmé: {scheduled_hours})")
        else:
            logger.debug(f"[INFO] Pas l'heure de run: {current_hour}h (programmé: {scheduled_hours})")
        
        return should_run
    
    def _load_control_config(self) -> Dict[str, Any]:
        """Charge la configuration de contrôle dynamique"""
        control_file = Path("data/autoscheduler_control.json")
        
        if not control_file.exists():
            # Configuration par défaut basée sur les variables d'environnement
            return {
                "enabled": SCHEDULE_CONFIG["enabled"],
                "scheduled_hours": SCHEDULE_CONFIG["hours"],
                "skip_dates": [],
                "pause_until": None
            }
        
        try:
            with open(control_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.debug(f"Configuration de contrôle chargée: {config}")
                return config
        except Exception as e:
            logger.warning(f"Erreur lecture contrôle config: {e}, utilisation config par défaut")
            return {
                "enabled": SCHEDULE_CONFIG["enabled"],
                "scheduled_hours": SCHEDULE_CONFIG["hours"],
                "skip_dates": [],
                "pause_until": None
            }
    
    def get_search_criteria_for_hour(self, hour: int) -> Dict[str, Any]:
        """Génère les critères de recherche diversifiés selon l'heure"""
        if not SCHEDULE_CONFIG["profile_rotation"]:
            # Profil standard si rotation désactivée
            return {
                "categories": ["Books"],
                "price_range": {"min": 15, "max": 50},
                "bsr_range": {"min": 1000, "max": 150000}
            }
        
        # Profils diversifiés par heure
        hour_profiles = {
            8: {  # Matin: Conservateur
                "categories": ["Books"],
                "price_range": {"min": 10, "max": 35},
                "bsr_range": {"min": 1000, "max": 75000}
            },
            15: {  # Midi: Équilibré
                "categories": ["Books"],
                "price_range": {"min": 15, "max": 50},
                "bsr_range": {"min": 1000, "max": 150000}
            },
            20: {  # Soir: Agressif + Large BSR
                "categories": ["Books"],
                "price_range": {"min": 20, "max": 60},
                "bsr_range": {"min": 1000, "max": SCHEDULE_CONFIG["bsr_max"]}
            }
        }
        
        profile = hour_profiles.get(hour, hour_profiles[15])  # Default à midi
        logger.info(f"📊 Profil {hour}h: Prix ${profile['price_range']['min']}-{profile['price_range']['max']}, BSR ≤{profile['bsr_range']['max']}")
        
        return profile
    
    async def run_autoscheduler(self) -> Optional[Dict[str, Any]]:
        """
        Exécute un cycle AutoScheduler complet.
        
        Returns:
            Résumé du run ou None si erreur
        """
        current_hour = datetime.now().hour
        
        # Vérification budget tokens
        if not self.metrics.check_token_budget(SCHEDULE_CONFIG["token_budget_daily"]):
            logger.warning("🚫 Budget tokens quotidien épuisé - skip run")
            return None
        
        # Création de la session database
        async with get_async_session() as db:
            try:
                autosourcing_service = AutoSourcingService(db)
                
                # Génération critères de recherche diversifiés
                search_criteria = self.get_search_criteria_for_hour(current_hour)
                max_results = SCHEDULE_CONFIG["max_results"]
                
                # Configuration de recherche
                search_config = SearchConfig(
                    categories=search_criteria["categories"],
                    price_range_min=float(search_criteria["price_range"]["min"]),
                    price_range_max=float(search_criteria["price_range"]["max"]),
                    bsr_threshold=search_criteria["bsr_range"]["max"],
                    profit_margin_min=0.25,  # 25% minimum
                    roi_threshold=0.30       # 30% ROI minimum
                )
                
                # Requête de découverte
                discovery_request = DiscoveryRequest(
                    name=f"AutoScheduler {current_hour}h - {datetime.now().strftime('%Y-%m-%d')}",
                    search_config=search_config,
                    max_products=max_results,
                    scheduler_run_id=f"auto_{datetime.now().strftime('%Y%m%d_%H%M')}"
                )
                
                logger.info(f"🚀 Démarrage AutoScheduler {current_hour}h - {max_results} produits max")
                self.metrics.record_run_start(current_hour, max_results)
                
                # Exécution de la recherche
                job_result = await autosourcing_service.discover_products(discovery_request)
                
                # Extraction des produits avec tiers
                products_with_tiers = []
                tokens_estimated = 0  # TODO: récupérer vrais tokens depuis KeepaService
                
                for pick in job_result.discovered_products:
                    product_data = {
                        "asin": pick.asin,
                        "title": pick.title,
                        "profit_net": pick.profit_net,
                        "roi_percentage": pick.roi_percentage,
                        "priority_tier": pick.priority_tier,
                        "tier_reason": pick.tier_reason,
                        "is_featured": pick.is_featured,
                        "bsr": pick.bsr,
                        "overall_rating": pick.overall_rating,
                        "created_at": pick.created_at.isoformat()
                    }
                    products_with_tiers.append(product_data)
                
                # Estimation tokens (approximative basée sur produits trouvés)
                tokens_estimated = len(products_with_tiers) * 25  # ~25 tokens par produit
                
                # Enregistrement métriques
                self.metrics.record_run_completion(products_with_tiers, tokens_estimated, current_hour)
                
                # Résumé du run
                run_summary = {
                    "hour": current_hour,
                    "job_id": str(job_result.id),
                    "products_found": len(products_with_tiers),
                    "tokens_estimated": tokens_estimated,
                    "tier_distribution": self._count_tiers(products_with_tiers),
                    "top_opportunities": self._get_top_opportunities(products_with_tiers, 3),
                    "status": "success",
                    "timestamp": datetime.now().isoformat()
                }
                
                logger.info(f"[OK] AutoScheduler {current_hour}h terminé", extra={"run_summary": run_summary})
                return run_summary

            except Exception as e:
                self.metrics.record_error("run_execution", str(e))
                logger.error(f"[ERROR] Erreur AutoScheduler: {e}")
                return None
    
    def _count_tiers(self, products: List[Dict]) -> Dict[str, int]:
        """Compte la distribution des tiers"""
        tiers = {"HOT": 0, "TOP": 0, "WATCH": 0, "OTHER": 0}
        for product in products:
            tier = product.get("priority_tier", "OTHER")
            if tier in tiers:
                tiers[tier] += 1
        return tiers
    
    def _get_top_opportunities(self, products: List[Dict], limit: int = 3) -> List[Dict]:
        """Récupère les top opportunités par ROI"""
        sorted_products = sorted(products, key=lambda p: p.get("roi_percentage", 0), reverse=True)
        return [{
            "asin": p["asin"], 
            "title": p["title"][:60] + "..." if len(p["title"]) > 60 else p["title"],
            "roi": p["roi_percentage"],
            "tier": p["priority_tier"]
        } for p in sorted_products[:limit]]

async def main():
    """Point d'entrée principal"""
    runner = AutoSchedulerRunner()

    logger.info("[INFO] AutoScheduler démarré", extra={"config": SCHEDULE_CONFIG})

    # Vérification lock file
    if runner.is_running():
        logger.warning("[WARN] AutoScheduler déjà en cours - abandon")
        return

    # Vérification horaire
    if not runner.should_run_now():
        logger.info("[INFO] Pas l'heure de run - arrêt")
        return
    
    # Exécution avec protection lock
    try:
        runner.create_lock()
        
        # Run principal
        result = await runner.run_autoscheduler()
        
        if result:
            logger.info("[OK] AutoScheduler terminé avec succès")

            # Log résumé quotidien
            daily_summary = runner.metrics.log_daily_summary()
            print("\n[INFO] RESUME QUOTIDIEN:")
            for key, value in daily_summary.items():
                print(f"  {key}: {value}")
        else:
            logger.warning("[WARN] AutoScheduler terminé sans résultat")

    except Exception as e:
        logger.error(f"[ERROR] Erreur critique AutoScheduler: {e}")
        
    finally:
        runner.remove_lock()

if __name__ == "__main__":
    asyncio.run(main())