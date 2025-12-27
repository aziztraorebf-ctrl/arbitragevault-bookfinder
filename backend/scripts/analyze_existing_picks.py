#!/usr/bin/env python3
"""
Analyze existing AutoSourcing picks and calculate profit projections.
"""
import requests

def main():
    # Recuperer tous les jobs avec picks
    response = requests.get(
        'https://arbitragevault-backend-v2.onrender.com/api/v1/autosourcing/jobs?limit=20',
        timeout=30
    )

    jobs = response.json()
    all_picks = []

    for job in jobs:
        if job['total_selected'] > 0:
            for pick in job['picks']:
                all_picks.append(pick)

    print(f"=== ANALYSE DE {len(all_picks)} PRODUITS EXISTANTS ===")
    print()

    if all_picks:
        total_investment = 0
        total_profit = 0

        for i, pick in enumerate(all_picks, 1):
            price = pick['current_price'] or 0
            roi = pick['roi_percentage']

            # Estimation cout achat: ~30% du prix de vente pour livres
            estimated_buy = price * 0.30
            profit = price * roi / 100

            total_investment += estimated_buy
            total_profit += profit

            print(f"{i}. {pick['asin']}")
            print(f"   Titre: {pick['title'][:55]}...")
            print(f"   Prix vente Amazon: ${price:.2f}")
            print(f"   Cout achat estime (30%): ${estimated_buy:.2f}")
            print(f"   Profit net estime: ${profit:.2f}")
            print(f"   ROI: {roi}% | BSR: {pick['bsr']} | Velocity: {pick['velocity_score']}")
            print(f"   Rating: {pick['overall_rating']}")
            fba = pick.get('fba_seller_count', 'N/A')
            amazon = pick.get('amazon_on_listing', 'N/A')
            print(f"   FBA Sellers: {fba} | Amazon vend: {amazon}")
            print()

        print("=" * 60)
        print(f"=== RESUME FINANCIER - {len(all_picks)} PRODUITS ===")
        print("=" * 60)
        print()
        print(f"Investissement total (30% du prix): ${total_investment:.2f}")
        print(f"Profit total estime (base sur ROI): ${total_profit:.2f}")
        print()
        print("--- PROJECTIONS ---")
        print(f"Si vous vendez 1 exemplaire de CHAQUE produit:")
        print(f"  Profit: ${total_profit:.2f}")
        print()
        print(f"Par JOUR (1 vente/produit):")
        print(f"  Profit journalier: ${total_profit:.2f}")
        print()
        print(f"Par SEMAINE (7 jours):")
        print(f"  Profit hebdo: ${total_profit * 7:.2f}")
        print()
        print(f"Par MOIS (30 jours):")
        print(f"  Profit mensuel: ${total_profit * 30:.2f}")
        print()
        print("--- ROI GLOBAL ---")
        roi_global = (total_profit / total_investment * 100) if total_investment > 0 else 0
        print(f"ROI moyen: {roi_global:.1f}%")
        print(f"Pour $100 investi: ${100 * roi_global / 100:.2f} de profit")
    else:
        print("Aucun pick trouve.")

if __name__ == "__main__":
    main()
