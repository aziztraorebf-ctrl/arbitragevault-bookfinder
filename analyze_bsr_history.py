#!/usr/bin/env python3
"""
Script pour analyser le BSR history d'un ASIN et valider la logique de calcul velocity.
"""
import requests
import json
from typing import List, Tuple

BASE_URL = "https://arbitragevault-backend-v2.onrender.com/api/v1"

def fetch_metrics(asin: str) -> dict:
    """Récupère les métriques complètes pour un ASIN."""
    url = f"{BASE_URL}/keepa/{asin}/metrics"
    params = {
        "config_profile": "default",
        "force_refresh": "false"
    }
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    return response.json()

def analyze_bsr_history(asin: str):
    """
    Analyse le BSR history pour comprendre le format et l'ordre des données.
    """
    print(f"\n{'='*70}")
    print(f"  ANALYSE BSR HISTORY - ASIN {asin}")
    print(f"{'='*70}\n")

    # Récupérer données
    data = fetch_metrics(asin)
    analysis = data.get("analysis", {})

    # Extraire score breakdown pour debug
    score_breakdown = analysis.get("score_breakdown", {})
    velocity_data = score_breakdown.get("velocity", {})

    print(f"[SCORES ACTUELS]")
    print(f"  Velocity Score: {velocity_data.get('score')}")
    print(f"  Velocity Raw: {velocity_data.get('raw')}")
    print(f"  Velocity Level: {velocity_data.get('level')}")
    print(f"  Notes: {velocity_data.get('notes')}\n")

    # Essayer d'extraire bsr_history de différentes sources possibles
    bsr_history = None

    # Tentative 1: Directement dans analysis
    if "bsr_history" in analysis:
        bsr_history = analysis["bsr_history"]
        print(f"[SOURCE] bsr_history trouvé dans analysis")

    # Tentative 2: Dans raw Keepa data (si disponible)
    elif "raw_keepa" in analysis:
        raw_keepa = analysis["raw_keepa"]
        csv = raw_keepa.get("csv", [])
        if len(csv) > 3 and csv[3]:
            bsr_csv = csv[3]
            print(f"[SOURCE] BSR extrait de raw_keepa.csv[3]")
            print(f"  Format CSV: [timestamp1, value1, timestamp2, value2, ...]")
            print(f"  Total éléments CSV: {len(bsr_csv)}")

            # Parser en tuples (timestamp, bsr)
            bsr_history = []
            for i in range(0, len(bsr_csv) - 1, 2):
                timestamp_minutes = bsr_csv[i]
                bsr_value = bsr_csv[i + 1]
                if bsr_value and bsr_value > 0:
                    bsr_history.append((timestamp_minutes, bsr_value))

            print(f"  BSR points valides parsés: {len(bsr_history)}\n")

    if not bsr_history:
        print(f"[ERREUR] Aucun bsr_history trouvé dans la réponse API!\n")
        print("Contenu de analysis.keys():")
        print(list(analysis.keys()))
        return

    # Analyser le format
    print(f"\n[FORMAT BSR HISTORY]")
    print(f"  Type: {type(bsr_history)}")
    print(f"  Total points: {len(bsr_history)}")

    if not bsr_history:
        print(f"  [VIDE] Pas de données BSR disponibles\n")
        return

    # Premier et dernier élément
    first_entry = bsr_history[0]
    last_entry = bsr_history[-1]

    print(f"\n  Premier élément: {first_entry}")
    print(f"    Type: {type(first_entry)}")
    if isinstance(first_entry, (list, tuple)) and len(first_entry) >= 2:
        print(f"    Timestamp: {first_entry[0]} (type: {type(first_entry[0])})")
        print(f"    BSR Value: {first_entry[1]} (type: {type(first_entry[1])})")

    print(f"\n  Dernier élément: {last_entry}")
    print(f"    Type: {type(last_entry)}")
    if isinstance(last_entry, (list, tuple)) and len(last_entry) >= 2:
        print(f"    Timestamp: {last_entry[0]} (type: {type(last_entry[0])})")
        print(f"    BSR Value: {last_entry[1]} (type: {type(last_entry[1])})")

    # Vérifier ordre chronologique
    print(f"\n[ORDRE CHRONOLOGIQUE]")
    timestamps = [entry[0] for entry in bsr_history if isinstance(entry, (list, tuple)) and len(entry) >= 2]

    if timestamps:
        is_ascending = all(timestamps[i] <= timestamps[i+1] for i in range(len(timestamps)-1))
        is_descending = all(timestamps[i] >= timestamps[i+1] for i in range(len(timestamps)-1))

        if is_ascending:
            print(f"  ✅ Ordre ASCENDANT (ancien → récent)")
        elif is_descending:
            print(f"  ⚠️  Ordre DESCENDANT (récent → ancien)")
        else:
            print(f"  ❌ Ordre NON TRIÉ (mixte)")

        print(f"  Premier timestamp: {timestamps[0]}")
        print(f"  Dernier timestamp: {timestamps[-1]}")

    # Analyser 7 premiers vs 7 derniers (logique actuelle du code)
    print(f"\n[ANALYSE VELOCITY - LOGIQUE ACTUELLE]")

    # Extraire valeurs BSR seulement
    bsr_values = [entry[1] for entry in bsr_history if isinstance(entry, (list, tuple)) and len(entry) >= 2]

    if len(bsr_values) >= 14:
        first_7_bsr = bsr_values[:7]
        last_7_bsr = bsr_values[-7:]

        import statistics
        older_avg = statistics.mean(first_7_bsr)
        recent_avg = statistics.mean(last_7_bsr)

        improvement = (older_avg - recent_avg) / older_avg if older_avg > 0 else 0
        velocity_raw = 0.5 + (improvement * 0.5)
        velocity_raw = max(0.0, min(1.0, velocity_raw))
        velocity_normalized = int(velocity_raw * 100)

        print(f"  7 PREMIERS BSR: {first_7_bsr}")
        print(f"  Moyenne 7 premiers (older_avg): {older_avg:.2f}")
        print(f"\n  7 DERNIERS BSR: {last_7_bsr}")
        print(f"  Moyenne 7 derniers (recent_avg): {recent_avg:.2f}")
        print(f"\n  Calcul improvement:")
        print(f"    (older_avg - recent_avg) / older_avg")
        print(f"    ({older_avg:.2f} - {recent_avg:.2f}) / {older_avg:.2f}")
        print(f"    = {improvement:.4f} ({improvement * 100:.2f}%)")
        print(f"\n  Velocity Raw: {velocity_raw:.4f}")
        print(f"  Velocity Normalized (0-100): {velocity_normalized}")

        # Déterminer si c'est cohérent
        if is_ascending:
            print(f"\n  [ANALYSE] Ordre ascendant = ancien → récent")
            print(f"    older_avg devrait être les ANCIENS BSR")
            print(f"    recent_avg devrait être les RÉCENTS BSR")
            print(f"    ✅ LOGIQUE CORRECTE si BSR amélioré (baissé) avec le temps")
        else:
            print(f"\n  [ANALYSE] Ordre non-ascendant")
            print(f"    ⚠️  POSSIBLE BUG: Besoin de trier avant calcul!")

    else:
        print(f"  [INSUFFISANT] Seulement {len(bsr_values)} BSR points (besoin >= 14)")

    print(f"\n{'='*70}\n")

if __name__ == "__main__":
    # Analyser Catcher in the Rye
    analyze_bsr_history("0316769487")
