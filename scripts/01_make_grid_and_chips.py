"""
01_make_grid_and_chips.py
-------------------------
Divides the aligned 190x238 imagery into 12 non-overlapping cells (3 rows x 4 cols),
exports grid_12_cells.geojson, and saves 12 RGB PNG chips.
"""

import os
import json
import numpy as np
import rasterio
from shapely.geometry import box, mapping
from PIL import Image

# Directories
RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"
CHIPS_DIR = os.path.join(PROCESSED_DIR, "chips")

os.makedirs(CHIPS_DIR, exist_ok=True)

rgb_path = os.path.join(RAW_DIR, "sentinel2_2019_rgb_visual_10m.tif")
grid_geojson_path = os.path.join(PROCESSED_DIR, "grid_12_cells.geojson")

with rasterio.open(rgb_path) as src:
    rgb = src.read() # Shape: (3, 190, 238)
    h, w = src.height, src.width
    transform = src.transform
    crs = src.crs

# Define 3 rows x 4 columns grid
n_rows, n_cols = 3, 4
row_edges = np.linspace(0, h, n_rows + 1, dtype=int)
col_edges = np.linspace(0, w, n_cols + 1, dtype=int)

geojson_features = []
cells_metadata = []

cell_num = 1
for r in range(n_rows):
    y0, y1 = row_edges[r], row_edges[r + 1]
    for c in range(n_cols):
        x0, x1 = col_edges[c], col_edges[c + 1]
        cid = f"C{cell_num:02d}"

        # 1. Slice image array & export PNG chip
        # Raster visual bands are 8-bit [0-255], shape (3, H, W) -> (H, W, 3)
        chip_arr = np.moveaxis(rgb[:, y0:y1, x0:x1], 0, -1)
        chip_img = Image.fromarray(chip_arr.astype(np.uint8))
        chip_file = os.path.join(CHIPS_DIR, f"{cid}.png")
        chip_img.save(chip_file)

        # 2. Compute geographic bounding box from affine transform
        geo_x0, geo_y0 = transform * (x0, y0)
        geo_x1, geo_y1 = transform * (x1, y1)
        
        # Coordinates in EPSG:4326 (minx, miny, maxx, maxy)
        cell_geom = box(
            min(geo_x0, geo_x1),
            min(geo_y0, geo_y1),
            max(geo_x0, geo_x1),
            max(geo_y0, geo_y1)
        )

        geojson_features.append({
            "type": "Feature",
            "properties": {
                "cell_id": cid,
                "row": r + 1,
                "col": c + 1,
                "pixel_shape": f"{y1 - y0}x{x1 - x0}"
            },
            "geometry": mapping(cell_geom)
        })

        cells_metadata.append({
            "cell_id": cid,
            "x0": int(x0), "x1": int(x1),
            "y0": int(y0), "y1": int(y1),
            "chip_path": chip_file
        })
        cell_num += 1

# Export GeoJSON
fc = {
    "type": "FeatureCollection",
    "name": "grid_12_cells",
    "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
    "features": geojson_features
}

with open(grid_geojson_path, "w") as f:
    json.dump(fc, f, indent=2)

print(f"Exported {len(geojson_features)} cells to {grid_geojson_path}")
print(f"Exported 12 image chips to {CHIPS_DIR}")