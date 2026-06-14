# -*- coding: utf-8 -*-
"""Download IBGE municipal boundaries of Paraiba (223 municipalities) as GeoJSON,
attach municipality names, and save a GeoPackage for downstream use."""
import sys, os, json
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in (_ROOT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import requests
import geopandas as gpd
import config


def _get(url, timeout=120):
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout)
    r.raise_for_status()
    return r.json()


def main():
    geojson_path = config.EXTERNAL / "pb_municipios.geojson"
    gj = _get(config.IBGE_MALHA_URL)
    muns = _get(config.IBGE_MUNICIPIOS_URL)
    code2name = {str(m["id"]): m["nome"] for m in muns}
    for f in gj["features"]:
        code = str(f["properties"].get("codarea"))
        f["properties"]["code"] = code
        f["properties"]["name"] = code2name.get(code, code)
    with open(geojson_path, "w", encoding="utf-8") as fh:
        json.dump(gj, fh, ensure_ascii=False)

    gdf = gpd.read_file(geojson_path)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4674")  # IBGE uses SIRGAS 2000
    gdf = gdf.to_crs("EPSG:4326")
    gpkg = config.EXTERNAL / "pb_municipios.gpkg"
    gdf.to_file(gpkg, driver="GPKG")
    print("municipios:", len(gdf))
    print("sample:", gdf[["code", "name"]].head(3).to_dict("records"))
    print("bounds (lon_min, lat_min, lon_max, lat_max):", [round(x, 3) for x in gdf.total_bounds])
    print("saved ->", gpkg)


if __name__ == "__main__":
    main()
