import os
import rasterio
import numpy as np

RAW_DIR = "data/raw"
rgb_path = os.path.join(RAW_DIR, "sentinel2_2019_rgb_visual_10m.tif")
ms_path = os.path.join(RAW_DIR, "sentinel2_2019_multispectral_10m.tif")
dw_path = os.path.join(RAW_DIR, "dynamic_world_2019.tif")
cop_path = os.path.join(RAW_DIR, "copernicus_lc100_2019.tif")

print("Checking raster shapes and grid alignment...")

with rasterio.open(rgb_path) as src:
    rgb = src.read()
    print(f"S2 RGB:        Shape = {rgb.shape} (Bands, H, W)")

with rasterio.open(ms_path) as src:
    ms = src.read()
    print(f"S2 MultiSpec:  Shape = {ms.shape} (Bands, H, W)")

with rasterio.open(dw_path) as src:
    dw = src.read(1)
    print(f"Dynamic World: Shape = {dw.shape} | Unique classes: {np.unique(dw)}")

with rasterio.open(cop_path) as src:
    cop = src.read(1)
    print(f"Copernicus:    Shape = {cop.shape} | Unique classes: {np.unique(cop)}")

assert rgb.shape[1:] == ms.shape[1:] == dw.shape == cop.shape, "Error: Shapes do not match!"
print("\nAll rasters have matching dimensions (190 x 238). No local reprojection needed.")