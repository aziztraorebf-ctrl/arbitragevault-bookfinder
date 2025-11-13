#!/usr/bin/env python3
"""
Analyse complète de la disponibilité des 30 ASINs
Pour comprendre pourquoi 63% n'ont pas de données
"""

import json
import requests
from datetime import datetime
from typing import Dict, List, Tuple

KEEPA_API_KEY = "rvd01p0nku3s8bsnbubeda6je1763vv5gc94jrng4eiakghlnv4bm3pmvd0sg7ru"

# Tous les 30 ASINs de test
TEST_ASINS = [
    # Textbooks (high value)
    "0134685997", "1260565955", "0134895436", "0134173279", "1265045631",

    # Business/Self-Help
    "0593655036", "0063340240", "0593579135", "0593723597",

    # Fiction/Literature
    "0593713842", "0593449274", "1668026031", "B0CW1SXHZL",

    # Technical Books
    "1492056200", "1098146891", "1718501129", "1718503261", "1593279280",

    # Health & Wellness
    "0063283956", "0593232097", "0593652916",

    # Children's Books
    "0063356562", "1534482849", "1665925760", "1665925779",

    # Others
    "B0BN84P9JK", "B0D5BY7JWM", "B0D4778Y2P", "B0995VKY1K", "9780060555665"
]


def analyze_asin_status(asin: str) -> Dict:
    """Analyse détaillée du statut d'un ASIN."""

    try:
        # Fetch avec tous les paramètres possibles
        params = {
            'key': KEEPA_API_KEY,
            'domain': 1,
            'asin': asin,
            'stats': 90,
            'history': 1,
            'offers': 50,
            'rating': 1,
            'buybox': 1
        }

        response = requests.get('https://api.keepa.com/product', params=params)
        data = response.json()

        if not data.get('products'):
            return {
                'asin': asin,
                'status': 'NO_DATA',
                'reason': 'No product found in Keepa'
            }

        product = data['products'][0]

        # Analyse détaillée
        result = {
            'asin': asin,
            'title': (product.get('title') or 'N/A')[:50],
            'tracking_since': product.get('trackingSince'),
            'last_update': product.get('lastUpdate'),
            'product_type': product.get('productType'),
            'status': 'UNKNOWN',
            'reason': '',
            'prices': {},
            'offers': 0,
            'has_history': False,
            'is_active': False
        }

        # Check stats.current for prices
        stats = product.get('stats', {})
        current = stats.get('current', [])

        # Prix indices selon documentation Keepa
        price_found = False
        if current and len(current) > 18:
            # Index 0: Amazon
            if current[0] and current[0] != -1:
                result['prices']['amazon'] = current[0] / 100.0
                price_found = True

            # Index 1: NEW
            if current[1] and current[1] != -1:
                result['prices']['new'] = current[1] / 100.0
                price_found = True

            # Index 7: NEW_FBA_LOWEST
            if len(current) > 7 and current[7] and current[7] != -1:
                result['prices']['fba'] = current[7] / 100.0
                price_found = True

            # Index 18: BUY_BOX
            if len(current) > 18 and current[18] and current[18] != -1:
                result['prices']['buy_box'] = current[18] / 100.0
                price_found = True

        # Check CSV data
        csv_data = product.get('csv', [])
        has_csv_data = any(csv_data)

        # Check offers
        total_offers = stats.get('totalOfferCount', 0)
        result['offers'] = total_offers

        # Check sales rank
        sales_rank_ref = product.get('salesRankReference', -1)
        has_sales_rank = sales_rank_ref != -1

        # Déterminer le statut
        if price_found:
            result['status'] = 'ACTIVE'
            result['is_active'] = True
            result['reason'] = f"Active with {len(result['prices'])} price points"
        elif total_offers > 0:
            result['status'] = 'OFFERS_ONLY'
            result['reason'] = f"Has {total_offers} offers but no current prices"
        elif has_csv_data:
            result['status'] = 'HISTORICAL_ONLY'
            result['has_history'] = True
            result['reason'] = "Has historical data but no current prices"
        elif product.get('lastUpdate', 0) == product.get('trackingSince', 0):
            result['status'] = 'NEW_TRACKING'
            result['reason'] = "Recently added to tracking, no data yet"
        else:
            result['status'] = 'DISCONTINUED'
            result['reason'] = "No prices, offers, or recent data"

        # Info additionnelle
        if product.get('availabilityAmazon') == -1:
            result['amazon_availability'] = 'Not available'

        return result

    except Exception as e:
        return {
            'asin': asin,
            'status': 'ERROR',
            'reason': str(e)
        }


def main():
    """Analyse complète des 30 ASINs."""

    print("""
================================================================
        ANALYSE DISPONIBILITE DES 30 ASINs TEST
================================================================
    """)

    results = {
        'ACTIVE': [],
        'OFFERS_ONLY': [],
        'HISTORICAL_ONLY': [],
        'DISCONTINUED': [],
        'NEW_TRACKING': [],
        'ERROR': [],
        'NO_DATA': []
    }

    # Analyser chaque ASIN
    for i, asin in enumerate(TEST_ASINS, 1):
        print(f"[{i}/30] Analyzing {asin}...", end=' ')

        analysis = analyze_asin_status(asin)
        status = analysis['status']
        results[status].append(analysis)

        if analysis['is_active']:
            print(f"[OK] ACTIVE ({len(analysis['prices'])} prices)")
        else:
            print(f"[X] {status}")

    # Rapport détaillé
    print(f"\n{'='*60}")
    print("RAPPORT D'ANALYSE - DISPONIBILITE")
    print(f"{'='*60}\n")

    total = len(TEST_ASINS)
    active = len(results['ACTIVE'])

    print("[STATISTIQUES GLOBALES]")
    print(f"  Total ASINs testés: {total}")
    print(f"  ASINs ACTIFS (avec prix): {active} ({active/total*100:.1f}%)")
    print(f"  ASINs DISCONTINUES: {len(results['DISCONTINUED'])} ({len(results['DISCONTINUED'])/total*100:.1f}%)")
    print(f"  ASINs HISTORIQUE SEULEMENT: {len(results['HISTORICAL_ONLY'])} ({len(results['HISTORICAL_ONLY'])/total*100:.1f}%)")
    print(f"  ASINs AVEC OFFRES SEULEMENT: {len(results['OFFERS_ONLY'])} ({len(results['OFFERS_ONLY'])/total*100:.1f}%)")

    # Liste des ASINs actifs
    print(f"\n[ASINs ACTIFS - UTILISABLES POUR TESTS]")
    print("-" * 40)
    for item in results['ACTIVE']:
        prices_str = ', '.join([f"{k}=${v:.2f}" for k, v in item['prices'].items()])
        print(f"  {item['asin']}: {item['title'][:30]}")
        print(f"    Prix: {prices_str}")

    # ASINs problématiques
    print(f"\n[ASINs PROBLEMATIQUES]")
    print("-" * 40)

    for status in ['DISCONTINUED', 'HISTORICAL_ONLY', 'NO_DATA', 'ERROR']:
        if results[status]:
            print(f"\n  {status}:")
            for item in results[status]:
                print(f"    - {item['asin']}: {item['reason']}")

    # Recommandations
    print(f"\n[RECOMMANDATIONS]")
    print("-" * 40)

    if active < 15:
        print(f"  [!] Seulement {active} ASINs actifs sur 30")
        print("  -> Besoin de trouver plus d'ASINs actifs pour tests valides")
        print("  -> Utiliser Keepa Product Finder pour identifier ASINs avec:")
        print("    - Buy Box price disponible")
        print("    - Sales rank < 100,000")
        print("    - Offers count > 0")
    else:
        print(f"  [OK] {active} ASINs actifs suffisants pour tests")

    # Sauvegarder les résultats
    output = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total': total,
            'active': active,
            'discontinued': len(results['DISCONTINUED']),
            'historical_only': len(results['HISTORICAL_ONLY'])
        },
        'active_asins': [item['asin'] for item in results['ACTIVE']],
        'detailed_results': results
    }

    with open('asin_availability_analysis.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\n[OK] Analyse sauvegardée dans asin_availability_analysis.json")

    # Retourner liste ASINs actifs
    return [item['asin'] for item in results['ACTIVE']]


if __name__ == "__main__":
    active_asins = main()

    print(f"\n[ASINS ACTIFS POUR RE-TEST]")
    print("active_asins = [")
    for asin in active_asins:
        print(f'    "{asin}",')
    print("]")