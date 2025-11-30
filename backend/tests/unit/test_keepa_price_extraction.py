"""
Tests unitaires pour extraction prix Keepa - validation fix Oct 15 2025

Vérifie que le parser utilise stats.current[] et non data[] arrays pour les prix actuels.
"""
import json
import pytest
from pathlib import Path
from app.services.keepa_parser_v2 import KeepaRawParser, parse_keepa_product


@pytest.fixture
def keepa_raw_data():
    """Charger données Keepa réelles depuis JSON local"""
    json_path = Path(__file__).parent.parent.parent / "keepa_raw_0593655036.json"
    with open(json_path, 'r') as f:
        response = json.load(f)
    return response['products'][0]


def test_extract_prices_from_stats_current(keepa_raw_data):
    """
    TEST CRITIQUE: Vérifie que les prix viennent de stats.current[] et PAS de data[] arrays

    Contexte: Bug découvert Oct 15 2025 - parser lisait data['NEW'] (historique)
    au lieu de stats.current[1] (snapshot actuel)
    """
    # Extraire valeurs attendues depuis stats.current
    stats = keepa_raw_data.get('stats', {})
    current_array = stats.get('current', [])

    assert len(current_array) > 1, "stats.current array should exist"

    expected_amazon = current_array[0] / 100 if current_array[0] != -1 else None
    expected_new = current_array[1] / 100 if current_array[1] != -1 else None
    expected_used = current_array[2] / 100 if len(current_array) > 2 and current_array[2] != -1 else None

    # Parser le produit
    parser = KeepaRawParser()
    current_values = parser.extract_current_values(keepa_raw_data)

    # Vérifier que les prix correspondent a stats.current (pas data arrays)
    # Note: Les valeurs peuvent etre Decimal, donc on convertit en float pour comparaison
    if expected_amazon:
        actual_amazon = float(current_values.get('amazon_price', 0))
        assert abs(actual_amazon - expected_amazon) < 0.01, \
            f"AMAZON price should be ${expected_amazon:.2f} from stats.current[0]"

    if expected_new:
        actual_new = float(current_values.get('new_price', 0))
        assert abs(actual_new - expected_new) < 0.01, \
            f"NEW price should be ${expected_new:.2f} from stats.current[1], got ${actual_new:.2f}"

        # Verifier qu'on n'a pas de prix suspect (< $1.00 pour un bestseller)
        assert actual_new > 1.0, \
            f"NEW price ${actual_new:.2f} suspiciously low - likely from data[] array instead of stats.current"

    if expected_used:
        actual_used = float(current_values.get('used_price', 0))
        assert abs(actual_used - expected_used) < 0.01, \
            f"USED price should be ${expected_used:.2f} from stats.current[2]"


def test_price_extraction_regression_detection(keepa_raw_data):
    """
    TEST RÉGRESSION: Détecte retour au bug data[] arrays

    Si ce test échoue, le parser est probablement revenu à lire data['NEW'][-1]
    au lieu de stats.current[1]
    """
    parsed = parse_keepa_product(keepa_raw_data)

    new_price = parsed.get('current_fbm_price')

    # Pour ASIN 0593655036 (livre bestseller), le prix réel est ~$14
    # Si on lit data[] arrays, on obtient des valeurs < $1.00
    assert new_price is not None, "NEW price should be extracted"
    assert new_price > 10.0, \
        f"NEW price ${new_price:.2f} too low - REGRESSION: reading from data[] arrays!"


def test_parser_handles_missing_stats_current(keepa_raw_data):
    """Vérifie que parser gère absence de stats.current gracieusement"""
    # Supprimer stats.current
    if 'stats' in keepa_raw_data:
        del keepa_raw_data['stats']

    parser = KeepaRawParser()
    current_values = parser.extract_current_values(keepa_raw_data)

    # Devrait retourner dict vide sans crasher
    assert isinstance(current_values, dict)


def test_parser_handles_null_prices(keepa_raw_data):
    """Vérifie que parser gère valeurs -1 (null Keepa) correctement"""
    # Remplacer prix par -1 (null Keepa)
    keepa_raw_data['stats']['current'][1] = -1  # NEW price null

    parser = KeepaRawParser()
    current_values = parser.extract_current_values(keepa_raw_data)

    # new_price ne devrait pas être présent
    assert 'new_price' not in current_values or current_values['new_price'] is None


def test_full_parse_includes_correct_prices(keepa_raw_data):
    """Test intégration complète: parse_keepa_product retourne prix corrects"""
    parsed = parse_keepa_product(keepa_raw_data)

    # Vérifier que les champs prix sont présents
    assert 'current_amazon_price' in parsed
    assert 'current_fbm_price' in parsed
    assert 'current_used_price' in parsed

    # Vérifier valeurs réalistes (ce livre coûte ~$14-17)
    amazon_price = parsed.get('current_amazon_price')
    new_price = parsed.get('current_fbm_price')

    if amazon_price:
        assert 10.0 < amazon_price < 30.0, f"Amazon price ${amazon_price:.2f} outside realistic range"

    if new_price:
        assert 10.0 < new_price < 30.0, f"NEW price ${new_price:.2f} outside realistic range"
