# spatial_models/fit_sar_poisson.py

import numpy as np
import pandas as pd
import libpysal
from spglm.family import Poisson
from spglm.glm import GLM
from spreg import GM_Lag
from pathlib import Path

# 1. Load data
df = pd.read_csv("../detentions_2021_25.csv")
pop = df["pop"]  # make sure you merged pop

# 2. Load W
npz = np.load("spatial_models/outputs/W_comunas.npz")
W = npz["W"]       # (n_comunas x n_comunas)
ids = npz["ids"]   # comuna codes

# 3. Build spatially lagged log(count)
#    reorder df by comuna to match ids
df = df.set_index("comuna").loc[ids].reset_index()
y = df["n_det"].values
X = np.log(df["pop"].values + 1).reshape(-1,1)  # intercept later

# 4. Fit SAR-Poisson via generalized method of moments
model = GM_Lag(y=y, x=X, w=W, name_y="n_det", name_x=["log_pop"],
               name_w="W", spat_diag=True, name_ds="ChileDet")
rho = model.rho[0]
beta = model.betas.flatten()
pvals = model.vm  # variance matrix for std errors

# 5. Save results
out = pd.DataFrame({
    "parameter": ["rho","beta_log_pop"],
    "estimate": [rho, beta[1]],       # beta[0] is intercept
    "std_err": np.sqrt(np.diag(pvals))
})
out.to_csv("spatial_models/outputs/sar_results.csv", index=False)
print("SAR results saved.")
