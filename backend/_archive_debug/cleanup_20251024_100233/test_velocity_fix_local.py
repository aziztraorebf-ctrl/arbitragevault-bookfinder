#!/usr/bin/env python3
"""
Test local du fix velocity sans passer par Render.
Simule le calcul avec vraies données BSR.
"""
import statistics
from typing import List, Tuple

# Simulation données BSR non triées (comme dans CSV Keepa)
# Prenons les valeurs réelles du MCP Keepa mais dans un ordre désordonné
bsr_data_unsorted: List[Tuple[int, float]] = [
    (7746100, 39706.0),
    (7745840, 33253.0),  # Plus ancien mais vient après
    (7746732, 41140.0),
    (7746290, 36400.0),
    (7747040, 34654.0),
    (7789042, 44652.0),  # Plus récent
    (7785442, 24377.0),
    (7784924, 25666.0),
    (7784722, 25665.0),
]

print("="*80)
print("  TEST LOCAL - FIX VELOCITY SCORE")
print("="*80)

print("\n[DONNÉES NON TRIÉES (ordre CSV)]")
for i, (ts, bsr) in enumerate(bsr_data_unsorted[:5]):
    print(f"  {i+1}. Timestamp: {ts} | BSR: {bsr:.0f}")
print("  ...")
for i, (ts, bsr) in enumerate(bsr_data_unsorted[-2:]):
    idx = len(bsr_data_unsorted) - 2 + i + 1
    print(f"  {idx}. Timestamp: {ts} | BSR: {bsr:.0f}")

# AVANT FIX: Sans tri
print("\n[AVANT FIX - SANS TRI]")
bsr_values_unsorted = [bsr for _, bsr in bsr_data_unsorted]
first_7_unsorted = bsr_values_unsorted[:7]
last_7_unsorted = bsr_values_unsorted[-7:]

older_avg_bad = statistics.mean(first_7_unsorted)
recent_avg_bad = statistics.mean(last_7_unsorted)
improvement_bad = (older_avg_bad - recent_avg_bad) / older_avg_bad if older_avg_bad > 0 else 0
velocity_bad = max(0.0, min(1.0, 0.5 + (improvement_bad * 0.5)))

print(f"  7 premiers (indices 0-6): {[int(b) for b in first_7_unsorted]}")
print(f"  Moyenne: {older_avg_bad:.2f}")
print(f"  7 derniers (indices -7 à -1): {[int(b) for b in last_7_unsorted]}")
print(f"  Moyenne: {recent_avg_bad:.2f}")
print(f"  Improvement: {improvement_bad:.6f} ({improvement_bad * 100:.2f}%)")
print(f"  Velocity Score: {int(velocity_bad * 100)}")

# APRÈS FIX: Avec tri
print("\n[APRÈS FIX - AVEC TRI CHRONOLOGIQUE]")
bsr_data_sorted = sorted(bsr_data_unsorted, key=lambda x: x[0])  # Trier par timestamp

print("  Données triées (ancien → récent):")
for i, (ts, bsr) in enumerate(bsr_data_sorted[:3]):
    print(f"    {i+1}. Timestamp: {ts} | BSR: {bsr:.0f} (ancien)")
print("    ...")
for i, (ts, bsr) in enumerate(bsr_data_sorted[-3:]):
    idx = len(bsr_data_sorted) - 3 + i + 1
    print(f"    {idx}. Timestamp: {ts} | BSR: {bsr:.0f} (récent)")

bsr_values_sorted = [bsr for _, bsr in bsr_data_sorted]
first_7_sorted = bsr_values_sorted[:7]
last_7_sorted = bsr_values_sorted[-7:]

older_avg_good = statistics.mean(first_7_sorted)
recent_avg_good = statistics.mean(last_7_sorted)
improvement_good = (older_avg_good - recent_avg_good) / older_avg_good if older_avg_good > 0 else 0
velocity_good = max(0.0, min(1.0, 0.5 + (improvement_good * 0.5)))

print(f"\n  7 PLUS ANCIENS (après tri): {[int(b) for b in first_7_sorted]}")
print(f"  Moyenne anciens: {older_avg_good:.2f}")
print(f"  7 PLUS RÉCENTS (après tri): {[int(b) for b in last_7_sorted]}")
print(f"  Moyenne récents: {recent_avg_good:.2f}")
print(f"  Improvement: {improvement_good:.6f} ({improvement_good * 100:.2f}%)")
print(f"  Velocity Score: {int(velocity_good * 100)}")

print("\n[RÉSULTAT]")
if int(velocity_good * 100) > int(velocity_bad * 100):
    print(f"  ✅ FIX FONCTIONNE:")
    print(f"     Avant: {int(velocity_bad * 100)} (incorrect)")
    print(f"     Après: {int(velocity_good * 100)} (correct)")
elif int(velocity_good * 100) == int(velocity_bad * 100):
    print(f"  ⚠️  SCORES IDENTIQUES: {int(velocity_good * 100)}")
    print(f"     Le tri n'a pas changé le résultat pour ces données")
else:
    print(f"  ❌ PROBLÈME:")
    print(f"     Avant: {int(velocity_bad * 100)}")
    print(f"     Après: {int(velocity_good * 100)}")

print("\n" + "="*80)
