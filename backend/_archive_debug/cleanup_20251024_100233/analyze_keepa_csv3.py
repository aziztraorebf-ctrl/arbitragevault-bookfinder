#!/usr/bin/env python3
"""
Analyser le CSV[3] (BSR history) des données brutes Keepa pour identifier le bug velocity_score = 0.
"""
import json
import statistics

# Données du MCP Keepa pour ASIN 0316769487 (Catcher in the Rye)
keepa_response = """
{"processingTimeInMs":7,"products":[{"csv":[[7480170,703],[7730192,300,7758356,399],[7737808,133,7747040,135,7751540,133,7751730,135,7751920,133,7752068,135,7752802,133,7752852,135,7753676,133,7753866,135,7754740,133,7754780,135,7755562,133,7755732,135,7755956,141,7757386,133,7757576,141,7758172,133,7758548,141,7759252,133,7759882,135,7760154,133,7760344,122,7760534,141,7760908,131,7761132,141,7761492,131,7761756,141,7762196,131,7762402,140,7762572,131,7762928,141,7763122,131,7763312,122,7763518,141,7764562,131,7764752,141,7765092,131,7765590,141,7765812,131,7766002,141,7766192,131,7766444,141,7766892,133,7767054,131,7767128,122,7767402,141,7767782,130,7767832,131,7767972,130,7781120,100,7781292,130],[7745840,33253,7746100,39706,7746290,36400,7746562,36398,7746732,41140,7747040,34654,7747282,34651,7747490,34652,7747680,34651,7749218,31685,7749404,31680,7749544,36004,7749700,36024,7749890,34735,7750292,35017,7750690,32904,7750882,32908,7751016,34467,7751242,31946,7751412,31944,7751540,31943,7751730,35479,7751920,35478,7752068,35570,7752322,24548,7752492,24549,7752802,26749,7753080,26744,7753270,29218,7753460,23469,7753866,26155,7754096,26152,7754286,26081,7754548,27437,7754740,27438,7754970,27564,7755202,26897,7755372,26898,7755732,26679,7756146,26800,7756342,26794,7756642,25605,7756980,27142,7757170,24811,7757386,24810,7757576,23935,7757830,23793,7757982,23788,7758172,22260,7758356,22262,7758548,22783,7758682,22784,7758872,16665,7759062,16664,7759252,16637,7759522,16635,7759692,18799,7760052,19336,7760344,19145,7760772,20807,7760908,20809,7761132,20807,7761492,23229,7761756,22875,7762006,22874,7762196,24516,7762402,24515,7762572,29408,7762762,31831,7762928,31830,7763122,31831,7763312,29019,7763660,29976,7764012,32637,7764372,31435,7764752,30804,7764942,30802,7765092,33399,7765328,36253,7765452,36254,7765590,36255,7765716,35476,7766002,35474,7766192,33606,7766444,30483,7766722,30482,7766864,31121,7767054,31122,7767252,34255,7767402,34250,7767592,39192,7767972,33111,7768232,29980,7768522,29979,7768692,26114,7768882,26112,7769072,26087,7769412,25453,7769772,22760,7770132,24375,7770322,23760,7770552,23757,7770720,25508,7770928,25509,7771118,25994,7771572,25949,7771952,25947,7772142,25434,7772652,28986,7773012,28504,7773248,26317,7773438,26316,7773564,29492,7773938,30467,7774092,30463,7774438,32968,7774832,31942,7775170,30225,7775356,34139,7775532,34143,7775722,34142,7775892,29442,7776028,29441,7776218,32410,7776484,33670,7776800,33667,7776972,25369,7777162,25975,7777332,25977,7777468,25976,7777658,29062,7778038,28815,7778602,33729,7778780,33726,7778970,25646,7779314,25647,7779492,28060,7779642,28059,7779832,27144,7780212,22746,7780592,22743,7780720,22738,7780910,22078,7781292,24218,7781574,26406,7781842,26407,7782032,27014,7782392,28861,7782582,31678,7782732,31680,7782922,31677,7783092,30561,7783220,30564,7783410,30150,7783600,30151,7783790,30994,7784020,30995,7784362,29679,7784532,28869,7784722,25665,7784924,25666,7785442,24377,7789042,44652]]}]}
"""

data = json.loads(keepa_response)
csv = data["products"][0]["csv"]

# CSV[3] = BSR history (SALES rank)
bsr_csv = csv[3]

print(f"{'='*80}")
print(f"  ANALYSE CSV[3] - BSR HISTORY (ASIN 0316769487)")
print(f"{'='*80}\n")

print(f"[FORMAT CSV KEEPA]")
print(f"  Format: [timestamp1, value1, timestamp2, value2, ...]")
print(f"  Timestamps: Minutes depuis epoch Keepa (21 Oct 2000)")
print(f"  Total éléments CSV: {len(bsr_csv)}")
print(f"  Total paires (timestamp, BSR): {len(bsr_csv) // 2}\n")

# Parser en tuples
bsr_history = []
for i in range(0, len(bsr_csv) - 1, 2):
    timestamp_minutes = bsr_csv[i]
    bsr_value = bsr_csv[i + 1]
    if bsr_value and bsr_value > 0:
        bsr_history.append((timestamp_minutes, bsr_value))

print(f"[DONNÉES PARSÉES]")
print(f"  Total BSR points valides: {len(bsr_history)}\n")

# Afficher premiers 10
print(f"[10 PREMIERS ÉLÉMENTS]")
for i, (ts, bsr) in enumerate(bsr_history[:10]):
    print(f"  {i+1}. Timestamp: {ts:>10} | BSR: {bsr:>6}")

# Afficher derniers 10
print(f"\n[10 DERNIERS ÉLÉMENTS]")
for i, (ts, bsr) in enumerate(bsr_history[-10:]):
    idx = len(bsr_history) - 10 + i + 1
    print(f"  {idx}. Timestamp: {ts:>10} | BSR: {bsr:>6}")

# Vérifier ordre chronologique
print(f"\n[ORDRE CHRONOLOGIQUE]")
timestamps = [ts for ts, _ in bsr_history]
is_ascending = all(timestamps[i] <= timestamps[i+1] for i in range(len(timestamps)-1))
is_descending = all(timestamps[i] >= timestamps[i+1] for i in range(len(timestamps)-1))

if is_ascending:
    print(f"  ✅ Ordre ASCENDANT (ancien → récent)")
elif is_descending:
    print(f"  ⚠️  Ordre DESCENDANT (récent → ancien)")
else:
    print(f"  ❌ Ordre NON TRIÉ (mixte)")

print(f"  Premier timestamp: {timestamps[0]}")
print(f"  Dernier timestamp: {timestamps[-1]}")
print(f"  Delta: {timestamps[-1] - timestamps[0]} minutes ({(timestamps[-1] - timestamps[0]) / 1440:.1f} jours)")

# ANALYSE VELOCITY - REPRODUIRE LE CODE ACTUEL
print(f"\n{'='*80}")
print(f"  REPRODUCTION DU BUG - LOGIQUE ACTUELLE")
print(f"{'='*80}\n")

bsr_values = [bsr for _, bsr in bsr_history]

if len(bsr_values) >= 14:
    # Code actuel (SANS TRI)
    first_7_bsr = bsr_values[:7]
    last_7_bsr = bsr_values[-7:]

    older_avg = statistics.mean(first_7_bsr)
    recent_avg = statistics.mean(last_7_bsr)

    improvement = (older_avg - recent_avg) / older_avg if older_avg > 0 else 0
    velocity_raw = 0.5 + (improvement * 0.5)
    velocity_raw = max(0.0, min(1.0, velocity_raw))
    velocity_normalized = int(velocity_raw * 100)

    print(f"[SANS TRI - CODE ACTUEL]")
    print(f"  7 PREMIERS BSR (indices 0-6):")
    print(f"    Valeurs: {first_7_bsr}")
    print(f"    Moyenne (older_avg): {older_avg:.2f}")

    print(f"\n  7 DERNIERS BSR (indices -7 à -1):")
    print(f"    Valeurs: {last_7_bsr}")
    print(f"    Moyenne (recent_avg): {recent_avg:.2f}")

    print(f"\n  Calcul Improvement:")
    print(f"    Formula: (older_avg - recent_avg) / older_avg")
    print(f"    ({older_avg:.2f} - {recent_avg:.2f}) / {older_avg:.2f}")
    print(f"    = {improvement:.6f}")
    print(f"    = {improvement * 100:.2f}%")

    print(f"\n  Velocity Score:")
    print(f"    Raw (0-1): {velocity_raw:.4f}")
    print(f"    Normalized (0-100): {velocity_normalized}")

    # Interprétation
    print(f"\n[INTERPRÉTATION]")
    if is_ascending:
        print(f"  ✅ Ordre ascendant confirmé:")
        print(f"     → Premiers (indices 0-6) = ANCIENS")
        print(f"     → Derniers (indices -7 à -1) = RÉCENTS")

        if older_avg < recent_avg:
            print(f"  ❌ PROBLÈME DÉTECTÉ:")
            print(f"     → BSR ancien ({older_avg:.0f}) < BSR récent ({recent_avg:.0f})")
            print(f"     → Rank s'est DÉGRADÉ (augmenté)")
            print(f"     → Improvement négatif = velocity = 0")
            print(f"  ✅ LOGIQUE CALCUL CORRECTE mais produit peu performant")
        else:
            print(f"  ✅ BSR s'est amélioré (baissé)")
            print(f"     → Improvement positif")
            print(f"     → Velocity > 50")

print(f"\n{'='*80}")
print(f"  CONCLUSION")
print(f"{'='*80}\n")

if is_ascending:
    print("✅ FORMAT CSV KEEPA: Timestamps ordre ascendant (ancien → récent)")
    print("✅ PARSER FONCTIONNE: bsr_history extrait correctement")
    print("✅ LOGIQUE CALCUL: Correcte (older = premiers, recent = derniers)")

    if older_avg < recent_avg:
        print("\n⚠️  RÉSULTAT: Velocity = 0 car Catcher in the Rye a un BSR qui se dégrade")
        print("   Ce n'est PAS un bug, c'est le comportement normal!")
        print(f"   BSR moyen ancien: {older_avg:.0f} (meilleur rank)")
        print(f"   BSR moyen récent: {recent_avg:.0f} (pire rank)")
        print("   Le livre se vend MOINS BIEN maintenant qu'avant")
else:
    print("❌ ORDRE NON ASCENDANT DÉTECTÉ!")
    print("   Le code doit TRIER par timestamp avant calcul!")
