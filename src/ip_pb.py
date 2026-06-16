# -*- coding: utf-8 -*-
"""Indice de Potencial de Geracao Hibrida da Paraiba (IP-PB).

Etapas (Secoes 2.4 e 4.2 do artigo):
  1. Normaliza WIND_SPEED (eixo x) e SOLAR_IRRAD (eixo y) entre 0 e 1, sobre o MM grid (Eq.7).
  2. Agrupa os pontos do MM grid por municipio (media de x e y) -> 223 municipios.
  3. IP-PB = raiz(x^2 + y^2)  (norma euclidiana; maximo raiz(2) ~ 1,4142).
  4. Divide os municipios pelas medianas de x e y em quatro grupos (Bom/Ruim para vento x
     Bom/Ruim para solar) e monta os rankings dos 10 melhores para solar, vento e hibrido.

Etapa do INDICE IP-PB (reproducao).
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
    """Normaliza as variaveis, agrupa por municipio, calcula o IP-PB e separa os municipios
    em grupos pelas medianas. Salva ip_pb_<label>.csv e devolve a tabela por municipio."""
    mm = pd.read_csv(mm_csv)
    mm["code"] = mm["code"].astype(str)
    # Normalizacao Max-Min (Eq. 7): coloca vento (x) e radiacao (y) entre 0 e 1.
    wmin, wmax = mm[W].min(), mm[W].max()
    smin, smax = mm[S].min(), mm[S].max()
    mm["x"] = (mm[W] - wmin) / (wmax - wmin)
    mm["y"] = (mm[S] - smin) / (smax - smin)
    # Agrupa os pontos da grade por municipio (media), reduzindo a ~223 municipios.
    muni = (mm.groupby(["code", "name"])
            .agg(x=("x", "mean"), y=("y", "mean"), WIND_SPEED=(W, "mean"),
                 SOLAR_IRRAD=(S, "mean"), n_points=("x", "size")).reset_index())

    # Municipios pequenos que nao receberam nenhum ponto da grade sao preenchidos pelo valor
    # interpolado no seu centroide, para fechar os 223 municipios.
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

    # IP-PB = norma euclidiana do ponto (x, y): premia quem tem bom vento E bom sol.
    muni["IP_PB"] = np.sqrt(muni["x"] ** 2 + muni["y"] ** 2)
    # Divide os municipios pela mediana de cada eixo em Bom/Ruim, formando 4 grupos.
    mx, my = muni["x"].median(), muni["y"].median()
    muni["wind_cls"] = np.where(muni["x"] >= mx, "Good", "Bad")
    muni["solar_cls"] = np.where(muni["y"] >= my, "Good", "Bad")
    muni["group"] = muni["wind_cls"] + "/" + muni["solar_cls"]  # rotulo no formato Vento/Solar
    muni = muni.sort_values("IP_PB", ascending=False).reset_index(drop=True)
    muni.to_csv(config.PROCESSED / ("ip_pb_%s.csv" % label), index=False)
    print("  IP-PB %s: municipalities=%d  median(x,y)=(%.3f,%.3f)  IP-PB max=%.4f" %
          (label, len(muni), mx, my, muni["IP_PB"].max()))
    print("  group counts:", muni["group"].value_counts().to_dict())
    return muni


def rankings(muni, label):
    """Monta os rankings dos 10 melhores municipios: solar (maior radiacao entre os de bom
    sol), vento (maior vento entre os de bom vento) e hibrido (maior IP-PB no grupo
    Bom/Bom). Salva cada ranking em outputs/tables."""
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
    """Roda o calculo do IP-PB e os rankings para uma base (nasa ou inmet)."""
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
