"""
00_eda_sentinel2.py
-------------------
Exploratory Data Analysis and Descriptive Statistics for Sentinel-2,
Dynamic World, and Copernicus CGLS-LC100 (2019) over Nagnechinagar, Rajasthan.
"""

import os
import rasterio
from rasterio.warp import reproject, Resampling
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Dynamic World & Copernicus Land Cover Class Dictionaries
DW_CLASSES = {
    0: "Water", 1: "Trees", 2: "Grass", 3: "Flooded Veg",
    4: "Crops", 5: "Shrub/Scrub", 6: "Built", 7: "Bare", 8: "Snow/Ice"
}

COP_CLASSES = {
    0: "Unknown/NoData",
    20: "Shrubland",
    30: "Herbaceous vegetation",
    40: "Cultivated / Agriculture",
    50: "Urban / Built-up",
    60: "Bare / Sparse vegetation",
    70: "Snow / Ice",
    80: "Permanent water",
    114: "Open forest (deciduous)",
    116: "Open forest (other)",
    124: "Closed forest (deciduous)",
    126: "Closed forest (other)"
}

def normalize_band(band, lower=2, upper=98):
    """Robust percentile stretch [0, 1] for visual display."""
    band_clean = np.nan_to_num(band, nan=0.0)
    vmin, vmax = np.percentile(band_clean, (lower, upper))
    if vmax <= vmin:
        return np.zeros_like(band_clean)
    clipped = np.clip(band_clean, vmin, vmax)
    return (clipped - vmin) / (vmax - vmin)

def load_rasters(rgb_path, ms_path, dw_path, cop_path):
    """Loads all raw rasters, calculates NDVI/NDBI if needed, and aligns Copernicus."""
    with rasterio.open(rgb_path) as src_rgb:
        rgb = np.moveaxis(src_rgb.read(), 0, -1)  # (H, W, 3)
        height, width = src_rgb.height, src_rgb.width
        bounds = src_rgb.bounds
        crs = src_rgb.crs
        transform = src_rgb.transform

    with rasterio.open(ms_path) as src_ms:
        ms = src_ms.read().astype(np.float32)  # (Bands, H, W)
        
        # Verify if NDVI/NDBI exist as bands 7 and 8; if not, compute from B4, B8, B11
        if ms.shape[0] < 8:
            # Assuming [B2, B3, B4, B8, B11, B12]
            b4 = ms[2]
            b8 = ms[3]
            b11 = ms[4]
            ndvi = np.where((b8 + b4) != 0, (b8 - b4) / (b8 + b4), 0.0)
            ndbi = np.where((b11 + b8) != 0, (b11 - b8) / (b11 + b8), 0.0)
            ms = np.vstack([ms, ndvi[np.newaxis, ...], ndbi[np.newaxis, ...]])

    with rasterio.open(dw_path) as src_dw:
        dw = src_dw.read(1)

    # Reproject Copernicus LC100 to match Sentinel-2 grid exactly
    with rasterio.open(cop_path) as src_cop:
        cop_reprojected = np.zeros((height, width), dtype=np.uint8)
        reproject(
            source=src_cop.read(1),
            destination=cop_reprojected,
            src_transform=src_cop.transform,
            src_crs=src_cop.crs,
            dst_transform=transform,
            dst_crs=crs,
            resampling=Resampling.nearest
        )

    return {
        "rgb": rgb,
        "ms": ms,
        "dw": dw,
        "cop": cop_reprojected,
        "height": height,
        "width": width,
        "bounds": bounds
    }

def get_grid_cells(height, width, n_rows=3, n_cols=4):
    """Calculates pixel slicing coordinates for a 3x4 grid without edge gaps."""
    row_step = height / n_rows
    col_step = width / n_cols
    cells = []
    idx = 1
    for r in range(n_rows):
        y0 = int(round(r * row_step))
        y1 = height if r == n_rows - 1 else int(round((r + 1) * row_step))
        for c in range(n_cols):
            x0 = int(round(c * col_step))
            x1 = width if c == n_cols - 1 else int(round((c + 1) * col_step))
            cid = f"C{idx:02d}"
            cells.append({
                "cell_id": cid,
                "row": r + 1,
                "col": c + 1,
                "x0": x0,
                "y0": y0,
                "x1": x1,
                "y1": y1
            })
            idx += 1
    return cells

def compute_cell_statistics(data, cells):
    """Computes descriptive stats (NDVI, NDBI, DW mode, Copernicus mode) per cell."""
    b_ndvi = data["ms"][6]
    b_ndbi = data["ms"][7]
    dw = data["dw"]
    cop = data["cop"]

    records = []
    for cell in cells:
        cid = cell["cell_id"]
        x0, x1 = cell["x0"], cell["x1"]
        y0, y1 = cell["y0"], cell["y1"]

        cell_ndvi = b_ndvi[y0:y1, x0:x1]
        cell_ndbi = b_ndbi[y0:y1, x0:x1]
        cell_dw = dw[y0:y1, x0:x1]
        cell_cop = cop[y0:y1, x0:x1]

        # Dynamic World mode & share
        dw_vals, dw_counts = np.unique(cell_dw, return_counts=True)
        dw_mode_val = dw_vals[np.argmax(dw_counts)]
        dw_mode_pct = (np.max(dw_counts) / cell_dw.size) * 100
        dw_mode_name = DW_CLASSES.get(dw_mode_val, f"DW_{dw_mode_val}")

        # Copernicus LC100 mode & share
        cop_vals, cop_counts = np.unique(cell_cop, return_counts=True)
        cop_mode_val = cop_vals[np.argmax(cop_counts)]
        cop_mode_pct = (np.max(cop_counts) / cell_cop.size) * 100
        cop_mode_name = COP_CLASSES.get(cop_mode_val, f"COP_{cop_mode_val}")

        records.append({
            "cell_id": cid,
            "grid_row": cell["row"],
            "grid_col": cell["col"],
            "pixel_count": cell_ndvi.size,
            "ndvi_mean": round(float(np.nanmean(cell_ndvi)), 3),
            "ndvi_std": round(float(np.nanstd(cell_ndvi)), 3),
            "ndvi_min": round(float(np.nanmin(cell_ndvi)), 3),
            "ndvi_max": round(float(np.nanmax(cell_ndvi)), 3),
            "ndbi_mean": round(float(np.nanmean(cell_ndbi)), 3),
            "ndbi_std": round(float(np.nanstd(cell_ndbi)), 3),
            "dw_2019_mode": dw_mode_name,
            "dw_mode_share_pct": round(dw_mode_pct, 1),
            "copernicus_2019_mode": cop_mode_name,
            "cop_mode_share_pct": round(cop_mode_pct, 1)
        })

    return pd.DataFrame(records)

def save_and_display_table(stats_df, out_csv_path):
    """Outputs formatted table to console and writes CSV."""
    stats_df.to_csv(out_csv_path, index=False)
    print("\n" + "=" * 90)
    print("CELL-LEVEL DESCRIPTIVE STATISTICS & COMPARATOR MODES (2019)")
    print("=" * 90)
    print(stats_df[[
        "cell_id", "ndvi_mean", "ndvi_max", "ndbi_mean",
        "dw_2019_mode", "dw_mode_share_pct",
        "copernicus_2019_mode", "cop_mode_share_pct"
    ]].to_string(index=False))
    print("=" * 90)
    print(f"Summary table saved to: {out_csv_path}")

def plot_exploratory_figures(data, cells, out_fig_path):
    """Generates 6-panel diagnostic comparison plot."""
    rgb = data["rgb"]
    ms = data["ms"]
    dw = data["dw"]
    cop = data["cop"]

    # False Color CIR (NIR=B8, Red=B4, Green=B3)
    cir = np.stack([
        normalize_band(ms[3]),
        normalize_band(ms[2]),
        normalize_band(ms[1])
    ], axis=-1)

    # SWIR Composite (SWIR2=B12, NIR=B8, Red=B4)
    swir = np.stack([
        normalize_band(ms[5]),
        normalize_band(ms[3]),
        normalize_band(ms[2])
    ], axis=-1)

    ndvi = ms[6]

    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    plt.subplots_adjust(wspace=0.15, hspace=0.22)

    # 1. RGB Visual + Grid
    ax = axes[0, 0]
    ax.imshow(rgb)
    ax.set_title("1. True Color RGB (B4-B3-B2) + 3x4 Grid", fontsize=11, fontweight="bold")
    for c in cells:
        rect = patches.Rectangle((c["x0"], c["y0"]), c["x1"] - c["x0"], c["y1"] - c["y0"],
                                 linewidth=1.5, edgecolor="yellow", facecolor="none", linestyle="--")
        ax.add_patch(rect)
        ax.text(c["x0"] + 3, c["y0"] + 15, c["cell_id"], color="yellow", fontsize=10, fontweight="bold",
                bbox=dict(boxstyle="square,pad=0.15", facecolor="black", alpha=0.6, edgecolor="none"))
    ax.axis("off")

    # 2. CIR (Infrared)
    ax = axes[0, 1]
    ax.imshow(cir)
    ax.set_title("2. False Color CIR (B8-B4-B3)\n[Red = Crops, Scrub & Vegetation]", fontsize=11, fontweight="bold")
    for c in cells:
        rect = patches.Rectangle((c["x0"], c["y0"]), c["x1"] - c["x0"], c["y1"] - c["y0"],
                                 linewidth=0.8, edgecolor="white", facecolor="none", linestyle=":")
        ax.add_patch(rect)
        ax.text(c["x0"] + 3, c["y0"] + 15, c["cell_id"], color="white", fontsize=9, fontweight="bold")
    ax.axis("off")

    # 3. SWIR Composite
    ax = axes[0, 2]
    ax.imshow(swir)
    ax.set_title("3. SWIR (B12-B8-B4)\n[Highlights Wasteland, Rock & Soil Moisture]", fontsize=11, fontweight="bold")
    for c in cells:
        rect = patches.Rectangle((c["x0"], c["y0"]), c["x1"] - c["x0"], c["y1"] - c["y0"],
                                 linewidth=0.8, edgecolor="cyan", facecolor="none", linestyle=":")
        ax.add_patch(rect)
        ax.text(c["x0"] + 3, c["y0"] + 15, c["cell_id"], color="cyan", fontsize=9, fontweight="bold")
    ax.axis("off")

    # 4. NDVI
    ax = axes[1, 0]
    im_ndvi = ax.imshow(ndvi, cmap="YlGn", vmin=0.0, vmax=0.4)
    ax.set_title("4. Sentinel-2 NDVI (Vegetation Index)", fontsize=11, fontweight="bold")
    for c in cells:
        rect = patches.Rectangle((c["x0"], c["y0"]), c["x1"] - c["x0"], c["y1"] - c["y0"],
                                 linewidth=0.8, edgecolor="black", facecolor="none", linestyle=":")
        ax.add_patch(rect)
        ax.text(c["x0"] + 3, c["y0"] + 15, c["cell_id"], color="black", fontsize=9, fontweight="bold")
    fig.colorbar(im_ndvi, ax=ax, fraction=0.046, pad=0.04, label="NDVI")
    ax.axis("off")

    # 5. Dynamic World 2019
    ax = axes[1, 1]
    dw_palette = {
        0: [65, 155, 223], 1: [57, 125, 73], 2: [136, 176, 83], 3: [122, 135, 198],
        4: [228, 150, 53], 5: [223, 195, 90], 6: [196, 40, 27], 7: [165, 155, 143]
    }
    dw_rgb = np.zeros((*dw.shape, 3), dtype=np.uint8)
    for val, col in dw_palette.items():
        dw_rgb[dw == val] = col

    ax.imshow(dw_rgb)
    ax.set_title("5. Dynamic World 2019 (10m Resolution)", fontsize=11, fontweight="bold")
    for c in cells:
        rect = patches.Rectangle((c["x0"], c["y0"]), c["x1"] - c["x0"], c["y1"] - c["y0"],
                                 linewidth=0.8, edgecolor="black", facecolor="none", linestyle=":")
        ax.add_patch(rect)
        ax.text(c["x0"] + 3, c["y0"] + 15, c["cell_id"], color="black", fontsize=9, fontweight="bold")
    ax.axis("off")
    dw_legend = [
        patches.Patch(facecolor="#e49635", label="Crops"),
        patches.Patch(facecolor="#dfc35a", label="Shrub/Scrub"),
        patches.Patch(facecolor="#a59b8f", label="Bare Land"),
        patches.Patch(facecolor="#c4281b", label="Built")
    ]
    ax.legend(handles=dw_legend, loc="lower right", fontsize=8, framealpha=0.8)

    # 6. Copernicus LC100 2019
    ax = axes[1, 2]
    cop_palette = {
        20: [255, 187, 34],   # Shrubland (yellow-orange)
        30: [255, 255, 76],   # Herbaceous (yellow)
        40: [240, 150, 255],  # Agriculture (pink/violet)
        50: [250, 0, 0],      # Built-up (red)
        60: [180, 180, 180]   # Bare (gray)
    }
    cop_rgb = np.full((*cop.shape, 3), 220, dtype=np.uint8)
    for val, col in cop_palette.items():
        cop_rgb[cop == val] = col

    ax.imshow(cop_rgb)
    ax.set_title("6. Copernicus LC100 2019 (100m Resolution)", fontsize=11, fontweight="bold")
    for c in cells:
        rect = patches.Rectangle((c["x0"], c["y0"]), c["x1"] - c["x0"], c["y1"] - c["y0"],
                                 linewidth=0.8, edgecolor="black", facecolor="none", linestyle=":")
        ax.add_patch(rect)
        ax.text(c["x0"] + 3, c["y0"] + 15, c["cell_id"], color="black", fontsize=9, fontweight="bold")
    ax.axis("off")
    cop_legend = [
        patches.Patch(facecolor="#ffbb22", label="Shrubland (20)"),
        patches.Patch(facecolor="#ffff4c", label="Herbaceous (30)"),
        patches.Patch(facecolor="#f096ff", label="Agriculture (40)"),
        patches.Patch(facecolor="#b4b4b4", label="Bare / Sparse (60)")
    ]
    ax.legend(handles=cop_legend, loc="lower right", fontsize=8, framealpha=0.8)

    plt.suptitle("Exploratory Multi-Sensor Diagnostic: Nagnechinagar, Rajasthan (2019)",
                 fontsize=14, fontweight="bold", y=0.98)
    plt.savefig(out_fig_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Diagnostic visualization saved to: {out_fig_path}")

def main():
    rgb_path = "data/raw/sentinel2_2019_rgb_visual_10m.tif"
    ms_path = "data/raw/sentinel2_2019_multispectral_10m.tif"
    dw_path = "data/raw/dynamic_world_2019.tif"
    cop_path = "data/raw/copernicus_lc100_2019.tif"

    out_fig_path = "outputs/sentinel2_exploratory_analysis.png"
    out_csv_path = "outputs/eda_cell_statistics.csv"

    os.makedirs("outputs", exist_ok=True)

    # 1. Load rasters
    data = load_rasters(rgb_path, ms_path, dw_path, cop_path)

    # 2. Define 3x4 grid cells
    cells = get_grid_cells(data["height"], data["width"])

    # 3. Compute cell descriptive stats and comparator modes
    stats_df = compute_cell_statistics(data, cells)

    # 4. Save and display stats
    save_and_display_table(stats_df, out_csv_path)

    # 5. Plot 6-panel exploratory figure
    plot_exploratory_figures(data, cells, out_fig_path)

if __name__ == "__main__":
    main()