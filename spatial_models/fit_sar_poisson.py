import numpy as np, pandas as pd
from libpysal.weights import Queen
import libpysal, geopandas as gpd
from spglm.family import Poisson
from spglm.glm import GLM
from spreg import GM_Lag


# 1. geometry & weights  ------------------------------------
gdf = gpd.read_file("../data/shapes/comunas.geojson", engine="pyogrio")
gdf["uid"] = gdf["GID_3"]

# This is *already* a libpysal W object
w = Queen.from_dataframe(gdf, ids=gdf["uid"])      # <-- remove .to_W()

# 2. align data to the weight-matrix order  ---------------
agg = pd.read_csv("outputs/agg_for_r.csv").set_index("uid").loc[w.id_order]

y = agg["n_det"].values.reshape((-1, 1))   # GM_Lag expects 2-D
X = agg[["log_pop"]].values                # (n × k)

from spglm.glm import GLM
model = GLM(y, X, family=Poisson(), w=w, spat_diag=True,
            name_y="n_det", name_x=["log_pop"])


print(model.summary)

# save
out = pd.DataFrame(
    {
        "parameter": ["beta_const", "beta_log_pop", "rho"],
        "estimate":  [model.betas[0,0], model.betas[1,0], model.rho[0]],
        "std_err":   np.sqrt(np.diag(model.vm))
    }
)
out.to_csv("outputs/py_spglm_poisson.csv", index=False)
print("✓ py_spglm_poisson.csv written")