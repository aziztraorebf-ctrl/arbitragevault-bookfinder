#!/usr/bin/env python3
"""
Test complet du système AutoScheduler avec validation BUILD-TEST-VALIDATE
"""
import asyncio
import os
import sys
import tempfile
import json
from datetime import datetime, time
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / 'backend'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.db import Base
from app.services.autosourcing_service import AutoSourcingService
from app.services.autoscheduler_metrics import AutoSchedulerMetrics
from app.models.autosourcing import DiscoveryRequest, SearchConfig, AutoSourcingPick
import structlog

logger = structlog.get_logger()

class AutoSchedulerTester:
    """Testeur complet pour AutoScheduler"""
    
    def __init__(self):
        self.temp_db = None
        self.engine = None
        self.async_session = None
        
    async def setup_test_db(self):
        """Configure une base de données temporaire pour les tests"""
        self.temp_db = tempfile.mktemp(suffix='.db')
        database_url = f"sqlite+aiosqlite:///{self.temp_db}"
        
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        
        # Création des tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info(f"✅ Test DB créée: {self.temp_db}")
        return True
    
    async def teardown_test_db(self):
        """Nettoie la base de données de test"""
        if self.engine:
            await self.engine.dispose()
        if self.temp_db and os.path.exists(self.temp_db):
            os.unlink(self.temp_db)
        logger.info("🗑️ Test DB nettoyée")
    
    async def test_tier_classification(self):
        """BUILD: Test de la classification par tiers"""
        logger.info("🔧 BUILD: Test classification par tiers")
        
        async with self.async_session() as db:
            service = AutoSourcingService(db)
            
            # Test données de différents niveaux
            test_cases = [
                {
                    'roi_percentage': 55,
                    'profit_net': 18.5,
                    'velocity_score': 85,
                    'confidence_score': 90,
                    'overall_rating': 'EXCELLENT',
                    'expected_tier': 'HOT'
                },
                {
                    'roi_percentage': 40,
                    'profit_net': 12.0,
                    'velocity_score': 75,
                    'confidence_score': 80,
                    'overall_rating': 'GOOD',
                    'expected_tier': 'TOP'
                },
                {
                    'roi_percentage': 28,
                    'profit_net': 7.5,
                    'velocity_score': 65,
                    'confidence_score': 70,
                    'overall_rating': 'FAIR',
                    'expected_tier': 'WATCH'
                },
                {
                    'roi_percentage': 15,
                    'profit_net': 3.0,
                    'velocity_score': 50,
                    'confidence_score': 60,
                    'overall_rating': 'PASS',
                    'expected_tier': 'OTHER'
                }
            ]
            
            classification_results = []
            
            for i, test_case in enumerate(test_cases):
                tier, reason = service._classify_product_tier(test_case)
                
                result = {
                    'case': i + 1,
                    'expected': test_case['expected_tier'],
                    'actual': tier,
                    'reason': reason,
                    'roi': test_case['roi_percentage'],
                    'passed': tier == test_case['expected_tier']
                }
                classification_results.append(result)
                
                status = "✅" if result['passed'] else "❌"
                logger.info(f"  {status} Case {i+1}: ROI {test_case['roi_percentage']}% → {tier} (attendu: {test_case['expected_tier']})")
            
            # Validation BUILD
            all_passed = all(r['passed'] for r in classification_results)
            logger.info(f"🏗️ BUILD Classification: {'✅ PASS' if all_passed else '❌ FAIL'}")
            
            return all_passed, classification_results
    
    async def test_diversified_criteria(self):
        """BUILD: Test de la diversification des critères"""
        logger.info("🔧 BUILD: Test diversification critères")
        
        async with self.async_session() as db:
            service = AutoSourcingService(db)
            
            # Test pour chaque heure programmée
            test_hours = [8, 15, 20]
            diversification_results = []
            
            for hour in test_hours:
                criteria = service.get_diversified_search_criteria(hour)
                
                result = {
                    'hour': hour,
                    'price_range': criteria['price_range'],
                    'bsr_max': criteria['bsr_range']['max'],
                    'description': criteria['description']
                }
                diversification_results.append(result)
                
                logger.info(f"  {hour}h: ${criteria['price_range']['min']}-{criteria['price_range']['max']}, BSR ≤{criteria['bsr_range']['max']}")
            
            # Validation: chaque heure doit avoir des critères différents
            unique_configs = len(set(
                (r['price_range']['min'], r['price_range']['max'], r['bsr_max']) 
                for r in diversification_results
            ))
            
            diversification_passed = unique_configs == len(test_hours)
            logger.info(f"🏗️ BUILD Diversification: {'✅ PASS' if diversification_passed else '❌ FAIL'}")
            
            return diversification_passed, diversification_results
    
    async def test_autoscheduler_workflow(self):
        """TEST: Workflow complet AutoScheduler"""
        logger.info("🧪 TEST: Workflow AutoScheduler complet")
        
        async with self.async_session() as db:
            service = AutoSourcingService(db)
            
            # Configuration pour test (équivalent profil 15h)
            search_config = SearchConfig(
                categories=["Books"],
                price_range_min=15.0,
                price_range_max=50.0,
                bsr_threshold=150000,
                profit_margin_min=0.25,
                roi_threshold=0.30
            )
            
            # Requête de découverte
            discovery_request = DiscoveryRequest(
                name="TEST AutoScheduler Workflow",
                search_config=search_config,
                max_products=10,  # Limité pour test rapide
                scheduler_run_id="test_run_001"
            )
            
            logger.info("🚀 Lancement découverte test...")
            
            try:
                # Exécution recherche
                job_result = await service.discover_products(discovery_request)
                
                # Vérifications workflow
                workflow_checks = {
                    'job_created': job_result is not None,
                    'has_products': len(job_result.discovered_products) > 0,
                    'products_have_tiers': all(
                        hasattr(p, 'priority_tier') and p.priority_tier 
                        for p in job_result.discovered_products
                    ),
                    'scheduler_run_id_set': all(
                        hasattr(p, 'scheduler_run_id') 
                        for p in job_result.discovered_products
                    )
                }
                
                # Analyse des tiers
                tier_counts = {'HOT': 0, 'TOP': 0, 'WATCH': 0, 'OTHER': 0}
                for product in job_result.discovered_products:
                    tier = getattr(product, 'priority_tier', 'OTHER')
                    if tier in tier_counts:
                        tier_counts[tier] += 1
                
                logger.info(f"✅ Job {job_result.id} créé avec {len(job_result.discovered_products)} produits")
                logger.info(f"📊 Distribution tiers: {tier_counts}")
                
                workflow_passed = all(workflow_checks.values())
                logger.info(f"🧪 TEST Workflow: {'✅ PASS' if workflow_passed else '❌ FAIL'}")
                
                return workflow_passed, {
                    'job_id': str(job_result.id),
                    'products_count': len(job_result.discovered_products),
                    'tier_counts': tier_counts,
                    'checks': workflow_checks
                }
                
            except Exception as e:
                logger.error(f"❌ Erreur workflow: {e}")
                return False, {'error': str(e)}
    
    async def test_metrics_tracking(self):
        """TEST: Système de métriques"""
        logger.info("🧪 TEST: Métriques AutoScheduler")
        
        # Test des métriques
        metrics = AutoSchedulerMetrics(metrics_dir="./test_metrics")
        
        # Simulation données produits
        test_products = [
            {'priority_tier': 'HOT', 'profit_net': 20.0, 'roi_percentage': 60, 'bsr': 25000},
            {'priority_tier': 'TOP', 'profit_net': 15.0, 'roi_percentage': 40, 'bsr': 85000},
            {'priority_tier': 'WATCH', 'profit_net': 8.0, 'roi_percentage': 25, 'bsr': 180000},
            {'priority_tier': 'OTHER', 'profit_net': 4.0, 'roi_percentage': 18, 'bsr': 300000}
        ]
        
        # Test enregistrement run
        metrics.record_run_completion(test_products, 150, 15)  # 150 tokens à 15h
        
        # Validation métriques
        summary = metrics.get_daily_summary()
        
        metrics_checks = {
            'runs_completed': summary['runs_completed'] == 1,
            'products_discovered': summary['products_discovered'] == 4,
            'tokens_consumed': summary['tokens_consumed'] == 150,
            'tier_distribution': summary['tier_distribution']['HOT'] == 1,
            'efficiency_calculated': float(summary['efficiency'].split()[0]) == 37.5  # 150/4
        }
        
        # Test budget check
        budget_ok = metrics.check_token_budget(12000)  # 150 < 12000
        budget_exceeded = not metrics.check_token_budget(100)  # 150 > 100
        
        metrics_checks['budget_check_ok'] = budget_ok
        metrics_checks['budget_check_exceeded'] = budget_exceeded
        
        metrics_passed = all(metrics_checks.values())
        logger.info(f"🧪 TEST Métriques: {'✅ PASS' if metrics_passed else '❌ FAIL'}")
        
        # Cleanup
        import shutil
        if os.path.exists("./test_metrics"):
            shutil.rmtree("./test_metrics")
        
        return metrics_passed, metrics_checks

async def run_complete_validation():
    """VALIDATE: Validation complète du système AutoScheduler"""
    logger.info("🎯 VALIDATION COMPLÈTE AutoScheduler")
    logger.info("=" * 60)
    
    tester = AutoSchedulerTester()
    
    try:
        # Setup
        await tester.setup_test_db()
        
        # BUILD Phase
        logger.info("\n🏗️ PHASE BUILD: Construction des composants")
        
        classification_passed, classification_results = await tester.test_tier_classification()
        diversification_passed, diversification_results = await tester.test_diversified_criteria()
        
        build_passed = classification_passed and diversification_passed
        
        # TEST Phase  
        logger.info("\n🧪 PHASE TEST: Tests fonctionnels")
        
        workflow_passed, workflow_results = await tester.test_autoscheduler_workflow()
        metrics_passed, metrics_results = await tester.test_metrics_tracking()
        
        test_passed = workflow_passed and metrics_passed
        
        # VALIDATE Phase
        logger.info("\n✅ PHASE VALIDATE: Validation finale")
        
        overall_passed = build_passed and test_passed
        
        # Résumé final
        logger.info("\n📊 RÉSULTATS FINAUX")
        logger.info("=" * 40)
        logger.info(f"🏗️ BUILD:    {'✅ PASS' if build_passed else '❌ FAIL'}")
        logger.info(f"🧪 TEST:     {'✅ PASS' if test_passed else '❌ FAIL'}")
        logger.info(f"✅ VALIDATE: {'✅ PASS' if overall_passed else '❌ FAIL'}")
        
        if overall_passed:
            logger.info("\n🎉 AutoScheduler PRÊT POUR PRODUCTION!")
            logger.info("Configuration recommandée:")
            logger.info("  - Horaires: [8, 15, 20]")
            logger.info("  - 45 produits/run max")
            logger.info("  - Budget: 12,000 tokens/jour")
            logger.info("  - BSR max: 250,000")
        else:
            logger.info("\n⚠️ AutoScheduler nécessite des corrections")
        
        return overall_passed
        
    finally:
        await tester.teardown_test_db()

if __name__ == "__main__":
    asyncio.run(run_complete_validation())