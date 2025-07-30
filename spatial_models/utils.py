# spatial_models/utils.py

import numpy as np

def load_weights(path="outputs/W_comunas.npz"):
    npz = np.load(path)
    return npz["W"], list(npz["ids"])
