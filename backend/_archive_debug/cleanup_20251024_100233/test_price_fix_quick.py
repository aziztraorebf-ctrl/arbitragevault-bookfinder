"""
Test rapide validation fix prix - utilise JSON local
"""
import json
from pathlib import Path
from app.services.keepa_parser_v2 import parse_keepa_product

def test_price_extraction():
    """Test que les prix sont extraits depuis stats.current et pas data arrays"""

    # Charger données Keepa raw
    json_path = Path(__file__).parent / "keepa_raw_0593655036.json"
    with open(json_path, 'r') as f:
        keepa_response = json.load(f)

    product_raw = keepa_response['products'][0]
    asin = product_raw['asin']

    print("\n" + "="*70)
    print("TEST EXTRACTION PRIX - POST FIX")
    print("="*70)
    print(f"\nASIN: {asin}")

    # Afficher ce qui est disponible dans Keepa response
    print("\n--- DONNÉES DISPONIBLES DANS KEEPA ---")

    # 1. Stats.current array (✅ SOURCE CORRECTE)
    stats = product_raw.get('stats', {})
    current_array = stats.get('current', [])

    if current_array and len(current_array) > 1:
        amazon_price_cents = current_array[0] if current_array[0] != -1 else None
        new_price_cents = current_array[1] if current_array[1] != -1 else None
        used_price_cents = current_array[2] if len(current_array) > 2 and current_array[2] != -1 else None

        print("\nOK stats.current[] array (CORRECT SOURCE):")
        if amazon_price_cents:
            print(f"  - current[0] AMAZON: ${amazon_price_cents/100:.2f}")
        if new_price_cents:
            print(f"  - current[1] NEW: ${new_price_cents/100:.2f}")
        if used_price_cents:
            print(f"  - current[2] USED: ${used_price_cents/100:.2f}")

    # 2. Data arrays (WRONG - SOURCE INCORRECTE - historique)
    data = product_raw.get('data', {})
    if data:
        print("\nWRONG data[] arrays (WRONG SOURCE - historical):")
        for key in ['AMAZON', 'NEW', 'USED']:
            if key in data:
                values = data[key]
                if values is not None and len(values) > 0:
                    # Dernier élément (ce que lisait l'ancien code)
                    last_value = values[-1] if isinstance(values, list) else None
                    if last_value and last_value != -1:
                        print(f"  - data['{key}'][-1]: ${last_value/100:.2f} (dernier historique)")

    # 3. Parser le produit avec NOUVEAU code
    print("\n--- RÉSULTAT DU PARSER (NOUVEAU CODE) ---")
    parsed = parse_keepa_product(product_raw)

    print(f"\nPrix extraits par le parser:")
    print(f"  current_amazon_price: ${parsed.get('current_amazon_price', 'N/A')}")
    print(f"  current_fbm_price (NEW): ${parsed.get('current_fbm_price', 'N/A')}")
    print(f"  current_used_price: ${parsed.get('current_used_price', 'N/A')}")
    print(f"  current_fba_price: ${parsed.get('current_fba_price', 'N/A')}")
    print(f"  current_buybox_price: ${parsed.get('current_buybox_price', 'N/A')}")
    print(f"  current_price (best): ${parsed.get('current_price', 'N/A')}")

    # Validation
    print("\n--- VALIDATION ---")

    expected_new_price = new_price_cents / 100 if new_price_cents else None
    actual_new_price = float(parsed.get('current_fbm_price', 0)) if parsed.get('current_fbm_price') else None

    if expected_new_price and actual_new_price:
        if abs(expected_new_price - actual_new_price) < 0.01:
            print(f"PASS: NEW price correct (${actual_new_price:.2f} == ${expected_new_price:.2f})")
        else:
            print(f"FAIL: NEW price incorrect!")
            print(f"   Attendu (stats.current[1]): ${expected_new_price:.2f}")
            print(f"   Obtenu (parser): ${actual_new_price:.2f}")
            return False

    # Vérifier qu'on n'a PAS de prix suspects (< $1.00 pour ce livre)
    if actual_new_price and actual_new_price < 1.0:
        print(f"FAIL: Prix suspect detecte (${actual_new_price:.2f} < $1.00)")
        print("   Probable lecture depuis data[] arrays au lieu de stats.current[]")
        return False

    if actual_new_price and actual_new_price > 10.0:
        print(f"PASS: Prix realiste pour un livre bestseller (${actual_new_price:.2f})")

    print("\n" + "="*70)
    print("TEST REUSSI - Prix extraits correctement depuis stats.current[]")
    print("="*70 + "\n")

    return True

if __name__ == "__main__":
    success = test_price_extraction()
    exit(0 if success else 1)
