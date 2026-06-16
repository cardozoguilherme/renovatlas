# -*- coding: utf-8 -*-
"""CONTRIBUICAO (combina Ideias 1 e 2): indice de geracao hibrida melhorado (IPH).

Junta as duas contribuicoes:
  - Ideia 2: a magnitude do recurso usa a melhor interpolacao encontrada (solar por
    Random Forest, vento por Kriging), em vez de so o Kriging do artigo.
  - Ideia 1: alem da magnitude, o indice considera a complementaridade temporal kappa.

Definicoes:
  M       = sqrt(x^2 + y^2)        magnitude combinada (igual ao IP-PB do artigo)
  M_norm  = M / sqrt(2)            magnitude em [0, 1]
  IPH     = M_norm * (1 + kappa)   indice hibrido; a complementaridade da um bonus de ate 2x

O ranking por IPH e comparado ao ranking so por magnitude (M), o que mostra quais
municipios sobem quando a complementaridade temporal e levada em conta.
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
from scipy.spatial import cKDTree
import config

W, S = config.WIND, config.SOLAR


def build_best_grid(label):
    """Monta a grade de magnitude com a melhor interpolacao de cada variavel: o vento vem do
    Kriging (mm_grid) e a radiacao vem do Random Forest (mm_grid_ml), conforme a analise de
    ML indicou ser melhor para cada uma."""
    krig = pd.read_csv(config.PROCESSED / ("mm_grid_%s.csv" % label))
    ml = pd.read_csv(config.PROCESSED / ("mm_grid_ml_%s.csv" % label))
    best = krig[["lon", "lat", "name", "code", W]].copy()        # vento do Kriging
    best = best.merge(ml[["lon", "lat", S]], on=["lon", "lat"])  # solar do Random Forest
    return best


def compute_hybrid(label):
    """Calcula o indice hibrido IPH por municipio: normaliza vento e solar, junta com a
    complementaridade kappa, combina tudo e compara o ranking com o de so magnitude. Salva
    hybrid_index_<label>.csv e o ranking top-10."""
    g = build_best_grid(label)
    kappa = pd.read_csv(config.PROCESSED / ("kappa_grid_%s.csv" % label))[["lon", "lat", "kappa"]]
    g = g.merge(kappa, on=["lon", "lat"])
    g["code"] = g["code"].astype(str)
    # normaliza vento (x) e solar (y) entre 0 e 1, sobre toda a grade
    g["x"] = (g[W] - g[W].min()) / (g[W].max() - g[W].min())
    g["y"] = (g[S] - g[S].min()) / (g[S].max() - g[S].min())
    # agrupa por municipio (media de x, y e kappa)
    muni = (g.groupby(["code", "name"])
            .agg(x=("x", "mean"), y=("y", "mean"), kappa=("kappa", "mean"),
                 WIND_SPEED=(W, "mean"), SOLAR_IRRAD=(S, "mean")).reset_index())
    # municipios sem ponto de grade recebem os valores do ponto de grade mais proximo do centroide
    mun = gpd.read_file(config.EXTERNAL / "pb_municipios.gpkg").to_crs("EPSG:4326")
    mun["code"] = mun["code"].astype(str)
    missing = mun[~mun["code"].isin(set(muni["code"]))]
    if len(missing):
        # centroide calculado em CRS metrico (UTM 25S) e convertido de volta para lon/lat
        cent = missing.to_crs("EPSG:31985").geometry.centroid.to_crs("EPSG:4326")
        tree = cKDTree(g[["lon", "lat"]].values)
        _, idx = tree.query(np.c_[cent.x.values, cent.y.values], k=1)
        add = pd.DataFrame({
            "code": missing["code"].values, "name": missing["name"].values,
            "x": g["x"].values[idx], "y": g["y"].values[idx], "kappa": g["kappa"].values[idx],
            "WIND_SPEED": g[W].values[idx], "SOLAR_IRRAD": g[S].values[idx]})
        muni = pd.concat([muni, add], ignore_index=True)

    # magnitude (o IP-PB do artigo) e indice hibrido (a contribuicao)
    muni["M"] = np.sqrt(muni["x"] ** 2 + muni["y"] ** 2)
    muni["M_norm"] = muni["M"] / np.sqrt(2)
    muni["IPH"] = muni["M_norm"] * (1.0 + muni["kappa"])   # magnitude com bonus de complementaridade
    muni["IPH_norm"] = muni["IPH"] / muni["IPH"].max()
    # rankings (posicao 1 = melhor)
    muni["rank_M"] = muni["M"].rank(ascending=False, method="min").astype(int)
    muni["rank_IPH"] = muni["IPH"].rank(ascending=False, method="min").astype(int)
    muni["delta_rank"] = muni["rank_M"] - muni["rank_IPH"]   # positivo = subiu ao incluir a complementaridade
    muni = muni.sort_values("IPH", ascending=False).reset_index(drop=True)
    muni.to_csv(config.PROCESSED / ("hybrid_index_%s.csv" % label), index=False)

    top_iph = muni.head(10)[["name", "IPH_norm", "M_norm", "kappa", "rank_M"]]
    top_mag = muni.sort_values("M", ascending=False).head(10)[["name", "M_norm", "kappa"]]
    top_iph.to_csv(config.TABLES / ("rank_hybridplus_%s.csv" % label), index=False)
    # municipios que mais subiram no ranking ao incluir a complementaridade
    risers = muni.sort_values("delta_rank", ascending=False).head(8)[
        ["name", "delta_rank", "rank_M", "rank_IPH", "kappa", "M_norm"]]

    print("=== Hybrid index (%s) ===" % label.upper())
    print("  TOP-10 by magnitude only (IP-PB / paper):")
    print("   ", ", ".join(top_mag["name"].tolist()))
    print("  TOP-10 by hybrid index IPH (magnitude + complementarity):")
    print("   ", ", ".join(top_iph["name"].tolist()))
    print("  Biggest climbers when complementarity is added (name: +positions, kappa):")
    for _, r in risers.iterrows():
        print("    %-22s +%d (kappa=%.2f)" % (r["name"], int(r["delta_rank"]), r["kappa"]))
    return muni


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    labels = ["nasa", "inmet"] if which == "all" else [which]
    for lbl in labels:
        # precisa do MM grid (Kriging), do MM grid por ML e da grade de kappa
        need = [config.PROCESSED / ("mm_grid_%s.csv" % lbl),
                config.PROCESSED / ("mm_grid_ml_%s.csv" % lbl),
                config.PROCESSED / ("kappa_grid_%s.csv" % lbl)]
        if all(p.exists() for p in need):
            compute_hybrid(lbl)
        else:
            print("missing inputs for", lbl)


if __name__ == "__main__":
    main()
