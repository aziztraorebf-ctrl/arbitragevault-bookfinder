"""
Micro-tests de robustesse pour les tables cache Phase 3
========================================================

Tests:
1. TTL Expiration - Vérifier purge des entrées expirées
2. Cache Hit - Vérifier incrémentation hit_count
3. Concurrent Access - Vérifier absence de deadlock

Usage:
    python test_cache_robustesse.py
"""

import os
import time
import json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Charger variables environnement
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError("DATABASE_URL non trouvee dans .env")

engine = create_engine(DATABASE_URL)

print("=" * 70)
print("MICRO-TESTS DE ROBUSTESSE - TABLES CACHE PHASE 3")
print("=" * 70)
print()

# =============================================================================
# TEST 1: TTL EXPIRATION
# =============================================================================

def test_ttl_expiration():
    """
    Test 1: Valider que les entrées expirées sont correctement identifiées
    et peuvent être purgées.
    """
    print("[TEST 1] TTL EXPIRATION")
    print("-" * 70)

    with engine.connect() as conn:
        # Nettoyer d'abord
        conn.execute(text("DELETE FROM product_discovery_cache WHERE cache_key LIKE 'test_ttl_%'"))
        conn.commit()

        # Insérer entrée EXPIRÉE (1 heure dans le passé)
        expired_key = "test_ttl_expired"
        expired_time = datetime.utcnow() - timedelta(hours=1)

        conn.execute(text("""
            INSERT INTO product_discovery_cache
            (cache_key, asins, filters_applied, created_at, expires_at, hit_count)
            VALUES (:key, :asins, :filters, NOW(), :expires, 0)
        """), {
            "key": expired_key,
            "asins": json.dumps(["B08N5WRWNW", "B00FLIJJSA"]),
            "filters": json.dumps({"bsr_min": 10000, "bsr_max": 50000}),
            "expires": expired_time
        })

        # Insérer entrée VALIDE (expire dans 24h)
        valid_key = "test_ttl_valid"
        valid_time = datetime.utcnow() + timedelta(hours=24)

        conn.execute(text("""
            INSERT INTO product_discovery_cache
            (cache_key, asins, filters_applied, created_at, expires_at, hit_count)
            VALUES (:key, :asins, :filters, NOW(), :expires, 0)
        """), {
            "key": valid_key,
            "asins": json.dumps(["0593655036", "1492056200"]),
            "filters": json.dumps({"bsr_min": 5000, "bsr_max": 30000}),
            "expires": valid_time
        })

        conn.commit()

        print(f"  - Entree expiree inseree: {expired_key} (expires_at: {expired_time})")
        print(f"  - Entree valide inseree: {valid_key} (expires_at: {valid_time})")
        print()

        # Vérifier nombre d'entrées expirées
        result = conn.execute(text("""
            SELECT COUNT(*) FROM product_discovery_cache
            WHERE cache_key LIKE 'test_ttl_%' AND expires_at < NOW()
        """))
        expired_count = result.scalar()

        result = conn.execute(text("""
            SELECT COUNT(*) FROM product_discovery_cache
            WHERE cache_key LIKE 'test_ttl_%' AND expires_at >= NOW()
        """))
        valid_count = result.scalar()

        print(f"  - Entrees expirees detectees: {expired_count}")
        print(f"  - Entrees valides detectees: {valid_count}")
        print()

        # Simuler purge (DELETE expired)
        result = conn.execute(text("""
            DELETE FROM product_discovery_cache
            WHERE cache_key LIKE 'test_ttl_%' AND expires_at < NOW()
            RETURNING cache_key
        """))
        deleted_keys = [row[0] for row in result]
        conn.commit()

        print(f"  - Entrees purgees: {len(deleted_keys)}")
        for key in deleted_keys:
            print(f"    * {key}")
        print()

        # Vérifier qu'il reste seulement l'entrée valide
        result = conn.execute(text("""
            SELECT cache_key FROM product_discovery_cache
            WHERE cache_key LIKE 'test_ttl_%'
        """))
        remaining_keys = [row[0] for row in result]

        print(f"  - Entrees restantes: {len(remaining_keys)}")
        for key in remaining_keys:
            print(f"    * {key}")
        print()

        # Cleanup
        conn.execute(text("DELETE FROM product_discovery_cache WHERE cache_key LIKE 'test_ttl_%'"))
        conn.commit()

        # Validation
        success = (expired_count == 1 and valid_count == 1 and
                   len(deleted_keys) == 1 and deleted_keys[0] == expired_key and
                   len(remaining_keys) == 1 and remaining_keys[0] == valid_key)

        if success:
            print("  RESULTAT: [OK] TTL expiration fonctionne correctement")
        else:
            print("  RESULTAT: [FAIL] Probleme avec logique expiration")

        print()
        return success


# =============================================================================
# TEST 2: CACHE HIT INCREMENT
# =============================================================================

def test_cache_hit_increment():
    """
    Test 2: Valider que hit_count s'incrémente correctement lors de
    réutilisations successives du cache.
    """
    print("[TEST 2] CACHE HIT INCREMENT")
    print("-" * 70)

    with engine.connect() as conn:
        # Nettoyer d'abord
        conn.execute(text("DELETE FROM product_discovery_cache WHERE cache_key = 'test_hit_count'"))
        conn.commit()

        # Insérer entrée avec hit_count = 0
        cache_key = "test_hit_count"
        conn.execute(text("""
            INSERT INTO product_discovery_cache
            (cache_key, asins, filters_applied, created_at, expires_at, hit_count)
            VALUES (:key, :asins, :filters, NOW(), NOW() + INTERVAL '24 hours', 0)
        """), {
            "key": cache_key,
            "asins": json.dumps(["B08N5WRWNW"]),
            "filters": json.dumps({"test": "hit_count"})
        })
        conn.commit()

        print(f"  - Entree cache creee: {cache_key}")
        print(f"  - hit_count initial: 0")
        print()

        # Simuler 5 cache hits
        hit_counts = []
        for i in range(5):
            # Lire le cache (simuler cache hit)
            result = conn.execute(text("""
                SELECT hit_count FROM product_discovery_cache
                WHERE cache_key = :key
            """), {"key": cache_key})
            current_hit = result.scalar()

            # Incrémenter hit_count
            conn.execute(text("""
                UPDATE product_discovery_cache
                SET hit_count = hit_count + 1
                WHERE cache_key = :key
            """), {"key": cache_key})
            conn.commit()

            # Vérifier nouvelle valeur
            result = conn.execute(text("""
                SELECT hit_count FROM product_discovery_cache
                WHERE cache_key = :key
            """), {"key": cache_key})
            new_hit = result.scalar()

            hit_counts.append(new_hit)
            print(f"  - Cache hit #{i+1}: hit_count = {new_hit}")

            # Pause courte entre hits
            time.sleep(0.1)

        print()

        # Vérifier progression hit_count: [1, 2, 3, 4, 5]
        expected = list(range(1, 6))
        success = (hit_counts == expected)

        if success:
            print(f"  RESULTAT: [OK] hit_count incremente correctement: {hit_counts}")
        else:
            print(f"  RESULTAT: [FAIL] hit_count incorrect: {hit_counts} (attendu: {expected})")

        # Cleanup
        conn.execute(text("DELETE FROM product_discovery_cache WHERE cache_key = 'test_hit_count'"))
        conn.commit()

        print()
        return success


# =============================================================================
# TEST 3: CONCURRENT ACCESS
# =============================================================================

def insert_cache_entry(thread_id, category):
    """
    Fonction exécutée par chaque thread pour tester accès concurrent.
    """
    try:
        engine_local = create_engine(DATABASE_URL)
        with engine_local.connect() as conn:
            cache_key = f"test_concurrent_thread{thread_id}_cat{category}"

            # Insérer entrée cache
            conn.execute(text("""
                INSERT INTO product_discovery_cache
                (cache_key, asins, filters_applied, created_at, expires_at, hit_count)
                VALUES (:key, :asins, :filters, NOW(), NOW() + INTERVAL '24 hours', 0)
            """), {
                "key": cache_key,
                "asins": json.dumps([f"ASIN_THREAD{thread_id}"]),
                "filters": json.dumps({"category": category, "thread": thread_id})
            })
            conn.commit()

            # Lire immédiatement
            result = conn.execute(text("""
                SELECT cache_key, hit_count FROM product_discovery_cache
                WHERE cache_key = :key
            """), {"key": cache_key})
            row = result.fetchone()

            # Incrémenter hit_count
            conn.execute(text("""
                UPDATE product_discovery_cache
                SET hit_count = hit_count + 1
                WHERE cache_key = :key
            """), {"key": cache_key})
            conn.commit()

            return {
                "thread_id": thread_id,
                "category": category,
                "cache_key": cache_key,
                "success": True,
                "error": None
            }

    except Exception as e:
        return {
            "thread_id": thread_id,
            "category": category,
            "cache_key": f"test_concurrent_thread{thread_id}_cat{category}",
            "success": False,
            "error": str(e)
        }


def test_concurrent_access():
    """
    Test 3: Valider que plusieurs threads peuvent accéder simultanément
    aux tables cache sans deadlock ni corruption de données.
    """
    print("[TEST 3] CONCURRENT ACCESS")
    print("-" * 70)

    # Nettoyer d'abord
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM product_discovery_cache WHERE cache_key LIKE 'test_concurrent_%'"))
        conn.commit()

    print("  - Lancement de 10 threads concurrents...")
    print("  - Chaque thread insere + lit + update une entree cache")
    print()

    # Lancer 10 threads simultanés avec catégories différentes
    num_threads = 10
    results = []

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [
            executor.submit(insert_cache_entry, thread_id, category)
            for thread_id, category in enumerate(range(1000, 1000 + num_threads))
        ]

        for future in as_completed(futures):
            result = future.result()
            results.append(result)

            if result["success"]:
                print(f"  [OK] Thread {result['thread_id']} - Categorie {result['category']}")
            else:
                print(f"  [FAIL] Thread {result['thread_id']} - Erreur: {result['error']}")

    elapsed = time.time() - start_time
    print()
    print(f"  - Temps execution: {elapsed:.2f}s")
    print()

    # Compter succès/échecs
    successes = sum(1 for r in results if r["success"])
    failures = sum(1 for r in results if not r["success"])

    print(f"  - Operations reussies: {successes}/{num_threads}")
    print(f"  - Operations echouees: {failures}/{num_threads}")
    print()

    # Vérifier intégrité des données
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) FROM product_discovery_cache
            WHERE cache_key LIKE 'test_concurrent_%'
        """))
        inserted_count = result.scalar()

        result = conn.execute(text("""
            SELECT cache_key, hit_count FROM product_discovery_cache
            WHERE cache_key LIKE 'test_concurrent_%'
            ORDER BY cache_key
        """))
        rows = result.fetchall()

        print(f"  - Entrees inserees dans la DB: {inserted_count}")
        print(f"  - hit_count attendu: 1 (apres UPDATE)")
        print()

        for i, row in enumerate(rows[:5]):  # Afficher les 5 premières
            print(f"    * {row[0]}: hit_count={row[1]}")
        if len(rows) > 5:
            print(f"    ... et {len(rows) - 5} autres entrees")
        print()

        # Cleanup
        conn.execute(text("DELETE FROM product_discovery_cache WHERE cache_key LIKE 'test_concurrent_%'"))
        conn.commit()

    # Validation
    success = (failures == 0 and inserted_count == num_threads)

    if success:
        print("  RESULTAT: [OK] Acces concurrent sans deadlock")
    else:
        print("  RESULTAT: [FAIL] Problemes detectes lors acces concurrent")

    print()
    return success


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    results = {}

    try:
        # Test 1: TTL Expiration
        results["ttl_expiration"] = test_ttl_expiration()

        # Test 2: Cache Hit Increment
        results["cache_hit"] = test_cache_hit_increment()

        # Test 3: Concurrent Access
        results["concurrent"] = test_concurrent_access()

    except Exception as e:
        print(f"ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()

    # Résumé final
    print("=" * 70)
    print("RESUME DES TESTS")
    print("=" * 70)
    print()

    for test_name, success in results.items():
        status = "[OK]" if success else "[FAIL]"
        print(f"  {status} Test {test_name}")

    print()

    total = len(results)
    passed = sum(1 for s in results.values() if s)

    print(f"  Tests reussis: {passed}/{total}")
    print()

    if passed == total:
        print("  [SUCCESS] Tous les tests de robustesse passent!")
    else:
        print("  [WARNING] Certains tests ont echoue - verification necessaire")

    print("=" * 70)
