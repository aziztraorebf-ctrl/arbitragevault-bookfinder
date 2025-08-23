#!/usr/bin/env python3
"""
Script d'optimisation simplifié qui utilise directement les fonctions backend
sans serveur HTTP. Approche plus directe et fiable.
"""
import os
import sys
import json
import asyncio
import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Dict, Any
from datetime import datetime

# Ajouter le backend au path
backend_path = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, os.path.abspath(backend_path))

# Imports des modules backend
try:
    from app.core.settings import get_settings
    from app.services.keepa_service import KeepaService
    from app.services.business_config_service import BusinessConfigService
    from app.api.v1.routers.keepa import analyze_product
    print("✅ Imports backend réussis")
except Exception as e:
    print(f"❌ Erreur imports backend: {e}")
    sys.exit(1)

# Configuration
ASIN_INPUT_FILE = "scripts/input_asins.json"
REPORT_DIR = "reports/scoring_opt"

GRID_SEARCH_PARAMS = {
    "roi_min": [25, 30, 35],
    "velocity_min": [50, 60, 70, 80], 
    "stability_min": [50, 60, 70, 80],
    "confidence_min": [60, 70, 80]
}

def ensure_directories():
    """Crée les répertoires nécessaires."""
    os.makedirs(REPORT_DIR, exist_ok=True)

def compute_overall_rating_with_thresholds(item: Dict, thresholds: Dict[str, float]) -> str:
    """Recalcule le rating avec de nouveaux seuils."""
    roi = item.get('roi_percentage', 0)
    velocity = item.get('velocity_score', 0)
    stability = item.get('stability_score', 0)
    confidence = item.get('confidence_score', 0)
    
    # EXCELLENT: tous les seuils respectés
    if (roi >= thresholds.get('roi_min', 35) and
        velocity >= thresholds.get('velocity_min', 70) and
        stability >= thresholds.get('stability_min', 70) and
        confidence >= thresholds.get('confidence_min', 70)):
        return "EXCELLENT"
    
    # GOOD: seuils relaxés
    elif (roi >= thresholds.get('roi_min', 25) and
          velocity >= thresholds.get('velocity_min', 60) and
          stability >= thresholds.get('stability_min', 60) and
          confidence >= thresholds.get('confidence_min', 60)):
        return "GOOD"
    
    # FAIR: ROI minimum
    elif roi >= max(20, thresholds.get('roi_min', 20) * 0.7):
        return "FAIR"
    else:
        return "PASS"

async def fetch_product_metrics(asin: str, keepa_service: KeepaService) -> Dict[str, Any]:
    """Récupère les métriques d'un produit via KeepaService."""
    try:
        print(f"  Fetching {asin}...")
        
        # Utiliser la fonction analyze_product directement
        result = await analyze_product(asin)
        
        if result and hasattr(result, 'dict'):
            data = result.dict()
            print(f"  ✅ {asin}: {data.get('overall_rating', 'N/A')} (ROI: {data.get('roi_percentage', 0):.1f}%)")
            return data
        else:
            print(f"  ❌ {asin}: Pas de données")
            return None
            
    except Exception as e:
        print(f"  ❌ {asin}: Erreur - {e}")
        return None

async def fetch_all_metrics(asins: List[str]) -> List[Dict[str, Any]]:
    """Récupère les métriques pour tous les ASINs."""
    print(f"📊 Récupération des métriques pour {len(asins)} ASINs...")
    
    results = []
    
    # Initialiser les services
    settings = get_settings()
    keepa_service = KeepaService(api_key=settings.keepa_api_key)
    
    async with keepa_service:
        for i, asin in enumerate(asins):
            print(f"[{i+1}/{len(asins)}]", end=" ")
            
            data = await fetch_product_metrics(asin, keepa_service)
            if data:
                data['asin'] = asin
                results.append(data)
            
            # Petit délai pour respecter les limites API
            await asyncio.sleep(0.5)
    
    print(f"✅ {len(results)} produits récupérés avec succès")
    return results

def run_grid_search(data: List[Dict], grid_params: Dict) -> pd.DataFrame:
    """Exécute la recherche par grille."""
    print("🔧 Optimisation par grille de recherche...")
    
    results = []
    combo_count = 0
    total = len(grid_params['roi_min']) * len(grid_params['velocity_min']) * len(grid_params['stability_min']) * len(grid_params['confidence_min'])
    
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
                    
                    # Recalcule les ratings
                    ratings = [compute_overall_rating_with_thresholds(item, thresholds) for item in data]
                    counts = {r: ratings.count(r) for r in ['EXCELLENT', 'GOOD', 'FAIR', 'PASS']}
                    
                    # Métriques business
                    total_items = len(ratings)
                    excellent_items = [item for item, rating in zip(data, ratings) if rating == 'EXCELLENT']
                    good_plus_items = [item for item, rating in zip(data, ratings) if rating in ['EXCELLENT', 'GOOD']]
                    
                    excellent_pct = (counts['EXCELLENT'] / total_items) * 100
                    good_plus_pct = ((counts['EXCELLENT'] + counts['GOOD']) / total_items) * 100
                    
                    # ROI stats
                    excellent_rois = [item['roi_percentage'] for item in excellent_items] if excellent_items else [0]
                    good_plus_rois = [item['roi_percentage'] for item in good_plus_items] if good_plus_items else [0]
                    
                    results.append({
                        'roi_min': roi_min,
                        'velocity_min': velocity_min,
                        'stability_min': stability_min,
                        'confidence_min': confidence_min,
                        'excellent_count': counts['EXCELLENT'],
                        'excellent_pct': excellent_pct,
                        'good_plus_count': counts['EXCELLENT'] + counts['GOOD'],
                        'good_plus_pct': good_plus_pct,
                        'excellent_median_roi': pd.Series(excellent_rois).median(),
                        'good_plus_median_roi': pd.Series(good_plus_rois).median(),
                    })
                    
                    if combo_count % 20 == 0:
                        print(f"  Progression: {combo_count}/{total}")
    
    return pd.DataFrame(results)

def generate_reports(data: List[Dict], grid_results: pd.DataFrame):
    """Génère les rapports."""
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
    
    # 2. Export CSV
    pd.DataFrame(data).to_csv(os.path.join(REPORT_DIR, 'detailed_analysis.csv'), index=False)
    
    # 3. Résultats grid search
    grid_sorted = grid_results.sort_values('excellent_median_roi', ascending=False)
    grid_sorted.to_csv(os.path.join(REPORT_DIR, 'grid_search_results.csv'), index=False)
    
    # 4. Top recommandations
    print("\n🏆 TOP 10 CONFIGURATIONS OPTIMALES:")
    print("=" * 80)
    
    top = grid_sorted.head(10)
    for i, (_, row) in enumerate(top.iterrows(), 1):
        print(f"{i:2d}. ROI≥{row['roi_min']}%, Vel≥{row['velocity_min']}, Stab≥{row['stability_min']}, Conf≥{row['confidence_min']} "
              f"→ EXCELLENT: {row['excellent_count']} ({row['excellent_pct']:.1f}%), ROI médian: {row['excellent_median_roi']:.1f}%")
    
    print(f"\n📁 Rapports: {os.path.abspath(REPORT_DIR)}")
    
    return top.iloc[0] if len(top) > 0 else None

async def main():
    """Fonction principale."""
    print("🎯 ArbitrageVault - Optimisation Directe v1.5.0")
    print("=" * 60)
    
    ensure_directories()
    
    try:
        # 1. Charger les ASINs
        print("\n📋 Chargement des ASINs...")
        script_dir = os.path.dirname(__file__)
        asin_file = os.path.join(script_dir, "..", ASIN_INPUT_FILE)
        
        with open(asin_file, 'r') as f:
            asin_data = json.load(f)
        
        all_asins = []
        test_data = asin_data.get('test_asins', asin_data)
        for category, asins in test_data.items():
            all_asins.extend(asins)
            print(f"  - {category}: {len(asins)} ASINs")
        
        print(f"Total: {len(all_asins)} ASINs")
        
        # 2. Récupérer les données
        analysis_data = await fetch_all_metrics(all_asins)
        
        if not analysis_data:
            print("❌ Aucune donnée récupérée")
            return
        
        # 3. Optimisation
        grid_results = run_grid_search(analysis_data, GRID_SEARCH_PARAMS)
        
        # 4. Rapports
        best_config = generate_reports(analysis_data, grid_results)
        
        # 5. Recommandation finale
        if best_config is not None:
            print(f"\n💡 RECOMMANDATION BUSINESS_RULES.JSON:")
            print(f"  \"roi_min\": {best_config['roi_min']},")
            print(f"  \"velocity_min\": {best_config['velocity_min']},")
            print(f"  \"stability_min\": {best_config['stability_min']},")
            print(f"  \"confidence_min\": {best_config['confidence_min']}")
        
        print("\n✅ Optimisation terminée!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())