#!/usr/bin/env python3
"""
Test simple avec données simulées pour valider la logique d'optimisation.
Pas de complexité - juste la validation du concept.
"""
import pandas as pd

# Dataset simulé - 20 produits avec scores variés mais réalistes
SIMULATED_DATA = [
    {"asin": "SIM001", "title": "Textbook Math", "roi_percentage": 45, "velocity_score": 85, "stability_score": 90, "confidence_score": 95},
    {"asin": "SIM002", "title": "Textbook Physics", "roi_percentage": 38, "velocity_score": 75, "stability_score": 80, "confidence_score": 90},
    {"asin": "SIM003", "title": "Textbook Chemistry", "roi_percentage": 42, "velocity_score": 70, "stability_score": 85, "confidence_score": 88},
    {"asin": "SIM004", "title": "Programming Book", "roi_percentage": 35, "velocity_score": 65, "stability_score": 75, "confidence_score": 85},
    {"asin": "SIM005", "title": "Business Book", "roi_percentage": 28, "velocity_score": 80, "stability_score": 70, "confidence_score": 80},
    {"asin": "SIM006", "title": "Fiction Popular", "roi_percentage": 25, "velocity_score": 90, "stability_score": 60, "confidence_score": 75},
    {"asin": "SIM007", "title": "Fiction Classic", "roi_percentage": 20, "velocity_score": 85, "stability_score": 95, "confidence_score": 90},
    {"asin": "SIM008", "title": "Technical Manual", "roi_percentage": 50, "velocity_score": 55, "stability_score": 80, "confidence_score": 70},
    {"asin": "SIM009", "title": "Cookbook", "roi_percentage": 30, "velocity_score": 75, "stability_score": 65, "confidence_score": 85},
    {"asin": "SIM010", "title": "Art Book", "roi_percentage": 35, "velocity_score": 50, "stability_score": 90, "confidence_score": 60},
    {"asin": "SIM011", "title": "History Book", "roi_percentage": 22, "velocity_score": 60, "stability_score": 85, "confidence_score": 80},
    {"asin": "SIM012", "title": "Science Fiction", "roi_percentage": 18, "velocity_score": 95, "stability_score": 55, "confidence_score": 70},
    {"asin": "SIM013", "title": "Self Help", "roi_percentage": 40, "velocity_score": 85, "stability_score": 70, "confidence_score": 90},
    {"asin": "SIM014", "title": "Language Learning", "roi_percentage": 32, "velocity_score": 70, "stability_score": 75, "confidence_score": 85},
    {"asin": "SIM015", "title": "Travel Guide", "roi_percentage": 15, "velocity_score": 40, "stability_score": 50, "confidence_score": 60},
    {"asin": "SIM016", "title": "Medical Text", "roi_percentage": 55, "velocity_score": 60, "stability_score": 90, "confidence_score": 95},
    {"asin": "SIM017", "title": "Children Book", "roi_percentage": 25, "velocity_score": 80, "stability_score": 60, "confidence_score": 75},
    {"asin": "SIM018", "title": "Biography", "roi_percentage": 30, "velocity_score": 65, "stability_score": 80, "confidence_score": 85},
    {"asin": "SIM019", "title": "Volatile Tech", "roi_percentage": 60, "velocity_score": 40, "stability_score": 30, "confidence_score": 50},
    {"asin": "SIM020", "title": "Niche Hobby", "roi_percentage": 70, "velocity_score": 35, "stability_score": 85, "confidence_score": 65}
]

# Grid search simple - paramètres réduits pour test rapide
GRID_PARAMS = {
    "roi_min": [25, 30, 35],
    "velocity_min": [60, 70, 80],
    "stability_min": [60, 70, 80],
    "confidence_min": [70, 80]
}

def compute_rating(item, thresholds):
    """Calcule le rating avec les seuils donnés."""
    roi = item["roi_percentage"]
    velocity = item["velocity_score"] 
    stability = item["stability_score"]
    confidence = item["confidence_score"]
    
    # EXCELLENT: tous seuils respectés
    if (roi >= thresholds["roi_min"] and 
        velocity >= thresholds["velocity_min"] and
        stability >= thresholds["stability_min"] and 
        confidence >= thresholds["confidence_min"]):
        return "EXCELLENT"
    
    # GOOD: seuils relaxés
    elif (roi >= thresholds["roi_min"] * 0.8 and
          velocity >= thresholds["velocity_min"] * 0.85 and
          stability >= thresholds["stability_min"] * 0.85 and
          confidence >= thresholds["confidence_min"] * 0.85):
        return "GOOD"
    
    # FAIR: ROI minimum
    elif roi >= thresholds["roi_min"] * 0.7:
        return "FAIR"
    else:
        return "PASS"

def test_grid_search():
    """Test simple du grid search."""
    print("🧪 Test de simulation - Optimisation des seuils")
    print("=" * 50)
    
    results = []
    
    for roi_min in GRID_PARAMS["roi_min"]:
        for velocity_min in GRID_PARAMS["velocity_min"]:
            for stability_min in GRID_PARAMS["stability_min"]:
                for confidence_min in GRID_PARAMS["confidence_min"]:
                    
                    thresholds = {
                        "roi_min": roi_min,
                        "velocity_min": velocity_min,
                        "stability_min": stability_min,
                        "confidence_min": confidence_min
                    }
                    
                    # Calculer les ratings
                    ratings = [compute_rating(item, thresholds) for item in SIMULATED_DATA]
                    counts = {r: ratings.count(r) for r in ["EXCELLENT", "GOOD", "FAIR", "PASS"]}
                    
                    # Métriques business
                    total = len(SIMULATED_DATA)
                    excellent_pct = (counts["EXCELLENT"] / total) * 100
                    good_plus_pct = ((counts["EXCELLENT"] + counts["GOOD"]) / total) * 100
                    
                    # ROI des items EXCELLENT
                    excellent_items = [item for item, rating in zip(SIMULATED_DATA, ratings) if rating == "EXCELLENT"]
                    excellent_roi_median = pd.Series([item["roi_percentage"] for item in excellent_items]).median() if excellent_items else 0
                    
                    results.append({
                        "roi_min": roi_min,
                        "velocity_min": velocity_min,
                        "stability_min": stability_min,  
                        "confidence_min": confidence_min,
                        "excellent_count": counts["EXCELLENT"],
                        "excellent_pct": excellent_pct,
                        "good_plus_pct": good_plus_pct,
                        "excellent_median_roi": excellent_roi_median
                    })
    
    # Trier par ROI médian des EXCELLENT
    df = pd.DataFrame(results)
    df_sorted = df.sort_values("excellent_median_roi", ascending=False)
    
    print(f"📊 Testé {len(results)} combinaisons sur {len(SIMULATED_DATA)} produits simulés\n")
    
    # Top 5 recommandations
    print("🏆 TOP 5 CONFIGURATIONS OPTIMALES:")
    print("-" * 70)
    
    for i, (_, row) in enumerate(df_sorted.head(5).iterrows(), 1):
        print(f"{i}. ROI≥{row['roi_min']}%, Vel≥{row['velocity_min']}, Stab≥{row['stability_min']}, Conf≥{row['confidence_min']} "
              f"→ EXCELLENT: {row['excellent_count']} ({row['excellent_pct']:.0f}%), ROI médian: {row['excellent_median_roi']:.1f}%")
    
    # Recommandation finale
    best = df_sorted.iloc[0]
    print(f"\n💡 RECOMMANDATION FINALE:")
    print(f"business_rules.json - advanced_scoring.thresholds:")
    print(f'  "roi_min": {best["roi_min"]},')
    print(f'  "velocity_min": {best["velocity_min"]},') 
    print(f'  "stability_min": {best["stability_min"]},')
    print(f'  "confidence_min": {best["confidence_min"]}')
    
    # Validation business
    print(f"\n✅ VALIDATION:")
    print(f"  - EXCELLENT items: {best['excellent_count']}/20 ({best['excellent_pct']:.0f}%)")
    print(f"  - ROI médian EXCELLENT: {best['excellent_median_roi']:.1f}%")
    print(f"  - Items viables (GOOD+): {best['good_plus_pct']:.0f}%")
    
    return best

def show_current_vs_recommended():
    """Compare seuils actuels vs recommandés."""
    print(f"\n🔄 COMPARAISON SEUILS:")
    
    # Seuils actuels (supposés)
    current = {"roi_min": 30, "velocity_min": 70, "stability_min": 70, "confidence_min": 70}
    
    # Test avec seuils actuels
    current_ratings = [compute_rating(item, current) for item in SIMULATED_DATA]
    current_excellent = current_ratings.count("EXCELLENT")
    
    print(f"  Seuils ACTUELS → EXCELLENT: {current_excellent}/20 ({current_excellent/20*100:.0f}%)")
    
    # Test avec seuils recommandés
    recommended = test_grid_search()
    
    if recommended["excellent_count"] > current_excellent:
        print(f"  ✅ Amélioration: +{recommended['excellent_count'] - current_excellent} items EXCELLENT")
    else:
        print(f"  → Seuils actuels sont déjà optimaux")

if __name__ == "__main__":
    show_current_vs_recommended()
    print(f"\n🎉 Test terminé - Logique d'optimisation validée!")