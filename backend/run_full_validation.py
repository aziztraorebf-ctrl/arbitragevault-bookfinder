"""
Script principal de validation complète du backend
Lance tous les tests end-to-end, performance et sécurité
"""
import asyncio
import subprocess
import sys
import time
import httpx
from pathlib import Path

BASE_URL = "http://localhost:8000"
BACKEND_DIR = Path(__file__).parent

class BackendValidator:
    """Coordinateur de validation complète du backend"""
    
    def __init__(self):
        self.server_process = None
        self.server_started = False
    
    async def check_server_running(self) -> bool:
        """Vérifie si le serveur FastAPI tourne déjà"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{BASE_URL}/health")
                return response.status_code == 200
        except:
            return False
    
    async def start_server_if_needed(self) -> bool:
        """Démarre le serveur FastAPI si nécessaire"""
        if await self.check_server_running():
            print("✅ Serveur FastAPI déjà en fonctionnement")
            return True
        
        print("🚀 Démarrage du serveur FastAPI...")
        
        # Commande pour démarrer le serveur
        cmd = [
            str(BACKEND_DIR / ".venv" / "Scripts" / "python.exe"),
            "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ]
        
        try:
            self.server_process = subprocess.Popen(
                cmd,
                cwd=BACKEND_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
            )
            
            # Attendre que le serveur démarre
            for attempt in range(30):  # 30 secondes max
                await asyncio.sleep(1)
                if await self.check_server_running():
                    print("✅ Serveur FastAPI démarré avec succès")
                    self.server_started = True
                    return True
                print(f"⏳ Attente serveur... ({attempt + 1}/30)")
            
            print("❌ Échec démarrage serveur après 30s")
            return False
            
        except Exception as e:
            print(f"❌ Erreur démarrage serveur: {str(e)}")
            return False
    
    async def run_test_suite(self, test_file: str, suite_name: str) -> bool:
        """Lance une suite de tests spécifique"""
        print(f"\n📋 LANCEMENT {suite_name.upper()}")
        print("=" * 50)
        
        cmd = [
            str(BACKEND_DIR / ".venv" / "Scripts" / "python.exe"),
            "-m", "pytest",
            f"tests/e2e/{test_file}",
            "-v", "--tb=short"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=BACKEND_DIR,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes max par suite
            )
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            success = result.returncode == 0
            if success:
                print(f"✅ {suite_name} - RÉUSSI")
            else:
                print(f"❌ {suite_name} - ÉCHEC (code: {result.returncode})")
            
            return success
            
        except subprocess.TimeoutExpired:
            print(f"⏰ {suite_name} - TIMEOUT (5 min dépassées)")
            return False
        except Exception as e:
            print(f"❌ {suite_name} - ERREUR: {str(e)}")
            return False
    
    async def run_direct_tests(self):
        """Lance les tests directement (sans pytest)"""
        print(f"\n🧪 LANCEMENT TESTS DIRECTS")
        print("=" * 50)
        
        try:
            # Import et lancement direct des tests
            sys.path.append(str(BACKEND_DIR))
            
            # Test corrections backend
            from tests.e2e.test_backend_corrections import test_complete_workflow as test_corrections
            print("🔧 Tests corrections backend...")
            await test_corrections()
            
            # Test performance
            from tests.e2e.test_performance_load import test_complete_performance_suite as test_perf
            print("\n⚡ Tests performance...")
            await test_perf()
            
            # Test sécurité  
            from tests.e2e.test_security_integration import test_complete_security_suite as test_security
            print("\n🔒 Tests sécurité...")
            await test_security()
            
            return True
            
        except Exception as e:
            print(f"❌ ERREUR TESTS DIRECTS: {str(e)}")
            return False
    
    def cleanup_server(self):
        """Nettoie le serveur si nous l'avons démarré"""
        if self.server_started and self.server_process:
            print("🛑 Arrêt du serveur FastAPI...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
    
    async def run_complete_validation(self):
        """Lance la validation complète"""
        print("🎯 DÉBUT VALIDATION COMPLÈTE BACKEND")
        print("=" * 60)
        
        start_time = time.time()
        results = {}
        
        try:
            # 1. Démarrer serveur
            if not await self.start_server_if_needed():
                print("❌ ÉCHEC: Impossible de démarrer le serveur")
                return False
            
            # 2. Attendre stabilisation
            await asyncio.sleep(3)
            
            # 3. Lancer tests directs (plus fiable)
            success = await self.run_direct_tests()
            
            if success:
                end_time = time.time()
                duration = end_time - start_time
                
                print("\n" + "=" * 60)
                print("🎉 VALIDATION COMPLÈTE RÉUSSIE!")
                print(f"⏱️ Durée totale: {duration:.1f} secondes")
                print("✅ Backend prêt pour développement frontend")
                print("✅ Performance validée sous charge")
                print("✅ Sécurité et intégrations confirmées")
                return True
            else:
                print("\n❌ VALIDATION ÉCHOUÉE")
                return False
                
        except KeyboardInterrupt:
            print("\n⚠️ Validation interrompue par l'utilisateur")
            return False
        except Exception as e:
            print(f"\n❌ ERREUR VALIDATION: {str(e)}")
            return False
        finally:
            self.cleanup_server()

async def main():
    """Point d'entrée principal"""
    validator = BackendValidator()
    success = await validator.run_complete_validation()
    
    if success:
        print("\n🚀 PROCHAINES ÉTAPES:")
        print("  1. Commit des corrections (Option 3)")
        print("  2. Implémentation nouvelles features (Option 1)")
        print("  3. Développement frontend")
        return 0
    else:
        print("\n🔧 ACTIONS REQUISES:")
        print("  1. Corriger les erreurs identifiées")  
        print("  2. Relancer la validation")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())