#!/usr/bin/env python
"""
Script de test direct API Keepa pour contourner le problème MCP Claude Code.
Usage: python test_keepa_direct.py <ASIN>
"""

import json
import sys
import requests
from typing import Optional

API_URL = "https://arbitragevault-backend-v2.onrender.com/api/v1/keepa/ingest"

def test_keepa_ingest(asin: str, force_refresh: bool = False) -> dict:
    """Test l'endpoint ingest avec un ASIN."""

    payload = {
        "identifiers": [asin],
        "config_profile": "default",
        "force_refresh": force_refresh,
        "async_threshold": 100
    }

    print(f">> Envoi requete pour ASIN: {asin}")
    print(f"   Force refresh: {force_refresh}")

    try:
        response = requests.post(API_URL, json=payload, timeout=30)
        response.raise_for_status()

        data = response.json()

        print("\n[OK] Reponse recue:")
        print(f"   Batch ID: {data.get('batch_id')}")
        print(f"   Items traites: {data.get('processed')}/{data.get('total_items')}")

        if data.get('results'):
            result = data['results'][0]
            if result.get('status') == 'success':
                analysis = result.get('analysis', {})
                print(f"\n[ANALYSE]")
                print(f"   Titre: {analysis.get('title', 'N/A')}")
                print(f"   BSR: {analysis.get('current_bsr', 'N/A'):,}")
                print(f"   Prix actuel: ${analysis.get('current_price', 0):.2f}")
                print(f"   Rating: {analysis.get('overall_rating', 'N/A')}")

                scores = analysis.get('score_breakdown', {})
                print(f"\n[SCORES]")
                for key, value in scores.items():
                    print(f"   {key}: {value.get('score', 0)} - {value.get('notes', '')}")

                if analysis.get('risk_factors'):
                    print(f"\n[RISQUES]")
                    for risk in analysis['risk_factors']:
                        print(f"   - {risk}")
            else:
                print(f"[ERREUR]: {result.get('error')}")

        return data

    except requests.exceptions.RequestException as e:
        print(f"[ERREUR] Reseau: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"[ERREUR] JSON: {e}")
        return {}

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_keepa_direct.py <ASIN> [--force-refresh]")
        sys.exit(1)

    asin = sys.argv[1]
    force_refresh = "--force-refresh" in sys.argv

    print("Test API Keepa Direct (contournement MCP)")
    print("=" * 50)

    result = test_keepa_ingest(asin, force_refresh)

    print("\n" + "=" * 50)
    print("JSON complet sauvegarde dans: test_result.json")

    with open("test_result.json", "w") as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    main()