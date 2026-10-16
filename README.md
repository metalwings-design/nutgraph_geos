# Small Land Cover Classification — Nagnechinagar, Rajasthan

This repository contains the code, data, and analysis outputs for **Question 1** of the **Geospatial and Machine Learning Researcher Technical Assessment**.

The project evaluates land cover across a ~3.90 km² arid landscape in **Nagnechinagar, Rajasthan** (site of a solar park development, grazing commons, and rainfed agriculture) partitioned into a fixed 3×4 grid of 12 non-overlapping cells (~500 m × 500 m each).

---

## 1. Study Area & Data Products (2019)

- **Location**: Nagnechinagar, Rajasthan, India  
  - Bounding Box: `72.08038° E – 72.10166° E, 26.90109° N – 26.91808° N` (~3.90 km²)
  - Valid Data Coverage: 100% across all 12 cells (no cloud/shadow nodata dropout)
- **Primary Imagery**: Sentinel-2 Level-2A Harmonized Surface Reflectance (10 m)
  - Time window: October 15 – November 30, 2019 (cloud/shadow screened via SCL & QA60, temporal median composite)
- **Comparator 1**: Google Dynamic World V1 (10 m)
  - S2-derived near-real-time model, mode composite over the identical window (Oct 15 – Nov 30, 2019)
- **Comparator 2**: Copernicus Global Land Cover CGLS-LC100 Collection 3 (100 m)
  - Annual discrete classification layer representing the full calendar year 2019

---

## 2. Repository Structure

```text
nutgraph_geos/
│
├── data/
│   ├── raw/
│   │   ├── sentinel2_2019_rgb_visual_10m.tif     # Visual RGB composite (10m)
│   │   ├── sentinel2_2019_multispectral_10m.tif  # 6 bands + NDVI + NDBI (10m)
│   │   ├── dynamic_world_2019.tif                # Dynamic World mode labels (10m)
│   │   ├── copernicus_lc100_2019.tif             # Copernicus LC100 discrete class (100m)
│   │   └── study_area_boundary.geojson           # AOI bounding polygon
│   │
│   └── processed/
│       ├── grid_12_cells.geojson                 # 3x4 grid polygon file with cell IDs (C01–C12)
│       └── chips/                                # 12 RGB PNG chips (C01.png to C12.png)
│
├── outputs/
│   ├── cell_level_classification.csv             # Full 12-cell comparison table
│   ├── sensitivity_test_comparison.csv           # Baseline vs. sensitivity test results
│   ├── eda_cell_statistics.csv                   # Spectral indices & comparator statistics
│   └── sentinel2_exploratory_analysis.png        # 6-panel visual diagnostic figure
│
├── scripts/
│   ├── 00_eda_sentinel2.py                       # Exploratory analysis & multi-sensor diagnostics
│   ├── 01_make_grid_and_chips.py                 # Slices AOI into 3x4 grid & exports 12 PNG chips
│   ├── 02_build_final_csv.py                     # Primary spectral classification & comparators join
│   └── 03_sensitivity_test.py                    # Evaluates threshold sensitivity on C01/C04
│
├── requirements.txt                              # Python environment dependencies
└── README.md                                     # Project documentation and reproducibility guide
```

---

## 3. Class Crosswalk & Schema Harmonization

To enable direct comparison across disparate product resolutions and taxonomies, labels are harmonized into a 3-class target schema:

| Target Class | Dynamic World (10 m) | Copernicus CGLS-LC100 (100 m) | Primary Classifier Rule (10 m) |
| :--- | :--- | :--- | :--- |
| **Bare Ground** | `Bare` (code 7) | `Bare / Sparse vegetation` (code 60) | Default when vegetation thresholds not met |
| **Scrub / Shrubland** | `Shrub/Scrub` (5), `Grass` (2) | `Shrubland` (20), `Herbaceous` (30) | `NDVI_max > 0.42` and `NDBI_mean < 0.10` |
| **Cropland** | `Crops` (code 4) | `Cultivated / Agriculture` (code 40) | `NDVI_max > 0.65` and `NDVI_mean > 0.17` |

---

## 4. Main Findings & Summary Results

### 12-Cell Classification Summary

| Cell ID | Visual Label (6 Cells) | Primary Method | Dynamic World (10 m) | Copernicus LC100 (100 m) | NDVI Mean | NDVI Max |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **C01** | Scrub / Shrubland | Bare Ground | Bare Ground (99.5%) | Scrub / Shrubland (94.4%) | 0.120 | 0.418 |
| **C02** | — | Scrub / Shrubland | Bare Ground (69.8%) | Bare / Sparse (39.5%) | 0.169 | 0.664 |
| **C03** | Bare Ground | Bare Ground | Bare Ground (92.7%) | Bare / Sparse (80.1%) | 0.103 | 0.393 |
| **C04** | Cropland | Cropland | Bare Ground (49.0%) | Cropland (62.8%) | 0.183 | 0.696 |
| **C05** | — | Scrub / Shrubland | Bare Ground (73.3%) | Scrub / Shrubland (95.3%) | 0.138 | 0.486 |
| **C06** | — | Scrub / Shrubland | Bare Ground (90.1%) | Scrub / Shrubland (92.6%) | 0.133 | 0.533 |
| **C07** | Mixed (Bare/Scrub) | Scrub / Shrubland | Bare Ground (69.1%) | Cropland (41.9%) | 0.137 | 0.436 |
| **C08** | — | Cropland | Cropland (68.9%) | Cropland (98.0%) | 0.255 | 0.840 |
| **C09** | Scrub / Shrubland | Scrub / Shrubland | Bare Ground (75.2%) | Scrub / Shrubland (96.6%) | 0.147 | 0.449 |
| **C10** | — | Bare Ground | Bare Ground (93.1%) | Scrub / Shrubland (98.4%) | 0.119 | 0.386 |
| **C11** | Bare Ground | Bare Ground | Bare Ground (90.5%) | Scrub / Shrubland (81.0%) | 0.119 | 0.585 |
| **C12** | — | Bare Ground | Bare Ground (89.9%) | Scrub / Shrubland (50.0%) | 0.110 | 0.332 |

### Key Observations

1. **Temporal Definition Divergence**: Dynamic World (a 6-week dry post-monsoon snapshot) classifies 11 of 12 cells as Bare Ground due to dry-season desiccation of sparse xerophytic shrubs. In contrast, Copernicus LC100 (an annual model) integrates earlier monsoon green-up, classifying 8 of 12 cells as Scrubland.
2. **Agreement vs. 6 Visual Labels (Denominator = 6)**:
   - Primary Spectral Method: **66.7% (4/6)**
   - Copernicus LC100: **66.7% (4/6)**
   - Dynamic World: **33.3% (2/6)**
3. **Disagreement Cell Diagnoses**:
   - **Cell C01 (Scrub vs. Bare)**: Peak vegetation index reaches $\text{NDVI}_{\max} = 0.418$. Arid deciduous shrubs (Prosopis/kair) drop foliage in late October, appearing bare to Dynamic World's single-window model, while Copernicus captures earlier annual greenness.
   - **Cell C04 (Cropland vs. Bare)**: Rectilinear cultivated field parcels where post-monsoon kharif harvest left bare plowed soil over 49% of the cell, causing Dynamic World's modal vote to default to Bare Ground despite standing crops in adjoining plots.
4. **Sensitivity Test**: Lowering the scrub threshold from $\text{NDVI}_{\max} > 0.420$ to $0.400$ changed exactly 1 of 12 cells (`C01`), increasing visual agreement to **83.3% (5/6)** and Copernicus agreement to **58.3% (7/12)**.

---

## 5. Methodological Disclosures & Independence

1. **Classifier Independence**: Primary classifications were computed directly from Sentinel-2 Level-2A surface reflectance indices (NDVI and NDBI). Neither Dynamic World nor Copernicus labels were used to train or guide the primary model.
2. **Spatial Separation**: Because an index-based threshold classifier was implemented rather than fitting a localized machine learning model on these 12 evaluation cells, there is zero spatial leakage between training and evaluation locations.
3. **Pretrained Overlap**: Dynamic World directly consumes Sentinel-2 L2A tiles. Copernicus CGLS-LC100 is based on PROBA-V (100 m) observations and regional reference data.

---

## 6. How to Reproduce

### 1. Setup Environment
```bash
git clone https://github.com/<your-username>/nutgraph_geos.git
cd nutgraph_geos
pip install -r requirements.txt
```

### 2. Run Scripts in Sequence
```bash
# Step 0: Run exploratory analysis and generate multi-panel diagnostic figure
python scripts/00_eda_sentinel2.py

# Step 1: Create 3x4 grid GeoJSON and export 12 RGB PNG chips (C01.png - C12.png)
python scripts/01_make_grid_and_chips.py

# Step 2: Compute primary classification, extract comparators, and build final CSV
python scripts/02_build_final_csv.py

# Step 3: Run parameter sensitivity test and generate comparison table
python scripts/03_sensitivity_test.py
```

### 3. Check Outputs
- Clean 12-cell CSV: `outputs/cell_level_classification.csv`
- Sensitivity CSV: `outputs/sensitivity_test_comparison.csv`
- Grid polygons: `data/processed/grid_12_cells.geojson`
- 12 PNG chips: `data/processed/chips/C01.png` to `C12.png`
- Visual diagnostic: `outputs/sentinel2_exploratory_analysis.png`
