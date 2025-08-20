#!/usr/bin/env python3
"""
Audit Simple ArbitrageVault
Script d'audit basique utilisant les fixtures de test existantes
"""

import time
import subprocess
import sys
from datetime import datetime
from typing import Dict, Any
import json

def run_command(cmd: str) -> tuple[int, str, str]:
    """Execute une commande et retourne le code, stdout, stderr"""
    # Utiliser uv run pour exécuter dans l'environnement virtuel
    full_cmd = f"uv run {cmd}" if not cmd.startswith("uv") else cmd
    result = subprocess.run(
        full_cmd,
        capture_output=True,
        text=True,
        cwd=".",
        shell=True
    )
    return result.returncode, result.stdout, result.stderr

def measure_time(func):
    """Décorateur pour mesurer le temps d'exécution"""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        return result, duration
    return wrapper

class SimpleAudit:
    """Audit simple du système ArbitrageVault"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "summary": {"total_tests": 0, "passed": 0, "failed": 0, "duration_seconds": 0},
            "tests": []
        }
    
    @measure_time
    def run_repository_tests(self) -> Dict[str, Any]:
        """Lance les tests repository existants"""
        print("🔍 Test des repositories...")
        
        test_files = [
            "test_user_repository.py",
            "test_batch_repository.py", 
            "test_analysis_repository.py"
        ]
        
        results = {"passed": 0, "failed": 0, "details": []}
        
        for test_file in test_files:
            print(f"  → {test_file}")
            code, stdout, stderr = run_command(f"pytest tests/{test_file} -v")
            
            test_result = {
                "file": test_file,
                "success": code == 0,
                "output": stdout if code == 0 else stderr
            }
            
            results["details"].append(test_result)
            
            if code == 0:
                results["passed"] += 1
                print(f"    ✅ Passé")
            else:
                results["failed"] += 1
                print(f"    ❌ Échoué")
        
        return results
    
    @measure_time
    def run_model_tests(self) -> Dict[str, Any]:
        """Lance les tests modèles existants"""
        print("🔍 Test des modèles...")
        
        test_files = [
            "test_basic_models.py",
            "test_models_simple.py"
        ]
        
        results = {"passed": 0, "failed": 0, "details": []}
        
        for test_file in test_files:
            print(f"  → {test_file}")
            code, stdout, stderr = run_command(f"pytest tests/{test_file} -v")
            
            test_result = {
                "file": test_file,
                "success": code == 0,
                "output": stdout if code == 0 else stderr
            }
            
            results["details"].append(test_result)
            
            if code == 0:
                results["passed"] += 1
                print(f"    ✅ Passé")
            else:
                results["failed"] += 1
                print(f"    ❌ Échoué")
        
        return results
    
    @measure_time 
    def run_performance_tests(self) -> Dict[str, Any]:
        """Lance quelques tests performance existants"""
        print("🔍 Test de performance...")
        
        test_files = [
            "test_base_repository_performance.py"
        ]
        
        results = {"passed": 0, "failed": 0, "details": []}
        
        for test_file in test_files:
            print(f"  → {test_file}")
            code, stdout, stderr = run_command(f"pytest tests/{test_file} -v")
            
            test_result = {
                "file": test_file,
                "success": code == 0,
                "output": stdout if code == 0 else stderr
            }
            
            results["details"].append(test_result)
            
            if code == 0:
                results["passed"] += 1
                print(f"    ✅ Passé")
            else:
                results["failed"] += 1
                print(f"    ❌ Échoué")
        
        return results
    
    def run_audit(self) -> Dict[str, Any]:
        """Lance l'audit complet"""
        print("🚀 Démarrage Audit Simple ArbitrageVault")
        print("=" * 50)
        
        start_time = time.time()
        
        # Tests repository
        repo_results, repo_duration = self.run_repository_tests()
        self.results["tests"].append({
            "category": "repository",
            "duration": repo_duration,
            "results": repo_results
        })
        
        # Tests modèles
        model_results, model_duration = self.run_model_tests()
        self.results["tests"].append({
            "category": "models", 
            "duration": model_duration,
            "results": model_results
        })
        
        # Tests performance
        perf_results, perf_duration = self.run_performance_tests()
        self.results["tests"].append({
            "category": "performance",
            "duration": perf_duration, 
            "results": perf_results
        })
        
        # Résumé
        total_duration = time.time() - start_time
        total_passed = repo_results["passed"] + model_results["passed"] + perf_results["passed"]
        total_failed = repo_results["failed"] + model_results["failed"] + perf_results["failed"]
        total_tests = total_passed + total_failed
        
        self.results["summary"] = {
            "total_tests": total_tests,
            "passed": total_passed,
            "failed": total_failed,
            "duration_seconds": round(total_duration, 2)
        }
        
        # Ajouter les métriques
        self.add_basic_metrics()
        
        return self.results
    
    def print_summary(self):
        """Affiche le résumé de l'audit"""
        print("\n" + "=" * 50)
        print("📊 RÉSUMÉ AUDIT")
        print("=" * 50)
        
        summary = self.results["summary"]
        print(f"Tests totaux: {summary['total_tests']}")
        print(f"✅ Passés: {summary['passed']}")
        print(f"❌ Échoués: {summary['failed']}")
        print(f"⏱️ Durée: {summary['duration_seconds']}s")
        
        success_rate = (summary['passed'] / summary['total_tests'] * 100) if summary['total_tests'] > 0 else 0
        print(f"📈 Taux succès: {success_rate:.1f}%")
        
        # Détail par catégorie
        print(f"\n📋 DÉTAIL PAR CATÉGORIE:")
        for test_category in self.results["tests"]:
            cat_name = test_category["category"]
            cat_results = test_category["results"]
            cat_duration = test_category["duration"]
            cat_rate = (cat_results["passed"] / (cat_results["passed"] + cat_results["failed"]) * 100) if (cat_results["passed"] + cat_results["failed"]) > 0 else 0
            print(f"  {cat_name.upper()}: {cat_results['passed']}/{cat_results['passed'] + cat_results['failed']} ({cat_rate:.0f}%) - {cat_duration:.1f}s")
        
        if summary['failed'] == 0:
            print("\n🎉 Audit RÉUSSI - Tous les tests passent !")
        else:
            print(f"\n⚠️ Audit PARTIEL - {summary['failed']} test(s) échoué(s)")
            print("Voir audit_report.json pour les détails des erreurs")
    
    def save_report(self, filename: str = "audit_report.json"):
        """Sauvegarde le rapport détaillé"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"📄 Rapport sauvegardé: {filename}")
    
    def add_basic_metrics(self):
        """Ajoute quelques métriques simples au rapport"""
        passed_files = [d["file"] for test in self.results["tests"] for d in test["results"]["details"] if d["success"]]
        
        metrics = {
            "system_health": {
                "core_repositories": "test_analysis_repository.py" in passed_files,
                "core_models": "test_models_simple.py" in passed_files,
                "performance_baseline": "test_base_repository_performance.py" in passed_files
            },
            "readiness_indicators": {
                "ready_for_keepa_integration": self.results["summary"]["failed"] <= 2 and self.results["summary"]["passed"] >= 3
            },
            "passed_test_files": passed_files
        }
        self.results["metrics"] = metrics

def main():
    """Point d'entrée principal"""
    audit = SimpleAudit()
    
    try:
        audit.run_audit()
        audit.print_summary()
        audit.save_report()
        
        # Code de sortie basé sur les résultats
        if audit.results["summary"]["failed"] == 0:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Audit interrompu par l'utilisateur")
        sys.exit(2)
    except Exception as e:
        print(f"💥 Erreur durant l'audit: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()