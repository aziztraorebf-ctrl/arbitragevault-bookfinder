"""
Investigation Keepa - Test Prix Obsolètes
==========================================
Objectif : Déterminer si le problème vient du cache Keepa ou du parser

Test 3 ASINs :
1. 0593655036 - The Anxious Generation (prix problème : $0.16/$0.30)
2. 1506295266 - Deuxième livre test
3. B0BSHF7WHW - Echo Dot (témoin stable Amazon)
"""

import os
import sys
import json
import requests
from datetime import datetime
from typing import Dict, Any

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

KEEPA_API_KEY = os.getenv("KEEPA_API_KEY")
KEEPA_BASE_URL = "https://api.keepa.com"

# ASINs à tester
TEST_ASINS = {
    "0593655036": "The Anxious Generation (problème connu)",
    "1506295266": "Livre test 2",
    "B0BSHF7WHW": "Echo Dot (témoin stable)"
}


def call_keepa_raw(asin: str) -> Dict[str, Any]:
    """
    Appel brut à l'API Keepa SANS parser
    Retourne la réponse JSON complète
    """
    params = {
        "key": KEEPA_API_KEY,
        "domain": 1,  # Amazon.com
        "asin": asin,
        "stats": 90,  # Stats 90 jours
        "history": 1,  # Inclure historique prix
        # NOTE: update=0 (default) = utilise cache Keepa
        # On teste D'ABORD avec cache pour voir si obsolète
    }

    print(f"\n{'='*80}")
    print(f"📡 Requête Keepa API")
    print(f"{'='*80}")
    print(f"URL: {KEEPA_BASE_URL}/product")
    print(f"Params: {json.dumps(params, indent=2)}")

    response = requests.get(f"{KEEPA_BASE_URL}/product", params=params, timeout=30)
    response.raise_for_status()

    return response.json()


def timestamp_to_date(keepa_time: int) -> str:
    """
    Convertit timestamp Keepa (minutes depuis epoch Keepa 21 Oct 2000)
    vers date lisible
    """
    if keepa_time == -1 or keepa_time is None:
        return "N/A"

    # Keepa epoch: 21 Oct 2000 00:00:00 GMT
    keepa_epoch = 971222400  # Unix timestamp pour 21 Oct 2000
    unix_timestamp = keepa_epoch + (keepa_time * 60)

    return datetime.fromtimestamp(unix_timestamp).strftime("%Y-%m-%d %H:%M:%S UTC")


def extract_price_fields(product: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrait les champs de prix critiques du JSON Keepa
    """
    data = product.get("data", {})
    stats = product.get("stats", {})

    # Prix actuels (dernier point de données)
    # Keepa stocke les prix en centimes (ex: 1699 = $16.99)
    current_prices = {
        "amazon": data.get("AMAZON"),           # Prix Amazon direct
        "new": data.get("NEW"),                 # Prix neuf (3rd party)
        "used": data.get("USED"),               # Prix usagé
        "sales_rank": data.get("SALES"),        # Historique BSR
        "buy_box": data.get("BUY_BOX_SHIPPING"), # BuyBox price
        "new_fba": data.get("NEW_FBA"),         # FBA neuf
        "lightning_deal": data.get("LIGHTNING_DEAL"),
        "warehouse": data.get("WAREHOUSE"),
        "new_fbm": data.get("NEW_FBM"),         # FBM neuf (Fulfilled by Merchant)
        "collection": data.get("COLLECTIBLE"),
        "refurbished": data.get("REFURBISHED"),
        "bb_used": data.get("BUY_BOX_USED"),    # BuyBox occasion
    }

    # Extraire dernier prix de chaque array (si existe)
    last_prices = {}
    for key, value in current_prices.items():
        if value and isinstance(value, list) and len(value) >= 2:
            # Format: [timestamp_minutes, price, timestamp, price, ...]
            # On veut le DERNIER prix (index -1)
            last_prices[key] = value[-1] if value[-1] != -1 else None
        else:
            last_prices[key] = None

    # Stats agrégées (90 jours)
    stats_90d = stats.get("current", [None] * 20)  # 20 valeurs stats

    return {
        "raw_arrays": current_prices,
        "last_prices_centimes": last_prices,
        "last_prices_dollars": {k: v/100 if v else None for k, v in last_prices.items()},
        "stats_90d": {
            "avg_amazon": stats_90d[0] / 100 if stats_90d[0] and stats_90d[0] != -1 else None,
            "avg_new": stats_90d[2] / 100 if stats_90d[2] and stats_90d[2] != -1 else None,
            "avg_used": stats_90d[6] / 100 if stats_90d[6] and stats_90d[6] != -1 else None,
        }
    }


def analyze_asin(asin: str, description: str):
    """
    Analyse complète d'un ASIN
    """
    print(f"\n{'#'*80}")
    print(f"# ASIN: {asin} - {description}")
    print(f"{'#'*80}\n")

    try:
        # 1. Appel Keepa brut
        raw_response = call_keepa_raw(asin)

        # 2. Vérifier si produit trouvé
        if "products" not in raw_response or not raw_response["products"]:
            print("❌ Aucun produit trouvé dans la réponse Keepa")
            return

        product = raw_response["products"][0]

        # 3. Informations générales
        print(f"\n📦 Informations Produit")
        print(f"{'─'*80}")
        print(f"Title: {product.get('title', 'N/A')[:80]}...")
        print(f"ASIN: {product.get('asin', 'N/A')}")
        print(f"Brand: {product.get('brand', 'N/A')}")
        print(f"Category: {product.get('categoryTree', [{}])[0].get('name', 'N/A')}")
        print(f"Amazon on Listing: {product.get('isAmazonOnListing', False)}")
        print(f"Buybox Winner: {product.get('buyBoxWinner', 'N/A')}")

        # 4. Timestamps et fraîcheur données
        last_update = product.get("lastUpdate", -1)
        last_price_change = product.get("lastPriceChange", -1)

        print(f"\n⏰ Fraîcheur des Données")
        print(f"{'─'*80}")
        print(f"Last Update Keepa: {timestamp_to_date(last_update)}")
        print(f"Last Price Change: {timestamp_to_date(last_price_change)}")

        if last_update != -1:
            # Calculer âge données
            keepa_epoch = 971222400
            unix_last_update = keepa_epoch + (last_update * 60)
            age_days = (datetime.now().timestamp() - unix_last_update) / 86400

            print(f"Âge données: {age_days:.1f} jours")

            if age_days > 7:
                print(f"⚠️  ATTENTION: Données obsolètes (> 7 jours)")
            elif age_days > 1:
                print(f"⚡ Données un peu vieilles (> 1 jour)")
            else:
                print(f"✅ Données fraîches (< 1 jour)")

        # 5. Extraction prix
        price_data = extract_price_fields(product)

        print(f"\n💰 Prix Extraits (dernière valeur de chaque array)")
        print(f"{'─'*80}")

        prices_display = price_data["last_prices_dollars"]

        print(f"Amazon Direct:     ${prices_display['amazon']:.2f}" if prices_display['amazon'] else "Amazon Direct:     N/A")
        print(f"New (3rd Party):   ${prices_display['new']:.2f}" if prices_display['new'] else "New (3rd Party):   N/A")
        print(f"New FBA:           ${prices_display['new_fba']:.2f}" if prices_display['new_fba'] else "New FBA:           N/A")
        print(f"New FBM:           ${prices_display['new_fbm']:.2f}" if prices_display['new_fbm'] else "New FBM:           N/A")
        print(f"Used:              ${prices_display['used']:.2f}" if prices_display['used'] else "Used:              N/A")
        print(f"BuyBox New:        ${prices_display['buy_box']:.2f}" if prices_display['buy_box'] else "BuyBox New:        N/A")
        print(f"BuyBox Used:       ${prices_display['bb_used']:.2f}" if prices_display['bb_used'] else "BuyBox Used:       N/A")

        print(f"\n📊 Stats Moyennes (90 jours)")
        print(f"{'─'*80}")
        stats = price_data["stats_90d"]
        print(f"Avg Amazon:  ${stats['avg_amazon']:.2f}" if stats['avg_amazon'] else "Avg Amazon:  N/A")
        print(f"Avg New:     ${stats['avg_new']:.2f}" if stats['avg_new'] else "Avg New:     N/A")
        print(f"Avg Used:    ${stats['avg_used']:.2f}" if stats['avg_used'] else "Avg Used:    N/A")

        # 6. Détection problème
        print(f"\n🔍 Diagnostic")
        print(f"{'─'*80}")

        # Vérifier si prix suspects (< $1)
        suspicious_prices = []
        for key, val in prices_display.items():
            if val and val < 1.0:
                suspicious_prices.append(f"{key}: ${val:.2f}")

        if suspicious_prices:
            print(f"⚠️  PRIX SUSPECTS DÉTECTÉS (< $1):")
            for sp in suspicious_prices:
                print(f"   - {sp}")
            print(f"\n💡 Hypothèse: Cache Keepa obsolète OU mauvaise extraction array")
        else:
            print(f"✅ Aucun prix suspect détecté")

        # 7. Afficher premiers/derniers points array pour debug
        print(f"\n🔬 Debug Arrays (premiers 4 et derniers 4 points)")
        print(f"{'─'*80}")

        for key, array in price_data["raw_arrays"].items():
            if array and isinstance(array, list):
                # Extraire timestamps et prix
                points = []
                for i in range(0, min(len(array), 8), 2):  # 4 premiers points
                    if i+1 < len(array):
                        timestamp = array[i]
                        price = array[i+1]
                        date = timestamp_to_date(timestamp)
                        price_str = f"${price/100:.2f}" if price != -1 else "N/A"
                        points.append(f"{date}: {price_str}")

                # Derniers points
                last_points = []
                start_idx = max(0, len(array) - 8)
                for i in range(start_idx, len(array), 2):
                    if i+1 < len(array):
                        timestamp = array[i]
                        price = array[i+1]
                        date = timestamp_to_date(timestamp)
                        price_str = f"${price/100:.2f}" if price != -1 else "N/A"
                        last_points.append(f"{date}: {price_str}")

                if points or last_points:
                    print(f"\n{key}:")
                    if points:
                        print(f"  Premiers: {' | '.join(points[:2])}")
                    if last_points:
                        print(f"  Derniers: {' | '.join(last_points[-2:])}")

        # 8. Sauvegarder JSON brut pour inspection manuelle
        output_file = f"keepa_raw_{asin}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(raw_response, f, indent=2, ensure_ascii=False)

        print(f"\n💾 JSON brut sauvegardé: {output_file}")

    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """
    Analyse les 3 ASINs de test
    """
    print(f"\n{'='*80}")
    print(f"INVESTIGATION KEEPA - PRIX OBSOLETES")
    print(f"{'='*80}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Keepa API Key: {KEEPA_API_KEY[:20]}..." if KEEPA_API_KEY else "ERREUR: KEEPA_API_KEY manquante")

    if not KEEPA_API_KEY:
        print("\nERREUR: KEEPA_API_KEY non definie dans .env")
        return

    # Analyser chaque ASIN
    for asin, description in TEST_ASINS.items():
        analyze_asin(asin, description)
        print("\n" + "="*80 + "\n")

    print(f"\n{'='*80}")
    print(f"Investigation terminee")
    print(f"{'='*80}")
    print(f"\nProchaines etapes:")
    print(f"1. Verifier les JSON bruts sauvegardes (keepa_raw_*.json)")
    print(f"2. Comparer prix extraits vs prix reels Amazon")
    print(f"3. Analyser keepa_parser_v2.py pour voir quelles cles sont utilisees")


if __name__ == "__main__":
    main()
