#!/usr/bin/env python3
"""
Real user test for AutoSourcing - simulates finding products and calculating profits.
"""
import requests
import json

def run_search():
    print("Launching AutoSourcing search...")

    response = requests.post(
        'https://arbitragevault-backend-v2.onrender.com/api/v1/autosourcing/run-custom',
        json={
            'discovery_config': {
                'categories': ['books'],
                'bsr_range': [1, 100000],
                'price_range': [8, 50],
                'max_fba_sellers': 8,
                'exclude_amazon_seller': True,
                'max_results': 25
            },
            'scoring_config': {
                'roi_min': 20,
                'velocity_min': 45,
                'stability_min': 45,
                'confidence_min': 45
            },
            'profile_name': 'Real-User-Test-Dec17-v2'
        },
        timeout=180
    )

    print(f"Status: {response.status_code}")
    data = response.json()

    print(f"\n=== RESULTATS RECHERCHE ===")
    print(f"Job ID: {data['id']}")
    print(f"Duree: {data['duration_ms']}ms")
    print(f"Produits testes: {data['total_tested']}")
    print(f"Produits selectionnes: {data['total_selected']}")
    print()

    if data['picks']:
        total_investment = 0
        total_profit = 0

        print(f"=== {len(data['picks'])} PRODUITS TROUVES ===")
        print()

        for i, pick in enumerate(data['picks'], 1):
            price = pick['current_price'] or 0
            roi = pick['roi_percentage']
            estimated_buy = pick.get('estimated_buy_cost') or (price * 0.3)
            profit = pick.get('profit_net') or (price * roi / 100)

            total_investment += estimated_buy
            total_profit += profit

            print(f"{i}. {pick['asin']}")
            print(f"   Titre: {pick['title'][:60]}...")
            print(f"   Prix vente: ${price:.2f}")
            print(f"   Cout achat estime: ${estimated_buy:.2f}")
            print(f"   Profit net estime: ${profit:.2f}")
            print(f"   ROI: {roi}%")
            print(f"   BSR: {pick['bsr']} | Velocity: {pick['velocity_score']} | Rating: {pick['overall_rating']}")
            print(f"   FBA Sellers: {pick.get('fba_seller_count', 'N/A')} | Amazon: {pick.get('amazon_on_listing', 'N/A')}")
            print()

        print(f"=== RESUME FINANCIER ===")
        print(f"Investissement total: ${total_investment:.2f}")
        print(f"Profit total estime: ${total_profit:.2f}")
        roi_avg = (total_profit/total_investment*100) if total_investment > 0 else 0
        print(f"ROI moyen: {roi_avg:.1f}%")
        print()
        print(f"Si vous vendez 1 exemplaire de chaque par jour:")
        print(f"  - Profit journalier: ${total_profit:.2f}")
        print(f"  - Profit hebdomadaire: ${total_profit * 7:.2f}")
        print(f"  - Profit mensuel: ${total_profit * 30:.2f}")
    else:
        print('Aucun produit trouve avec ces criteres.')
        print('Conseil: Elargir les criteres ou reduire le roi_min')

if __name__ == "__main__":
    run_search()
