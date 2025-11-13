"""Analyse BSR de Learning Python pour comprendre le trend bizarre."""

bsr_csv = [7778944,6577,7779576,6584,7779646,6579,7779716,6571,7779740,6576,7779810,6574,7779950,6563,7780020,6582,7780120,6581,7780184,6576,7780228,6554,7780298,6583,7780356,6580,7780426,6573,7780496,6580,7780512,6577,7780582,6581,7780652,6577,7780722,6582,7780776,6578,7780846,6570,7781236,6564,7781306,6578,7781376,6579,7781446,6573,7781516,6555,7781586,6543,7781658,6578,7781734,6580,7781804,6581,7782748,6165,7782814,6578,7782954,6584,7783024,6572,7783094,6555,7783174,6574,7783244,6549,7783314,6574,7783376,6579,7783446,6570,7784882,6556,7784952,6555,7785022,6573,7785408,6566,7785478,6580,7785524,6574,7785598,6557,7785880,6583,7785950,6577,7785984,6560,7786052,6579,7786122,6580,7786192,6572,7787064,6571,7787134,6580,7787204,6581,7787274,6572,7787344,6580,7787414,6583,7787494,6561,7787564,6579,7787634,6577,7787704,6567,7787768,6582,7787838,6580,7787908,6574,7787978,6580,7788008,6578,7788042,6574,7788112,6576,7788148,6579,7788286,6566,7788356,6575,7788372,6584,7788442,6570,7788498,6575,7788506,6572,7788576,6558,7788646,6572,7788680,6559,7788750,6572,7788756,6578]

print("="*80)
print("ANALYSE BSR - Learning Python (1449355730)")
print("="*80)

# Parse CSV[3] format
bsr_history = []
for i in range(0, len(bsr_csv) - 1, 2):
    timestamp = bsr_csv[i]
    bsr = bsr_csv[i + 1]
    if bsr and bsr > 0:
        bsr_history.append((timestamp, bsr))

print(f"\nTotal BSR data points: {len(bsr_history)}")

# Vérifier ordre chronologique
timestamps = [ts for ts, _ in bsr_history]
is_sorted = all(timestamps[i] <= timestamps[i+1] for i in range(len(timestamps)-1))
print(f"Données triées chronologiquement: {is_sorted}")

# SANS TRI (comme avant le fix)
print("\n" + "-"*80)
print("CALCUL SANS TRI (ordre CSV brut):")
print("-"*80)
bsr_values_unsorted = [bsr for _, bsr in bsr_history]
older_avg_unsorted = sum(bsr_values_unsorted[:7]) / 7
recent_avg_unsorted = sum(bsr_values_unsorted[-7:]) / 7

print(f"7 premiers (indices 0-6): {bsr_values_unsorted[:7]}")
print(f"  Moyenne: {older_avg_unsorted:.2f}")
print(f"7 derniers (indices -7 à -1): {bsr_values_unsorted[-7:]}")
print(f"  Moyenne: {recent_avg_unsorted:.2f}")

improvement_unsorted = (older_avg_unsorted - recent_avg_unsorted) / older_avg_unsorted
print(f"  Improvement: {improvement_unsorted:.4f} ({improvement_unsorted * 100:.2f}%)")

velocity_raw_unsorted = 0.5 + (improvement_unsorted * 0.5)
velocity_raw_unsorted = max(0.0, min(1.0, velocity_raw_unsorted))
velocity_score_unsorted = int(velocity_raw_unsorted * 100)
print(f"  Velocity Score: {velocity_score_unsorted}")

# AVEC TRI CHRONOLOGIQUE (après le fix)
print("\n" + "-"*80)
print("CALCUL AVEC TRI CHRONOLOGIQUE (fix appliqué):")
print("-"*80)
sorted_bsr = sorted(bsr_history, key=lambda x: x[0])
bsr_values_sorted = [bsr for _, bsr in sorted_bsr]

older_avg_sorted = sum(bsr_values_sorted[:7]) / 7
recent_avg_sorted = sum(bsr_values_sorted[-7:]) / 7

print(f"7 plus anciens (chronologiquement): {bsr_values_sorted[:7]}")
print(f"  Timestamps: {[ts for ts, _ in sorted_bsr[:7]]}")
print(f"  Moyenne: {older_avg_sorted:.2f}")

print(f"7 plus récents (chronologiquement): {bsr_values_sorted[-7:]}")
print(f"  Timestamps: {[ts for ts, _ in sorted_bsr[-7:]]}")
print(f"  Moyenne: {recent_avg_sorted:.2f}")

improvement_sorted = (older_avg_sorted - recent_avg_sorted) / older_avg_sorted
print(f"  Improvement: {improvement_sorted:.4f} ({improvement_sorted * 100:.2f}%)")

velocity_raw_sorted = 0.5 + (improvement_sorted * 0.5)
velocity_raw_sorted = max(0.0, min(1.0, velocity_raw_sorted))
velocity_score_sorted = int(velocity_raw_sorted * 100)
print(f"  Velocity Score: {velocity_score_sorted}")

# Comparaison
print("\n" + "="*80)
print("COMPARAISON:")
print("="*80)
print(f"Sans tri (buggy):  velocity = {velocity_score_unsorted}, trend = {improvement_unsorted * 100:.2f}%")
print(f"Avec tri (fixed):  velocity = {velocity_score_sorted}, trend = {improvement_sorted * 100:.2f}%")
print(f"Différence:        {velocity_score_sorted - velocity_score_unsorted} points")

if is_sorted:
    print("\n⚠️  Les données sont DÉJÀ triées chronologiquement dans le CSV!")
    print("    Le tri ne devrait pas changer le résultat.")
else:
    print("\n✅ Les données ne sont PAS triées chronologiquement.")
    print("   Le fix de tri est nécessaire.")
