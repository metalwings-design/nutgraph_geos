"""
02_build_final_csv.py
---------------------
Combines manual visual labels, primary classification, Dynamic World,
and Copernicus LC100 into the required cell-level comparative CSV.
"""

import os
import pandas as pd
import numpy as np

# 1. Load EDA statistics
eda_path = "outputs/eda_cell_statistics.csv"
df = pd.read_csv(eda_path)

# 2. Add the 6 manual visual labels
manual_labels = {
    "C01": {"visual_label": "Scrub / Shrubland", "visual_cue": "Low-contrast diffuse texture, sparse thorny scrub", "confidence": "Medium"},
    "C03": {"visual_label": "Bare Ground",        "visual_cue": "High albedo, uniform bare sandy soil",            "confidence": "High"},
    "C04": {"visual_label": "Cropland",           "visual_cue": "Rectilinear field parcel boundary",              "confidence": "High"},
    "C07": {"visual_label": "Mixed (Bare/Scrub)", "visual_cue": "Transitional terrain between bare soil and scrub","confidence": "Low"},
    "C09": {"visual_label": "Scrub / Shrubland", "visual_cue": "Patchy surface roughness, grazing commons scrub", "confidence": "Medium"},
    "C11": {"visual_label": "Bare Ground",        "visual_cue": "Monolithic high albedo with drainage fringe",     "confidence": "Medium"}
}

df["visual_label"] = df["cell_id"].apply(lambda x: manual_labels.get(x, {}).get("visual_label", np.nan))
df["visual_cue"] = df["cell_id"].apply(lambda x: manual_labels.get(x, {}).get("visual_cue", np.nan))
df["visual_confidence"] = df["cell_id"].apply(lambda x: manual_labels.get(x, {}).get("confidence", np.nan))

# 3. Primary Classifier (Index-based Spectral Rule on 10m Bands)
# Rule:
# If ndvi_max > 0.65 and ndvi_mean > 0.17 -> Cropland
# Else If ndvi_max > 0.42 and ndbi_mean < 0.10 -> Scrub / Shrubland
# Else -> Bare Ground
def primary_classifier(row):
    if row["ndvi_max"] > 0.65 and row["ndvi_mean"] > 0.17:
        return "Cropland"
    elif row["ndvi_max"] > 0.42 and row["ndbi_mean"] < 0.10:
        return "Scrub / Shrubland"
    else:
        return "Bare Ground"

df["primary_label"] = df.apply(primary_classifier, axis=1)

# Uncertainty heuristic: Higher variance or proximity to class decision boundaries
df["primary_uncertainty"] = np.where(df["ndvi_std"] > 0.08, "High",
                            np.where(df["ndvi_std"] > 0.045, "Medium", "Low"))

# 4. Harmonize Comparator Labels via Crosswalk
# Dynamic World Harmonization:
# 'Bare' -> 'Bare Ground', 'Crops' -> 'Cropland', 'Shrub/Scrub' -> 'Scrub / Shrubland'
dw_crosswalk = {
    "Bare": "Bare Ground",
    "Crops": "Cropland",
    "Shrub/Scrub": "Scrub / Shrubland",
    "Grass": "Scrub / Shrubland",
    "Built": "Built-up"
}
df["dw_harmonized"] = df["dw_2019_mode"].map(dw_crosswalk).fillna(df["dw_2019_mode"])

# Copernicus LC100 Harmonization:
# 'Shrubland' -> 'Scrub / Shrubland', 'Bare / Sparse vegetation' -> 'Bare Ground', 'Cultivated / Agriculture' -> 'Cropland'
cop_crosswalk = {
    "Shrubland": "Scrub / Shrubland",
    "Bare / Sparse vegetation": "Bare Ground",
    "Cultivated / Agriculture": "Cropland",
    "Herbaceous vegetation": "Scrub / Shrubland"
}
df["copernicus_harmonized"] = df["copernicus_2019_mode"].map(cop_crosswalk).fillna(df["copernicus_2019_mode"])

# 5. Select & organize final columns
output_cols = [
    "cell_id", "grid_row", "grid_col", "pixel_count",
    "visual_label", "visual_cue", "visual_confidence",
    "primary_label", "primary_uncertainty",
    "dw_2019_mode", "dw_harmonized", "dw_mode_share_pct",
    "copernicus_2019_mode", "copernicus_harmonized", "cop_mode_share_pct",
    "ndvi_mean", "ndvi_max", "ndbi_mean"
]

out_csv = "outputs/cell_level_classification.csv"
df[output_cols].to_csv(out_csv, index=False)
print(f"Generated final comparative CSV: {out_csv}")