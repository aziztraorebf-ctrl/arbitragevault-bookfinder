#!/usr/bin/env python3
"""
Debug Niche Analysis - Diagnostic détaillé
==========================================

Script pour diagnostiquer pourquoi l'analyse E2E ne trouve pas de niches.
"""

import asyncio
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_path))

import keyring
from app.services.keepa_service import KeepaService
from app.services.category_analyzer import CategoryAnalyzer
from app.models.niche import NicheAnalysisCriteria


async def debug_single_category_analysis():
    """Debug détaillé d'une seule catégorie."""
    print("🔍 DEBUG ANALYSE CATÉGORIE DÉTAILLÉE")
    print("=" * 50)
    
    # Setup
    keepa_api_key = keyring.get_password("memex", "KEEPA_API_KEY")
    keepa_service = KeepaService(keepa_api_key)
    analyzer = CategoryAnalyzer(keepa_service)
    
    # Critères plus permissifs pour debug
    criteria = NicheAnalysisCriteria(
        bsr_range=(1000, 100000),  # Plage très large
        max_sellers=10,            # Plus permissif
        min_margin_percent=15.0,   # Marge plus faible
        min_price_stability=0.50,  # Stabilité plus faible
        sample_size=5              # Petit échantillon
    )
    
    print(f"Critères debug : BSR {criteria.bsr_range}, ≤{criteria.max_sellers} vendeurs")
    print(f"Marge ≥{criteria.min_margin_percent}%, Stabilité ≥{criteria.min_price_stability}")
    
    # Test catégorie Medical Books (3738)
    category_id = 3738
    category_name = "Health, Fitness & Dieting > Medical Books"
    
    print(f"\n📚 Analyse catégorie : {category_name}")
    
    # Obtenir échantillon d'ASINs
    sample_asins = analyzer._get_sample_asins_for_category(category_id)
    print(f"ASINs d'échantillon : {sample_asins[:5]}")
    
    # Analyser chaque produit individuellement
    viable_count = 0
    total_analyzed = 0
    
    for i, asin in enumerate(sample_asins[:5]):
        print(f"\n--- Produit {i+1}: {asin} ---")
        
        try:
            # Récupérer données Keepa
            product_data = await keepa_service.get_product_data(asin)
            
            if not product_data:
                print("❌ Aucune donnée Keepa")
                continue
            
            total_analyzed += 1
            
            # Analyser chaque composant
            print(f"Titre : {product_data.get('title', 'Non disponible')[:50]}")
            
            # BSR
            bsr = analyzer._extract_bsr(product_data)
            print(f"BSR : {bsr:,}" if bsr else "BSR : Non disponible")
            bsr_ok = bsr and criteria.bsr_range[0] <= bsr <= criteria.bsr_range[1]
            print(f"   BSR dans plage : {'✅' if bsr_ok else '❌'}")
            
            # Prix
            price = analyzer._extract_current_price(product_data)
            print(f"Prix : ${price:.2f}" if price else "Prix : Non disponible")
            
            # Vendeurs
            sellers = analyzer._estimate_seller_count(product_data)
            print(f"Vendeurs estimés : {sellers:.1f}")
            sellers_ok = sellers <= criteria.max_sellers
            print(f"   Vendeurs acceptable : {'✅' if sellers_ok else '❌'}")
            
            # Stabilité prix
            stability = analyzer._calculate_price_stability(product_data)
            print(f"Stabilité prix : {stability:.3f}" if stability else "Stabilité : Non calculable")
            stability_ok = stability and stability >= criteria.min_price_stability
            print(f"   Stabilité acceptable : {'✅' if stability_ok else '❌'}")
            
            # Marge profit
            margin = analyzer._estimate_profit_margin(product_data, criteria)
            print(f"Marge profit : {margin:.1f}%" if margin else "Marge : Non calculable")
            margin_ok = margin and margin >= criteria.min_margin_percent
            print(f"   Marge acceptable : {'✅' if margin_ok else '❌'}")
            
            # Test viabilité globale
            viable = analyzer._is_product_viable(product_data, criteria)
            print(f"VIABLE : {'✅ OUI' if viable else '❌ NON'}")
            
            if viable:
                viable_count += 1
            
            # Afficher données brutes critiques
            print(f"Données debug :")
            print(f"   availabilityAmazon : {product_data.get('availabilityAmazon', 'N/A')}")
            csv_data = product_data.get('csv', [])
            if csv_data:
                amazon_prices = csv_data[0] if len(csv_data) > 0 else []
                recent_prices = [p for p in amazon_prices[-5:] if p and p > 0] if amazon_prices else []
                print(f"   Prix récents (csv[0]) : {recent_prices}")
            
        except Exception as e:
            print(f"❌ Erreur analyse {asin} : {e}")
            continue
        
        await asyncio.sleep(0.2)  # Rate limiting
    
    print(f"\n📊 RÉSUMÉ CATÉGORIE {category_name}")
    print(f"Produits analysés : {total_analyzed}")
    print(f"Produits viables : {viable_count}")
    print(f"Taux viabilité : {viable_count/total_analyzed*100:.1f}%" if total_analyzed > 0 else "N/A")
    
    # Si aucun viable avec critères permissifs = problème dans la logique
    if viable_count == 0 and total_analyzed > 0:
        print("\n⚠️  PROBLÈME DÉTECTÉ : Aucun produit viable avec critères très permissifs")
        print("Cela suggère un problème dans la logique de calcul des métriques")
    
    return viable_count > 0


async def main():
    """Point d'entrée principal."""
    await debug_single_category_analysis()


if __name__ == "__main__":
    asyncio.run(main())