#!/usr/bin/env python3
"""
Test rapide de l'intégration avec le backend existant.
"""
import requests
import time
import subprocess
import os
import signal
import sys

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "backend")
BACKEND_URL = "http://localhost:8000"

server_process = None

def start_server():
    """Démarre le serveur backend."""
    global server_process
    
    print("🚀 Démarrage du serveur backend...")
    os.chdir(BACKEND_DIR)
    
    # Windows command
    cmd = '.venv\\Scripts\\activate.bat && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000'
    server_process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Attendre le démarrage
    print("⏳ Attente du serveur...")
    for i in range(20):
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=2)
            if response.status_code == 200:
                print("✅ Serveur démarré!")
                return True
        except:
            time.sleep(1)
    
    print("❌ Échec du démarrage")
    return False

def stop_server():
    """Arrête le serveur."""
    global server_process
    if server_process:
        print("🛑 Arrêt du serveur...")
        server_process.terminate()
        server_process = None

def test_single_asin():
    """Test avec un ASIN."""
    test_asin = "0134093410"
    
    print(f"🧪 Test avec ASIN: {test_asin}")
    
    try:
        url = f"{BACKEND_URL}/api/v1/keepa/{test_asin}/metrics"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Succès!")
            print(f"  Titre: {data.get('title', 'N/A')[:50]}...")
            print(f"  ROI: {data.get('roi_percentage', 0):.1f}%")
            print(f"  Velocity: {data.get('velocity_score', 0):.1f}")
            print(f"  Stability: {data.get('stability_score', 0):.1f}") 
            print(f"  Confidence: {data.get('confidence_score', 0):.1f}")
            print(f"  Rating: {data.get('overall_rating', 'N/A')}")
            return True
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            print(f"Réponse: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def cleanup(sig, frame):
    """Nettoyage propre."""
    print("\n🔄 Nettoyage...")
    stop_server()
    sys.exit(0)

def main():
    print("🧪 Test d'intégration Backend")
    print("=" * 40)
    
    signal.signal(signal.SIGINT, cleanup)
    
    try:
        if start_server():
            success = test_single_asin()
            if success:
                print("\n✅ Test réussi! Le script d'optimisation peut fonctionner.")
            else:
                print("\n❌ Test échoué. Vérifier la configuration backend.")
        else:
            print("❌ Impossible de démarrer le serveur")
    
    finally:
        stop_server()

if __name__ == "__main__":
    main()