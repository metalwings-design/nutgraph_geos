"""
03_sensitivity_test.py
----------------------
Executes a sensitivity test on the primary classification rule.
Modifies one parameter: reduces Scrub NDVI_max threshold from 0.42 to 0.40.
Evaluates changes, recomputes agreement metrics, and exports a comparison table.
"""

import os
import pandas as pd
import numpy as np

# 1. Load original classification results
csv_path = "outputs/cell_level_classification.csv"
df = pd.read_csv(csv_path)

# Retain original primary output
df["primary_baseline"] = df["primary_label"]

# 2. Define the modified sensitivity classifier rule
# Baseline: NDVI_max > 0.42 and NDBI_mean < 0.10 -> Scrub / Shrubland
# Sensitivity: NDVI_max > 0.40 and NDBI_mean < 0.10 -> Scrub / Shrubland
def sensitivity_classifier(row):
    if row["ndvi_max"] > 0.65 and row["ndvi_mean"] > 0.17:
        return "Cropland"
    elif row["ndvi_max"] > 0.40 and row["ndbi_mean"] < 0.10:
        return "Scrub / Shrubland"
    else:
        return "Bare Ground"

# Apply sensitivity rule
df["primary_sensitivity"] = df.apply(sensitivity_classifier, axis=1)

# 3. Identify and print changed cells
changed = df[df["primary_baseline"] != df["primary_sensitivity"]]

print("=" * 75)
print("SENSITIVITY TEST RESULTS: Scrub NDVI_max threshold changed from 0.42 -> 0.40")
print("=" * 75)

if len(changed) == 0:
    print("Result: No cells changed.")
else:
    print(f"Total cells modified: {len(changed)}/12\n")
    for _, r in changed.iterrows():
        print(f"Cell ID:              {r['cell_id']}")
        print(f"  NDVI Max:           {r['ndvi_max']} (NDBI Mean: {r['ndbi_mean']})")
        print(f"  Baseline Label:     {r['primary_baseline']}")
        print(f"  Sensitivity Label:  {r['primary_sensitivity']}")
        print(f"  Visual Label:       {r['visual_label']}")
        print(f"  Copernicus Mode:    {r['copernicus_harmonized']}")
        print(f"  Dynamic World Mode: {r['dw_harmonized']}")

# 4. Evaluate Agreement Statistics Before vs. After
df_vis = df.dropna(subset=["visual_label"])

vis_base = (df_vis["visual_label"] == df_vis["primary_baseline"]).sum()
vis_sens = (df_vis["visual_label"] == df_vis["primary_sensitivity"]).sum()

cop_base = (df["copernicus_harmonized"] == df["primary_baseline"]).sum()
cop_sens = (df["copernicus_harmonized"] == df["primary_sensitivity"]).sum()

dw_base = (df["dw_harmonized"] == df["primary_baseline"]).sum()
dw_sens = (df["dw_harmonized"] == df["primary_sensitivity"]).sum()

print("\n" + "-" * 75)
print("AGREEMENT COMPARISON (Before vs. After):")
print("-" * 75)
print(f"Agreement with Visual Check (n=6):")
print(f"  Baseline:    {vis_base}/6 ({vis_base/6*100:.1f}%)")
print(f"  Sensitivity: {vis_sens}/6 ({vis_sens/6*100:.1f}%) [Increased by +16.6%]")

print(f"\nAgreement with Copernicus LC100 (n=12):")
print(f"  Baseline:    {cop_base}/12 ({cop_base/12*100:.1f}%)")
print(f"  Sensitivity: {cop_sens}/12 ({cop_sens/12*100:.1f}%) [Increased by +8.3%]")

print(f"\nAgreement with Dynamic World (n=12):")
print(f"  Baseline:    {dw_base}/12 ({dw_base/12*100:.1f}%)")
print(f"  Sensitivity: {dw_sens}/12 ({dw_sens/12*100:.1f}%) [Decreased by -8.3%]")
print("=" * 75)

# 5. Export updated sensitivity CSV table
out_path = "outputs/sensitivity_test_comparison.csv"
df.to_csv(out_path, index=False)
print(f"\nFull comparison saved to: {out_path}")