# -*- coding: utf-8 -*-
"""CONTRIBUICAO (Ideia 2): coleta de covariaveis fisicas que o artigo nao usa.

O artigo interpola usando apenas latitude e longitude. Aqui acrescentamos duas variaveis:
  - elevacao (relevo), obtida da API Open-Meteo (modelo Copernicus DEM 90 m);
  - distancia ate a costa atlantica, calculada a partir do contorno leste da Paraiba.

Gera versoes "_cov.csv" dos pontos da NASA, das estacoes do INMET e do MM grid, com as
colunas elev (m) e dist_coast (km) acrescentadas, para servir de entrada aos modelos de
aprendizado de maquina (src/train.py e src/ml_interpolation.py).
"""
import sys, os, time
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in (_ROOT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import numpy as np
import pandas as pd
import requests
import geopandas as gpd
from scipy.spatial import cKDTree
import config

ELEV_API = "https://api.open-meteo.com/v1/elevation"
LAT0 = -7.2  # latitude de referencia da PB, usada na projecao plana local (distancia em km)


def fetch_elevation(lats, lons, batch=100):
    """Consulta a elevacao de varios pontos na API Open-Meteo, em lotes de ate 100. Trata o
    limite de requisicoes (erro HTTP 429) esperando mais tempo e tentando de novo, e faz uma
    pausa entre os lotes para nao sobrecarregar a API publica."""
    out = []
    n = len(lats)
    for i in range(0, n, batch):
        la = lats[i:i + batch]
        lo = lons[i:i + batch]
        params = {"latitude": ",".join("%.4f" % v for v in la),
                  "longitude": ",".join("%.4f" % v for v in lo)}
        for attempt in range(6):
            try:
                r = requests.get(ELEV_API, params=params, timeout=60)
                if r.status_code == 429:           # 429 = muitas requisicoes; espera mais
                    raise requests.HTTPError("429 rate limit")
                r.raise_for_status()
                out += r.json()["elevation"]
                break
            except Exception as e:
                if attempt == 5:
                    raise
                wait = 20 * (attempt + 1) if "429" in str(e) else 3 * (attempt + 1)
                time.sleep(wait)
        time.sleep(1.2)                            # pausa entre lotes (gentileza com a API)
    return out


def _to_xy(lon, lat):
    """Projecao plana local (em km) em torno da Paraiba: converte graus de lon/lat em km,
    para que a distancia ate a costa saia em quilometros."""
    x = np.asarray(lon) * 111.32 * np.cos(np.radians(LAT0))
    y = np.asarray(lat) * 110.57
    return np.c_[x, y]


def coast_points(lon_thresh=-35.15):
    """Extrai os vertices do contorno do estado que ficam no lado leste (litoral atlantico),
    isto e, com longitude maior que o limiar. Esses vertices representam a linha de costa."""
    mun = gpd.read_file(config.EXTERNAL / "pb_municipios.gpkg").to_crs("EPSG:4326")
    estado = mun.union_all() if hasattr(mun, "union_all") else mun.unary_union  # une os 223 municipios
    geom = estado.boundary
    coords = []
    if geom.geom_type == "LineString":
        coords = list(geom.coords)
    else:
        for g in geom.geoms:
            coords += list(g.coords)
    coast = [(x, y) for (x, y) in coords if x > lon_thresh]
    return np.array(coast)


def add_distance_to_coast(df):
    """Para cada ponto do DataFrame, calcula a distancia (km) ate o ponto de costa mais
    proximo, usando uma arvore de busca (cKDTree) sobre as coordenadas projetadas."""
    coast = coast_points()
    tree = cKDTree(_to_xy(coast[:, 0], coast[:, 1]))
    d, _ = tree.query(_to_xy(df["lon"].values, df["lat"].values), k=1)
    df["dist_coast"] = d  # distancia em km
    return df


def enrich(in_csv, out_csv, label):
    """Acrescenta as colunas elev e dist_coast a um arquivo de pontos. Se a saida ja existe,
    reaproveita (cache), evitando baixar a elevacao de novo."""
    if out_csv.exists():
        df = pd.read_csv(out_csv)
        print("%-10s cached (%d points)" % (label, len(df)))
        return df
    df = pd.read_csv(in_csv)
    df["elev"] = fetch_elevation(df["lat"].tolist(), df["lon"].tolist())
    df = add_distance_to_coast(df)
    df.to_csv(out_csv, index=False)
    print("%-10s n=%4d | elev %.0f-%.0f m | dist_coast %.0f-%.0f km -> %s" %
          (label, len(df), df["elev"].min(), df["elev"].max(),
           df["dist_coast"].min(), df["dist_coast"].max(), out_csv.name))
    return df


def main():
    # Enriquece os tres conjuntos de pontos: NASA, INMET e o MM grid.
    jobs = [
        (config.PROCESSED / "nasa_points.csv", config.PROCESSED / "nasa_points_cov.csv", "nasa"),
        (config.PROCESSED / "inmet_points.csv", config.PROCESSED / "inmet_points_cov.csv", "inmet"),
        (config.PROCESSED / "mm_grid_points.csv", config.PROCESSED / "mm_grid_cov.csv", "mm_grid"),
    ]
    for in_csv, out_csv, label in jobs:
        if in_csv.exists():
            enrich(in_csv, out_csv, label)
        else:
            print("missing:", in_csv)


if __name__ == "__main__":
    main()
