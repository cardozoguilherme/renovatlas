# -*- coding: utf-8 -*-
"""Collect NASA POWER daily series (WS10M, ALLSKY_SFC_SW_DWN) on a 0.5 deg grid
covering Paraiba and neighbouring states. One CSV per grid point (cached)."""
import sys, os, time
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in (_ROOT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
import pandas as pd
import requests
import config

NASA_DIR = config.RAW / "nasa"
NASA_DIR.mkdir(parents=True, exist_ok=True)


def grid_points():
    g = config.NASA_GRID
    lats = np.round(np.arange(g["lat_min"], g["lat_max"] + 1e-9, config.NASA_RES), 4)
    lons = np.round(np.arange(g["lon_min"], g["lon_max"] + 1e-9, config.NASA_RES), 4)
    return [(float(la), float(lo)) for la in lats for lo in lons]


def fetch_point(lat, lon, retries=4):
    params = {
        "parameters": ",".join(config.NASA_PARAMS),
        "community": config.NASA_COMMUNITY,
        "longitude": lon, "latitude": lat,
        "start": config.NASA_START, "end": config.NASA_END,
        "format": "JSON",
    }
    for attempt in range(retries):
        try:
            r = requests.get(config.NASA_API, params=params, timeout=120,
                             headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            return r.json()
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(3 * (attempt + 1))


def json_to_df(js, lat, lon):
    p = js["properties"]["parameter"]
    df = pd.DataFrame({k: pd.Series(v) for k, v in p.items()})
    df.index.name = "date"
    df = df.reset_index()
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    df.insert(1, "lat", lat)
    df.insert(2, "lon", lon)
    for c in config.NASA_PARAMS:          # NASA POWER fill value is -999
        df[c] = df[c].where(df[c] > -900, np.nan)
    return df


def main(limit=None):
    pts = grid_points()
    if limit:
        pts = pts[:limit]
    print("NASA grid points to fetch:", len(pts))
    manifest = []
    for i, (lat, lon) in enumerate(pts, 1):
        fn = NASA_DIR / ("nasa_%+.2f_%+.2f.csv" % (lat, lon))
        if fn.exists() and fn.stat().st_size > 0:
            manifest.append((lat, lon, fn.name))
            print("[%d/%d] cached %s" % (i, len(pts), fn.name))
            continue
        try:
            df = json_to_df(fetch_point(lat, lon), lat, lon)
            df.to_csv(fn, index=False)
            print("[%d/%d] %s rows=%d ws_valid=%d sw_valid=%d" %
                  (i, len(pts), fn.name, len(df),
                   int(df["WS10M"].notna().sum()),
                   int(df["ALLSKY_SFC_SW_DWN"].notna().sum())))
            manifest.append((lat, lon, fn.name))
            time.sleep(0.4)
        except Exception as e:
            print("[%d/%d] FAIL (%.2f,%.2f): %s" % (i, len(pts), lat, lon, repr(e)[:120]))
    pd.DataFrame(manifest, columns=["lat", "lon", "file"]).to_csv(
        NASA_DIR / "_manifest.csv", index=False)
    print("DONE saved %d points -> %s" % (len(manifest), NASA_DIR))


if __name__ == "__main__":
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else None
    main(lim)
