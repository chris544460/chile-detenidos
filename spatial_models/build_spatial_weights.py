# spatial_models/build_spatial_weights.py
import json
import numpy as np
import pandas as pd
from shapely.geometry import shape
import libpysal

# ---------- 1. load GeoJSON ----------
with open("../data/shapes/comunas.geojson", "r") as f:
    gj = json.load(f)

records = []
for feat in gj["features"]:
    props = feat["properties"].copy()
    props["geometry"] = shape(feat["geometry"])
    records.append(props)

gdf = pd.DataFrame(records)

# ---------- 2. build a human‑readable name & a unique id ----------
gdf["comuna_norm"] = (
    gdf["NAME_3"]
      .str.upper()
      .str.normalize("NFKD")
      .str.encode("ascii", errors="ignore")
      .str.decode("utf-8")
      .str.strip()
)

# use GID_3 (e.g. 'CHL.2.1.1_1') as the unique key
gdf["uid"] = gdf["GID_3"]

# ---------- 3. build Queen contiguity weights ----------
w = libpysal.weights.Queen.from_dataframe(gdf, ids=gdf["uid"])
w.transform = "R"   # row‑standardise

# ---------- 4. save ----------
W, ids = w.full()                     # dense W and ordered id list
np.savez("outputs/W_comunas.npz", W=W, ids=np.array(ids))

# also save a lookup table uid → comuna name for later merges
lookup = gdf[["uid", "comuna_norm"]]
lookup.to_csv("outputs/uid_to_comuna.csv", index=False)

print("✓ W matrix saved:", W.shape, "   lookup rows:", len(lookup))
