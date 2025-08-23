#!/usr/bin/env python3
"""
Script d'optimisation pragmatique utilisant l'API backend existante.
Utilise les endpoints /api/v1/keepa/{asin}/metrics déjà fonctionnels.
"""
import asyncio
import json
import os
import time
import subprocess
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Any
from datetime import datetime
import signal
import sys

# ============================================================================
# CONFIGURATION
# ============================================================================

# Paths
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "backend")
ASIN_INPUT_FILE = "scripts/input_asins.json"
CACHE_DIR = "scripts/cache"
REPORT_DIR = "reports/scoring_opt"

# API Settings
BACKEND_URL = "http://localhost:8000"
REQUEST_DELAY = 0.5  # Délai entre requêtes pour ne pas surcharger

# Grid search parameters
GRID_SEARCH_PARAMS = {
    "roi_min": [25, 30, 35],
    "velocity_min": [50, 60, 70, 80],
    "stability_min": [50, 60, 70, 80], 
    "confidence_min": [60, 70, 80]
}

# Global variable pour le processus serveur
server_process = None

# ============================================================================
# SERVER MANAGEMENT
# ============================================================================

def start_backend_server():
    """Démarre le serveur backend en arrière-plan."""
    global server_process
    
    print("🚀 Démarrage du serveur backend...")
    
    # Change to backend directory
    os.chdir(BACKEND_DIR)
    
    # Activate virtual environment and start server
    if os.name == 'nt':  # Windows
        cmd = ['.venv\\Scripts\\activate.bat', '&&', 'python', '-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000']
        server_process = subprocess.Popen(
            ' '.join(cmd), 
            shell=True,
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
    else:  # Unix-like
        cmd = ['bash', '-c', 'source .venv/bin/activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000']
        server_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    
    # Wait for server to start
    print("⏳ Attente du démarrage du serveur...")
    max_attempts = 30
    for i in range(max_attempts):
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=2)
            if response.status_code == 200:
                print("✅ Serveur backend démarré avec succès!")
                return True
        except requests.exceptions.RequestException:
            time.sleep(1)
    
    print("❌ Échec du démarrage du serveur backend")
    return False

def stop_backend_server():
    """Arrête le serveur backend."""
    global server_process
    if server_process:
        print("🛑 Arrêt du serveur backend...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
        server_process = None

def signal_handler(sig, frame):
    """Gestionnaire de signal pour nettoyage propre."""
    print("\n🔄 Arrêt en cours...")
    stop_backend_server()
    sys.exit(0)

# ============================================================================
# DATA FETCHING
# ============================================================================

def fetch_asin_metrics(asin: str, retries: int = 3) -> Dict[str, Any]:
    """Récupère les métriques d'un ASIN via l'API backend."""
    
    for attempt in range(retries):
        try:
            url = f"{BACKEND_URL}/api/v1/keepa/{asin}/metrics"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ {asin}: {data.get('overall_rating', 'N/A')} (ROI: {data.get('roi_percentage', 0):.1f}%)")
                return data
            
            elif response.status_code == 404:
                print(f"  ❌ {asin}: Produit non trouvé")
                return None
                
            else:
                print(f"  ⚠️  {asin}: Erreur HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"  ⚠️  {asin}: Erreur réseau (tentative {attempt + 1}/{retries})")
            if attempt < retries - 1:
                time.sleep(2)
    
    return None

def fetch_all_asins(asins: List[str]) -> List[Dict[str, Any]]:
    """Récupère les métriques de tous les ASINs."""
    print(f"📊 Récupération des métriques pour {len(asins)} ASINs...")
    
    results = []
    
    for i, asin in enumerate(asins):
        print(f"[{i+1}/{len(asins)}] Traitement {asin}...")
        
        data = fetch_asin_metrics(asin)
        if data:
            data['asin'] = asin
            results.append(data)
        
        # Délai pour éviter de surcharger l'API
        time.sleep(REQUEST_DELAY)
    
    print(f"✅ {len(results)} produits récupérés avec succès")
    return results

# ============================================================================
# OPTIMIZATION LOGIC (Réutilise la logique du script précédent)
# ============================================================================

def compute_overall_rating_with_thresholds(scores: Dict[str, float], thresholds: Dict[str, float]) -> str:
    """Recalcule le rating avec de nouveaux seuils."""
    roi_score = scores.get('roi_percentage', 0)
    velocity_score = scores.get('velocity_score', 0)
    stability_score = scores.get('stability_score', 0)
    confidence_score = scores.get('confidence_score', 0)
    
    # EXCELLENT: tous les seuils respectés
    if (roi_score >= thresholds.get('roi_min', 35) and
        velocity_score >= thresholds.get('velocity_min', 70) and
        stability_score >= thresholds.get('stability_min', 70) and
        confidence_score >= thresholds.get('confidence_min', 70)):
        return "EXCELLENT"
    
    # GOOD: seuils relaxés  
    elif (roi_score >= thresholds.get('roi_min', 25) and
          velocity_score >= thresholds.get('velocity_min', 60) and
          stability_score >= thresholds.get('stability_min', 60) and
          confidence_score >= thresholds.get('confidence_min', 60)):
        return "GOOD"
    
    # FAIR: ROI minimum
    elif roi_score >= max(20, thresholds.get('roi_min', 20) * 0.7):
        return "FAIR"
    
    else:
        return "PASS"

def run_grid_search(data: List[Dict], grid_params: Dict) -> pd.DataFrame:
    """Exécute la recherche de grille sur les combinaisons de seuils."""
    print("🔧 Lancement de l'optimisation par grille...")
    
    results = []
    total_combinations = 1
    for values in grid_params.values():
        total_combinations *= len(values)
    
    combo_count = 0
    
    for roi_min in grid_params['roi_min']:
        for velocity_min in grid_params['velocity_min']:
            for stability_min in grid_params['stability_min']:
                for confidence_min in grid_params['confidence_min']:
                    combo_count += 1
                    
                    thresholds = {
                        'roi_min': roi_min,
                        'velocity_min': velocity_min, 
                        'stability_min': stability_min,
                        'confidence_min': confidence_min
                    }
                    
                    # Recalcule les ratings avec ces seuils
                    new_ratings = [compute_overall_rating_with_thresholds(item, thresholds) for item in data]
                    rating_counts = {rating: new_ratings.count(rating) for rating in ['EXCELLENT', 'GOOD', 'FAIR', 'PASS']}
                    
                    # Calcule les métriques
                    total_items = len(new_ratings)
                    excellent_items = [item for item, rating in zip(data, new_ratings) if rating == 'EXCELLENT']
                    good_plus_items = [item for item, rating in zip(data, new_ratings) if rating in ['EXCELLENT', 'GOOD']]
                    
                    excellent_pct = (rating_counts['EXCELLENT'] / total_items) * 100
                    good_plus_pct = ((rating_counts['EXCELLENT'] + rating_counts['GOOD']) / total_items) * 100
                    
                    # Stats ROI
                    excellent_rois = [item['roi_percentage'] for item in excellent_items] if excellent_items else [0]
                    good_plus_rois = [item['roi_percentage'] for item in good_plus_items] if good_plus_items else [0]
                    
                    results.append({
                        'roi_min': roi_min,
                        'velocity_min': velocity_min,
                        'stability_min': stability_min,
                        'confidence_min': confidence_min,
                        'excellent_count': rating_counts['EXCELLENT'],
                        'excellent_pct': excellent_pct,
                        'good_plus_count': rating_counts['EXCELLENT'] + rating_counts['GOOD'],
                        'good_plus_pct': good_plus_pct,
                        'excellent_median_roi': pd.Series(excellent_rois).median(),
                        'good_plus_median_roi': pd.Series(good_plus_rois).median(),
                        'total_items': total_items
                    })
                    
                    if combo_count % 20 == 0:
                        print(f"  Progression: {combo_count}/{total_combinations} combinaisons testées")
    
    return pd.DataFrame(results)

# ============================================================================
# REPORTING
# ============================================================================

def ensure_directories():
    """Crée les répertoires nécessaires."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)

def generate_reports(data: List[Dict], grid_results: pd.DataFrame):
    """Génère les rapports d'analyse."""
    print("📋 Génération des rapports...")
    
    # 1. Distribution des scores
    plt.figure(figsize=(15, 10))
    plt.style.use('dark_background')
    
    scores_df = pd.DataFrame([{
        'ROI %': item['roi_percentage'],
        'Velocity': item['velocity_score'],
        'Stability': item['stability_score'],  
        'Confidence': item['confidence_score']
    } for item in data])
    
    for i, col in enumerate(['ROI %', 'Velocity', 'Stability', 'Confidence']):
        plt.subplot(2, 2, i+1)
        plt.hist(scores_df[col], bins=15, alpha=0.7, color=['red', 'blue', 'green', 'orange'][i])
        plt.title(f'{col} Distribution')
        plt.xlabel(col)
        plt.ylabel('Fréquence')
        plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(REPORT_DIR, 'score_distributions.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. Export données détaillées
    detailed_df = pd.DataFrame(data)
    detailed_df.to_csv(os.path.join(REPORT_DIR, 'detailed_analysis.csv'), index=False)
    
    # 3. Résultats de la grille de recherche
    grid_results = grid_results.sort_values('excellent_median_roi', ascending=False)
    grid_results.to_csv(os.path.join(REPORT_DIR, 'grid_search_results.csv'), index=False)
    
    # 4. Top recommandations
    print("\n🏆 TOP 10 CONFIGURATIONS RECOMMANDÉES:")
    print("=" * 80)
    
    top_configs = grid_results.head(10)
    for i, (_, row) in enumerate(top_configs.iterrows(), 1):
        print(f"{i:2d}. ROI≥{row['roi_min']}%, Vel≥{row['velocity_min']}, Stab≥{row['stability_min']}, Conf≥{row['confidence_min']} "
              f"→ EXCELLENT: {row['excellent_count']} ({row['excellent_pct']:.1f}%), "
              f"ROI médian: {row['excellent_median_roi']:.1f}%")
    
    print(f"\n📁 Rapports sauvegardés dans: {os.path.abspath(REPORT_DIR)}")
    
    return top_configs.iloc[0] if len(top_configs) > 0 else None

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Fonction principale."""
    print("🎯 ArbitrageVault - Optimisation Backend v1.5.0")
    print("=" * 60)
    
    # Configuration du gestionnaire de signal
    signal.signal(signal.SIGINT, signal_handler)
    
    ensure_directories()
    
    try:
        # 1. Démarrage du serveur
        if not start_backend_server():
            print("❌ Impossible de démarrer le serveur backend")
            return
        
        # 2. Chargement des ASINs de test
        print("\n📋 Chargement des ASINs de test...")
        with open(ASIN_INPUT_FILE, 'r') as f:
            asin_data = json.load(f)
        
        all_asins = []
        test_data = asin_data.get('test_asins', asin_data)
        for category, asins in test_data.items():
            all_asins.extend(asins)
            print(f"  - {category}: {len(asins)} ASINs")
        
        print(f"Total: {len(all_asins)} ASINs à analyser")
        
        # 3. Récupération des données
        analysis_data = fetch_all_asins(all_asins)
        
        if not analysis_data:
            print("❌ Aucune donnée récupérée")
            return
        
        print(f"✅ {len(analysis_data)} produits analysés avec succès")
        
        # 4. Optimisation par grille
        print("\n🔧 Optimisation des seuils...")
        grid_results = run_grid_search(analysis_data, GRID_SEARCH_PARAMS)
        
        # 5. Génération des rapports
        print("\n📊 Génération des rapports...")
        best_config = generate_reports(analysis_data, grid_results)
        
        # 6. Recommandation finale
        if best_config is not None:
            print(f"\n💡 RECOMMANDATION FINALE:")
            print(f"Mettre à jour business_rules.json avec:")
            print(f"  roi_min: {best_config['roi_min']}")
            print(f"  velocity_min: {best_config['velocity_min']}")
            print(f"  stability_min: {best_config['stability_min']}")
            print(f"  confidence_min: {best_config['confidence_min']}")
        
        print("\n✅ Optimisation terminée avec succès!")
        
    except KeyboardInterrupt:
        print("\n🔄 Arrêt demandé par l'utilisateur")
    
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
    
    finally:
        stop_backend_server()
        print("🏁 Nettoyage terminé")

if __name__ == "__main__":
    main()