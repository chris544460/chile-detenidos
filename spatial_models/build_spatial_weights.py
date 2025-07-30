# spatial_models/build_spatial_weights.py

import geopandas as gpd
import libpysal
import numpy as np

# 1. Load comuna shapes
gdf = gpd.read_file("../data/shapes/comunas.geojson")
gdf = gdf.to_crs(epsg=4326)

# 2. Build contiguity-based weights
w = libpysal.weights.Queen.from_dataframe(gdf, idVariable="COMUNA_CODE")
w.transform = "R"  # row-standardize

# 3. Serialize
weights_array = w.full()[0]    # the W matrix
ids = np.array(w.id_order)     # comuna identifiers in the same order
np.savez("spatial_models/outputs/W_comunas.npz",
         W=weights_array, ids=ids)
print("Saved W_comunas.npz with shape", weights_array.shape)
