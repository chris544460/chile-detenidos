# spatial_models/fit_spatial_error.py

import numpy as np
import pandas as pd
import libpysal
from spreg import GM_Error
from pathlib import Path

# 1. Load DPI summary
dpi = pd.read_csv("../data/dpi_summary.csv")   # contains commune, year, DPI

# 2. Load W (same as before)
npz = np.load("spatial_models/outputs/W_comunas.npz")
W = npz["W"]
ids = npz["ids"]

# 3. Align and extract X, y
dpi = dpi.set_index("comuna").loc[ids].reset_index()
y = dpi["DPI"].values.reshape(-1,1)
X = np.ones((y.shape[0],1))  # intercept only, or add covariates

# 4. Fit Spatial Error
model = GM_Error(y=y, x=X, w=W, name_y="DPI", name_x=["const"], name_w="W")
lam = model.lambda1[0]
beta = model.betas.flatten()
pvals = model.vm

# 5. Save results
out = pd.DataFrame({
    "parameter": ["lambda","beta_const"],
    "estimate": [lam, beta[0]],
    "std_err": np.sqrt(np.diag(pvals))
})
out.to_csv("spatial_models/outputs/error_results.csv", index=False)
print("Spatial‐Error results saved.")
