import time
import subprocess
import sys

print("⏳ Attente du démarrage du serveur...")
time.sleep(5)  # Wait 5 seconds
print("🚀 Lancement du test d'intégration...")

# Run the integration test
result = subprocess.run([
    sys.executable, "test_autosourcing_integration.py"
], capture_output=True, text=True)

print(result.stdout)
if result.stderr:
    print("ERRORS:")
    print(result.stderr)
    
sys.exit(result.returncode)