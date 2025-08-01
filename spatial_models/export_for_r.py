import numpy as np
import pandas as pd
import unicodedata

def norm(txt):
    if pd.isna(txt): return None
    return unicodedata.normalize("NFKD", str(txt)) \
        .encode("ascii", "ignore") \
        .decode("utf-8") \
        .upper().strip()

# 1) load
det = pd.read_csv("../detentions_2021_25.csv")
pop = pd.read_csv("../census_pop_debug.csv")

# 2) normalize & merge
det["comuna_norm"] = det["comuna"].apply(norm)
pop["comuna_norm"] = pop["comuna"].apply(norm)
df = det.merge(pop[["comuna_norm","year","pop"]], on=["comuna_norm","year"], how="left")
df = df[df["year"] == 2022]

# 3) attach uids
lookup = pd.read_csv("outputs/uid_to_comuna.csv")  # from build_spatial_weights
df = df.merge(lookup, on="comuna_norm", how="inner")

# 4) aggregate to commune‐level
agg = (
    df.groupby("uid")
      .agg(n_det=("n_det","sum"),
           pop   =("pop",  "first"))
      .reset_index()
)

# 5) align to W order
npz  = np.load("outputs/W_comunas.npz")
uids = list(npz["ids"])
median_pop = agg["pop"].median()
agg = (
    agg.set_index("uid")
       .reindex(uids)
       .fillna({"n_det":0,"pop":median_pop})
       .reset_index()
)

# 6) compute log-pop & export
agg["log_pop"] = np.log(agg["pop"] + 1)
agg.to_csv("outputs/agg_for_r.csv", index=False)
print("→ outputs/agg_for_r.csv written:", agg.shape)
