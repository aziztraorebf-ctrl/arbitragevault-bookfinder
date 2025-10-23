#!/usr/bin/env python
"""
Helper API ArbitrageVault - Contournement MCP pour Claude Code
Usage: python api_helper.py <endpoint> [args]

Exemples:
  python api_helper.py ingest 0316769487
  python api_helper.py metrics B00FLIJJSA
  python api_helper.py raw B00FLIJJSA
  python api_helper.py health
"""

import json
import sys
import requests
from typing import Optional, List, Dict, Any

BASE_URL = "https://arbitragevault-backend-v2.onrender.com/api/v1"

class APIHelper:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def _pretty_print(self, data: dict, title: str = ""):
        """Affichage formaté des résultats."""
        if title:
            print(f"\n{'='*60}")
            print(f"  {title}")
            print('='*60)

        print(json.dumps(data, indent=2, ensure_ascii=False))

    def _handle_error(self, response: requests.Response):
        """Gestion des erreurs HTTP."""
        try:
            error_data = response.json()
            print(f"[ERREUR HTTP {response.status_code}]")
            self._pretty_print(error_data)
        except:
            print(f"[ERREUR HTTP {response.status_code}]: {response.text}")

    # === KEEPA ENDPOINTS ===

    def ingest(self, identifiers: List[str], force_refresh: bool = False,
               config_profile: str = "default"):
        """POST /keepa/ingest - Ingère des ASINs pour analyse."""
        url = f"{self.base_url}/keepa/ingest"

        payload = {
            "identifiers": identifiers if isinstance(identifiers, list) else [identifiers],
            "config_profile": config_profile,
            "force_refresh": force_refresh,
            "async_threshold": 100
        }

        print(f"\n>> POST /keepa/ingest")
        print(f"   Identifiers: {identifiers}")
        print(f"   Force refresh: {force_refresh}")

        try:
            response = self.session.post(url, json=payload, timeout=30)

            if response.status_code == 200:
                data = response.json()
                self._pretty_print(data, "Ingest Response")

                # Résumé rapide
                print(f"\n[RESUME]")
                print(f"  Batch ID: {data.get('batch_id')}")
                print(f"  Traités: {data.get('processed')}/{data.get('total_items')}")
                print(f"  Succès: {data.get('successful')}, Échecs: {data.get('failed')}")

                return data
            else:
                self._handle_error(response)
                return None

        except requests.exceptions.RequestException as e:
            print(f"[ERREUR RESEAU]: {e}")
            return None

    def metrics(self, asin: str, force_refresh: bool = False,
                config_profile: str = "default"):
        """GET /keepa/{asin}/metrics - Récupère métriques complètes."""
        url = f"{self.base_url}/keepa/{asin}/metrics"
        params = {
            "force_refresh": force_refresh,
            "config_profile": config_profile
        }

        print(f"\n>> GET /keepa/{asin}/metrics")

        try:
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                self._pretty_print(data, f"Metrics for {asin}")

                # Résumé des scores
                if 'analysis' in data:
                    analysis = data['analysis']
                    print(f"\n[SCORES]")
                    print(f"  Velocity: {analysis.get('velocity_score', 'N/A')}")
                    print(f"  Stability: {analysis.get('price_stability_score', 'N/A')}")
                    print(f"  Confidence: {analysis.get('confidence_score', 'N/A')}")
                    print(f"  Rating: {analysis.get('overall_rating', 'N/A')}")

                return data
            else:
                self._handle_error(response)
                return None

        except requests.exceptions.RequestException as e:
            print(f"[ERREUR RESEAU]: {e}")
            return None

    def raw_keepa(self, asin: str, force_refresh: bool = False):
        """GET /keepa/{asin}/raw - Données brutes Keepa."""
        url = f"{self.base_url}/keepa/{asin}/raw"
        params = {"force_refresh": force_refresh}

        print(f"\n>> GET /keepa/{asin}/raw")

        try:
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                self._pretty_print(data, f"Raw Keepa Data for {asin}")
                return data
            else:
                self._handle_error(response)
                return None

        except requests.exceptions.RequestException as e:
            print(f"[ERREUR RESEAU]: {e}")
            return None

    # === HEALTH ENDPOINTS ===

    def health(self):
        """GET /health - Status du backend."""
        url = f"{self.base_url.replace('/api/v1', '')}/health"

        print(f"\n>> GET /health")

        try:
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                self._pretty_print(data, "Backend Health")
                return data
            else:
                self._handle_error(response)
                return None

        except requests.exceptions.RequestException as e:
            print(f"[ERREUR RESEAU]: {e}")
            return None

    def keepa_health(self):
        """GET /keepa/health - Status Keepa service."""
        url = f"{self.base_url}/keepa/health"

        print(f"\n>> GET /keepa/health")

        try:
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                self._pretty_print(data, "Keepa Service Health")
                return data
            else:
                self._handle_error(response)
                return None

        except requests.exceptions.RequestException as e:
            print(f"[ERREUR RESEAU]: {e}")
            return None

    # === BATCH ENDPOINTS ===

    def list_batches(self, page: int = 1, per_page: int = 20):
        """GET /batches - Liste des batches."""
        url = f"{self.base_url}/batches"
        params = {"page": page, "per_page": per_page}

        print(f"\n>> GET /batches (page {page})")

        try:
            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                self._pretty_print(data, "Batches List")

                print(f"\n[RESUME]")
                print(f"  Total: {data.get('total')}")
                print(f"  Page: {data.get('page')}/{data.get('pages')}")

                return data
            else:
                self._handle_error(response)
                return None

        except requests.exceptions.RequestException as e:
            print(f"[ERREUR RESEAU]: {e}")
            return None


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1].lower()
    helper = APIHelper()

    try:
        if command == "ingest":
            if len(sys.argv) < 3:
                print("Usage: python api_helper.py ingest <ASIN1> [ASIN2...] [--force-refresh]")
                sys.exit(1)

            force_refresh = "--force-refresh" in sys.argv
            asins = [arg for arg in sys.argv[2:] if not arg.startswith("--")]

            result = helper.ingest(asins, force_refresh=force_refresh)

        elif command == "metrics":
            if len(sys.argv) < 3:
                print("Usage: python api_helper.py metrics <ASIN> [--force-refresh]")
                sys.exit(1)

            asin = sys.argv[2]
            force_refresh = "--force-refresh" in sys.argv

            result = helper.metrics(asin, force_refresh=force_refresh)

        elif command == "raw":
            if len(sys.argv) < 3:
                print("Usage: python api_helper.py raw <ASIN> [--force-refresh]")
                sys.exit(1)

            asin = sys.argv[2]
            force_refresh = "--force-refresh" in sys.argv

            result = helper.raw_keepa(asin, force_refresh=force_refresh)

        elif command == "health":
            result = helper.health()

        elif command == "keepa-health":
            result = helper.keepa_health()

        elif command == "batches":
            page = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            result = helper.list_batches(page=page)

        else:
            print(f"Commande inconnue: {command}")
            print(__doc__)
            sys.exit(1)

        # Sauvegarde résultat
        if result:
            with open("last_api_result.json", "w") as f:
                json.dump(result, f, indent=2)
            print(f"\n[SAUVEGARDE] Résultat dans: last_api_result.json")

    except KeyboardInterrupt:
        print("\n\n[INTERROMPU]")
        sys.exit(0)

if __name__ == "__main__":
    main()
