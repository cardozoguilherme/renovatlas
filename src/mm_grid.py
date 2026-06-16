# -*- coding: utf-8 -*-
"""Monta a grade MM (Multi-Map): pontos de 0,05 grau dentro do poligono da Paraiba (cerca
de 2054 esperados pelo artigo; ~2016 obtidos aqui), cada um marcado com o seu municipio.
Em seguida, interpola WIND_SPEED e SOLAR_IRRAD para esses pontos por Kriging, a partir dos
conjuntos de pontos da NASA e do INMET.

Etapa de CONSTRUCAO DO MM GRID (reproducao). Corresponde a Secao 4.1 do artigo.
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
from shapely.geometry import Point
import config
from interpolation import kriging_interpolate   # reaproveita o Kriging do modulo de interpolacao


def build_pb_grid():
    """Cria a grade regular de 0,05 grau no retangulo que envolve a Paraiba e mantem so os
    pontos que caem dentro do estado, marcando o municipio de cada um. Pontos a ate meia
    celula da borda sao atribuidos ao municipio mais proximo (para nao perder a faixa de
    fronteira). Retorna um GeoDataFrame com lon, lat, nome e codigo do municipio."""
    mun = gpd.read_file(config.EXTERNAL / "pb_municipios.gpkg").to_crs("EPSG:4326")
    b = config.PB_BBOX
    lats = np.round(np.arange(round(b["lat_min"], 2), b["lat_max"] + 1e-9, config.MM_RES), 3)
    lons = np.round(np.arange(round(b["lon_min"], 2), b["lon_max"] + 1e-9, config.MM_RES), 3)
    pts = [(float(lo), float(la)) for la in lats for lo in lons]
    gdf = gpd.GeoDataFrame(
        {"lon": [p[0] for p in pts], "lat": [p[1] for p in pts]},
        geometry=[Point(p) for p in pts], crs="EPSG:4326")
    # sjoin_nearest liga cada ponto ao municipio que o contem ou, para pontos a ate meia
    # celula da borda, ao municipio mais proximo.
    joined = gpd.sjoin_nearest(gdf, mun[["name", "code", "geometry"]],
                               max_distance=config.MM_RES * 0.5, how="inner")
    joined = (joined.drop(columns=["index_right"])
              .drop_duplicates(subset=["lon", "lat"]).reset_index(drop=True))
    print("MM grid points inside PB:", len(joined), "| municipalities:", joined["name"].nunique())
    return joined


def interpolate_grid(grid, points_csv, label):
    """Interpola vento e radiacao para todos os pontos da grade, por Kriging, usando os
    pontos de origem (NASA ou INMET). Salva mm_grid_<label>.csv."""
    src = pd.read_csv(points_csv)
    g = grid.copy()
    target = g[["lon", "lat"]].values
    for col in (config.WIND, config.SOLAR):
        sub = src.dropna(subset=[col])
        xy = sub[["lon", "lat"]].values
        z = sub[col].values
        g[col] = kriging_interpolate(xy, z, target, k=config.N_NEIGHBORS)
    out = pd.DataFrame(g.drop(columns="geometry"))
    fn = config.PROCESSED / ("mm_grid_%s.csv" % label)
    out.to_csv(fn, index=False)
    print("  %s: WIND %.2f-%.2f | SOLAR %.2f-%.2f -> %s" %
          (label, out[config.WIND].min(), out[config.WIND].max(),
           out[config.SOLAR].min(), out[config.SOLAR].max(), fn.name))
    return out


def main():
    # Monta a grade uma vez (salva os pontos) e interpola para NASA e/ou INMET.
    grid = build_pb_grid()
    grid.drop(columns="geometry").to_csv(config.PROCESSED / "mm_grid_points.csv", index=False)
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("all", "nasa"):
        interpolate_grid(grid, config.PROCESSED / "nasa_points.csv", "nasa")
    if which in ("all", "inmet"):
        ip = config.PROCESSED / "inmet_points.csv"
        if ip.exists():
            interpolate_grid(grid, ip, "inmet")
        else:
            print("  (inmet_points.csv not ready yet)")


if __name__ == "__main__":
    main()
