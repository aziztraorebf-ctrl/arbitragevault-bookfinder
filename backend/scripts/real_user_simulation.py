#!/usr/bin/env python3
"""
Real user simulation - analyze existing picks with MCP validation.
Shows what a real arbitrage seller would earn.
"""
import requests

def main():
    # Get existing picks from the API
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

    # Remove duplicates by ASIN
    unique_asins = {}
    for pick in all_picks:
        asin = pick['asin']
        if asin not in unique_asins:
            unique_asins[asin] = pick

    unique_picks = list(unique_asins.values())

    print("=" * 70)
    print("   RAPPORT D'ARBITRAGE - SIMULATION UTILISATEUR REEL")
    print("=" * 70)
    print()
    print(f"Produits uniques trouves: {len(unique_picks)}")
    print()

    # Categorize by rating
    excellent = [p for p in unique_picks if p['overall_rating'] == 'EXCELLENT']
    good = [p for p in unique_picks if p['overall_rating'] == 'GOOD']
    fair = [p for p in unique_picks if p['overall_rating'] == 'FAIR']

    print(f"  - EXCELLENT: {len(excellent)} produits (meilleurs deals)")
    print(f"  - GOOD: {len(good)} produits")
    print(f"  - FAIR: {len(fair)} produits")
    print()

    # Focus on EXCELLENT products only for realistic scenario
    print("-" * 70)
    print("   TOP PICKS (EXCELLENT seulement)")
    print("-" * 70)
    print()

    total_investment = 0
    total_profit = 0

    for i, pick in enumerate(excellent, 1):
        price = pick['current_price'] or 0
        roi = pick['roi_percentage']
        bsr = pick['bsr'] or 0
        velocity = pick['velocity_score']

        # Realistic buy cost estimation based on BSR
        # Lower BSR = more popular = likely higher buy cost (30-40%)
        # Higher BSR = niche = can find cheaper (20-30%)
        if bsr < 1000:
            buy_ratio = 0.35  # 35% of sale price
        elif bsr < 10000:
            buy_ratio = 0.30  # 30%
        elif bsr < 50000:
            buy_ratio = 0.25  # 25%
        else:
            buy_ratio = 0.20  # 20%

        estimated_buy = price * buy_ratio

        # Amazon FBA fees estimation (approximately 15% + $3-5 per item)
        fba_fee = price * 0.15 + 4.00

        # Realistic profit calculation
        profit = price - estimated_buy - fba_fee

        total_investment += estimated_buy
        total_profit += profit

        print(f"{i}. {pick['asin']} - BSR #{bsr:,}")
        print(f"   {pick['title'][:55]}...")
        print(f"   Prix vente Amazon:  ${price:.2f}")
        print(f"   Cout achat estime:  ${estimated_buy:.2f} ({buy_ratio*100:.0f}%)")
        print(f"   Frais FBA estimes:  ${fba_fee:.2f}")
        print(f"   PROFIT NET:         ${profit:.2f}")
        print(f"   Velocity: {velocity}/100 | ROI declare: {roi}%")
        print()

    print("=" * 70)
    print("   PROJECTIONS FINANCIERES")
    print("=" * 70)
    print()
    print(f"Nombre de produits EXCELLENT: {len(excellent)}")
    print(f"Investissement total:         ${total_investment:.2f}")
    print(f"Profit total par vente:       ${total_profit:.2f}")
    print()

    if total_investment > 0:
        actual_roi = (total_profit / total_investment) * 100
        print(f"ROI reel (apres frais FBA):   {actual_roi:.1f}%")
    print()

    print("-" * 70)
    print("   SCENARIO: 1 vente par produit par jour")
    print("-" * 70)
    print(f"   Profit journalier:   ${total_profit:.2f}")
    print(f"   Profit hebdomadaire: ${total_profit * 7:.2f}")
    print(f"   Profit mensuel:      ${total_profit * 30:.2f}")
    print()

    print("-" * 70)
    print("   SCENARIO: 2 ventes par produit par jour (realiste avec BSR bas)")
    print("-" * 70)
    print(f"   Profit journalier:   ${total_profit * 2:.2f}")
    print(f"   Profit hebdomadaire: ${total_profit * 14:.2f}")
    print(f"   Profit mensuel:      ${total_profit * 60:.2f}")
    print()

    print("-" * 70)
    print("   INVESTISSEMENT INITIAL REQUIS")
    print("-" * 70)
    print(f"   Pour 1 exemplaire de chaque:  ${total_investment:.2f}")
    print(f"   Pour 5 exemplaires de chaque: ${total_investment * 5:.2f}")
    print(f"   Pour 10 exemplaires de chaque: ${total_investment * 10:.2f}")
    print()

    print("=" * 70)
    print("   NOTES IMPORTANTES")
    print("=" * 70)
    print("""
    1. Ces calculs sont des ESTIMATIONS basees sur:
       - Prix de vente actuel sur Amazon
       - Cout d'achat estime (20-35% selon popularite)
       - Frais FBA estimes (15% + $4 par article)

    2. Facteurs non inclus:
       - Frais d'expedition vers Amazon
       - Taxes
       - Retours clients
       - Variations de prix

    3. BSR (Best Seller Rank) indique la velocite de vente:
       - < 1,000 = vend plusieurs fois par jour
       - 1,000-10,000 = vend plusieurs fois par semaine
       - 10,000-100,000 = vend plusieurs fois par mois

    4. Les produits EXCELLENT ont ete pre-filtres pour:
       - ROI minimum 25%
       - Velocity score eleve
       - Stabilite des ventes
    """)

if __name__ == "__main__":
    main()
