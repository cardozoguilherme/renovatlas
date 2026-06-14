# -*- coding: utf-8 -*-
"""Interpolation methods (IDW and Ordinary Kriging) and leave-one-out
cross-validation to reproduce Table 2 (IDW vs Kriging error comparison).

IDW uses the corrected inverse-distance weighting: w_i = 1/d_i^p (the paper's
printed Eq. 2 has d^2 in the numerator, which is a typo). Kriging uses an
exponential variogram (paper Eq. 3) restricted to the k closest neighbours.
"""
import sys, os
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in (_ROOT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from sklearn.metrics import r2_score
from pykrige.ok import OrdinaryKriging
import config


def idw_interpolate(xy_known, z_known, xy_target, k=config.N_NEIGHBORS, power=config.IDW_POWER):
    tree = cKDTree(xy_known)
    k = min(k, len(xy_known))
    dist, idx = tree.query(xy_target, k=k)
    if k == 1:
        dist, idx = dist[:, None], idx[:, None]
    with np.errstate(divide="ignore"):
        w = 1.0 / np.power(dist, power)
    w[~np.isfinite(w)] = 1e12          # exact coincidence -> dominant weight
    z = z_known[idx]
    return np.sum(w * z, axis=1) / np.sum(w, axis=1)


def kriging_interpolate(xy_known, z_known, xy_target, k=config.N_NEIGHBORS,
                        variogram=config.KRIGING_VARIOGRAM):
    OK = OrdinaryKriging(xy_known[:, 0], xy_known[:, 1], z_known,
                         variogram_model=variogram, coordinates_type="euclidean",
                         verbose=False, enable_plotting=False)
    kk = min(k, len(xy_known))
    z, _ = OK.execute("points", xy_target[:, 0], xy_target[:, 1],
                      backend="loop", n_closest_points=kk)
    return np.asarray(z)


def _xyz(df, value_col):
    sub = df.dropna(subset=[value_col])
    return sub[["lon", "lat"]].values, sub[value_col].values


def loocv(df, value_col, method, k=config.N_NEIGHBORS):
    xy, z = _xyz(df, value_col)
    n = len(z)
    pred = np.full(n, np.nan)
    for i in range(n):
        tr = np.arange(n) != i
        fn = idw_interpolate if method == "idw" else kriging_interpolate
        pred[i] = fn(xy[tr], z[tr], xy[i:i + 1], k=k)[0]
    return z, pred


def metrics(y, yhat):
    e = yhat - y
    return dict(RMSE=float(np.sqrt(np.mean(e ** 2))),
                MAE=float(np.mean(np.abs(e))),
                R2=float(r2_score(y, yhat)))


def reproduce_table2(points_csv, label):
    df = pd.read_csv(points_csv)
    rows = []
    specs = [(config.WIND, "WIND_SPEED (m/s)"), (config.SOLAR, "SOLAR_IRRAD (kWh/m2)")]
    for col, pretty in specs:
        for method in ("idw", "kriging"):
            y, yhat = loocv(df, col, method)
            m = metrics(y, yhat)
            rows.append(dict(Variable=pretty, Method=method.upper(), n=len(y), **m))
            print("%-22s %-7s n=%2d RMSE=%.4f MAE=%.4f R2=%.4f" %
                  (pretty, method.upper(), len(y), m["RMSE"], m["MAE"], m["R2"]))
    out = pd.DataFrame(rows)
    fn = config.TABLES / ("table2_%s.csv" % label)
    out.to_csv(fn, index=False)
    print("saved ->", fn)
    return out


if __name__ == "__main__":
    for lbl in ("nasa", "inmet"):
        pts = config.PROCESSED / ("%s_points.csv" % lbl)
        if pts.exists():
            print("=== Table 2 reproduction (LOOCV, k=%d neighbours) — %s ===" %
                  (config.N_NEIGHBORS, lbl.upper()))
            reproduce_table2(pts, lbl)
