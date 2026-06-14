# -*- coding: utf-8 -*-
"""Paraiba Hybrid Generation Potential Index (IP-PB).

Steps (paper Section 2.4 / 4.2):
  1. Max-Min normalise WIND_SPEED (x) and SOLAR_IRRAD (y) over the MM grid (Eq.7).
  2. Group the MM-grid points by municipality (mean x, y) -> 223 municipalities.
  3. IP-PB = sqrt(x^2 + y^2)  (euclidean norm; max sqrt(2) ~ 1.4142).
  4. Split municipalities by the medians of x and y into Good/Bad x Good/Bad
     groups (labelled Wind/Solar) and build solar / wind / hybrid top-10 rankings.
"""
import sys, os
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in (_ROOT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import numpy as np
import pandas as pd
import geopandas as gpd
import config
from interpolation import kriging_interpolate

W, S = config.WIND, config.SOLAR


def compute_ip_pb(mm_csv, points_csv, label):
    mm = pd.read_csv(mm_csv)
    mm["code"] = mm["code"].astype(str)
    wmin, wmax = mm[W].min(), mm[W].max()
    smin, smax = mm[S].min(), mm[S].max()
    mm["x"] = (mm[W] - wmin) / (wmax - wmin)
    mm["y"] = (mm[S] - smin) / (smax - smin)
    muni = (mm.groupby(["code", "name"])
            .agg(x=("x", "mean"), y=("y", "mean"), WIND_SPEED=(W, "mean"),
                 SOLAR_IRRAD=(S, "mean"), n_points=("x", "size")).reset_index())

    # cover municipalities with no grid point via their centroid
    mun = gpd.read_file(config.EXTERNAL / "pb_municipios.gpkg").to_crs("EPSG:4326")
    mun["code"] = mun["code"].astype(str)
    missing = mun[~mun["code"].isin(muni["code"])]
    if len(missing):
        cent = missing.geometry.centroid
        src = pd.read_csv(points_csv).dropna(subset=[W, S])
        xy = src[["lon", "lat"]].values
        tgt = np.c_[cent.x.values, cent.y.values]
        wv = kriging_interpolate(xy, src[W].values, tgt)
        sv = kriging_interpolate(xy, src[S].values, tgt)
        add = pd.DataFrame({"code": missing["code"].values, "name": missing["name"].values,
                            "WIND_SPEED": wv, "SOLAR_IRRAD": sv, "n_points": 0})
        add["x"] = (add["WIND_SPEED"] - wmin) / (wmax - wmin)
        add["y"] = (add["SOLAR_IRRAD"] - smin) / (smax - smin)
        muni = pd.concat([muni, add], ignore_index=True)
        print("  added %d municipalities via centroid" % len(missing))

    muni["IP_PB"] = np.sqrt(muni["x"] ** 2 + muni["y"] ** 2)
    mx, my = muni["x"].median(), muni["y"].median()
    muni["wind_cls"] = np.where(muni["x"] >= mx, "Good", "Bad")
    muni["solar_cls"] = np.where(muni["y"] >= my, "Good", "Bad")
    muni["group"] = muni["wind_cls"] + "/" + muni["solar_cls"]  # Wind/Solar
    muni = muni.sort_values("IP_PB", ascending=False).reset_index(drop=True)
    muni.to_csv(config.PROCESSED / ("ip_pb_%s.csv" % label), index=False)
    print("  IP-PB %s: municipalities=%d  median(x,y)=(%.3f,%.3f)  IP-PB max=%.4f" %
          (label, len(muni), mx, my, muni["IP_PB"].max()))
    print("  group counts:", muni["group"].value_counts().to_dict())
    return muni


def rankings(muni, label):
    solar = (muni[muni["solar_cls"] == "Good"].sort_values("SOLAR_IRRAD", ascending=False)
             .head(10)[["name", "SOLAR_IRRAD", "group", "IP_PB"]])
    wind = (muni[muni["wind_cls"] == "Good"].sort_values("WIND_SPEED", ascending=False)
            .head(10)[["name", "WIND_SPEED", "group", "IP_PB"]])
    hybrid = (muni[muni["group"] == "Good/Good"].sort_values("IP_PB", ascending=False)
              .head(10)[["name", "IP_PB", "WIND_SPEED", "SOLAR_IRRAD"]])
    for nm, r in (("solar", solar), ("wind", wind), ("hybrid", hybrid)):
        r.to_csv(config.TABLES / ("rank_%s_%s.csv" % (nm, label)), index=False)
    print("\n  TOP-10 SOLAR (%s):" % label, ", ".join(solar["name"].tolist()))
    print("  TOP-10 WIND  (%s):" % label, ", ".join(wind["name"].tolist()))
    print("  TOP-10 HYBRID(%s):" % label, ", ".join(hybrid["name"].tolist()))
    return solar, wind, hybrid


def run(label):
    mm = config.PROCESSED / ("mm_grid_%s.csv" % label)
    pts = config.PROCESSED / ("%s_points.csv" % label)
    if not mm.exists():
        print("  (%s MM grid not ready)" % label); return
    muni = compute_ip_pb(mm, pts, label)
    rankings(muni, label)


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    for lbl in (["nasa", "inmet"] if which == "all" else [which]):
        print("=== IP-PB:", lbl, "===")
        run(lbl)
