# -*- coding: utf-8 -*-
"""CONTRIBUICAO: figuras. Comparacao dos modelos de interpolacao (Kriging vs ML), mapa da
complementaridade kappa, ranking hibrido vs magnitude e ciclo mensal de vento e sol (para
ilustrar a complementaridade)."""
import sys, os
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in (_ROOT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")   # backend sem janela (apenas salva PNG)
import matplotlib.pyplot as plt
import config

FIG = config.FIGURES


def _municipios():
    """Carrega a malha dos municipios da Paraiba (para os contornos dos mapas)."""
    return gpd.read_file(config.EXTERNAL / "pb_municipios.gpkg").to_crs("EPSG:4326")


def fig_ml_comparison(label="nasa"):
    """Grafico de barras do RMSE de cada modelo (Kriging em cinza, ML em azul), separado em
    vento e radiacao. Mostra onde o aprendizado de maquina melhora a interpolacao."""
    df = pd.read_csv(config.TABLES / ("contrib_ml_%s.csv" % label))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for ax, var in zip(axes, df["Variable"].unique()):
        sub = df[df["Variable"] == var]
        colors = ["0.6" if "paper" in m else "#1f77b4" for m in sub["Model"]]  # cinza = Kriging do artigo
        ax.barh(sub["Model"], sub["RMSE"], color=colors)
        ax.invert_yaxis()
        ax.set_xlabel("RMSE (menor e melhor)")
        ax.set_title(var)
    fig.suptitle("Interpolacao: Kriging do paper (cinza) vs aprendizado de maquina (azul) — %s" % label.upper())
    fig.tight_layout()
    fn = FIG / ("contrib_ml_rmse_%s.png" % label)
    fig.savefig(fn, dpi=130); plt.close(fig)
    print("  saved", fn.name)


def fig_kappa_map(label="nasa"):
    """Mapa da complementaridade kappa em toda a grade: verde = alta (boa para hibrido),
    vermelho = baixa."""
    g = pd.read_csv(config.PROCESSED / ("kappa_grid_%s.csv" % label))
    mun = _municipios()
    fig, ax = plt.subplots(figsize=(8, 5))
    mun.boundary.plot(ax=ax, color="0.6", linewidth=0.4)
    sc = ax.scatter(g["lon"], g["lat"], c=g["kappa"], cmap="RdYlGn", s=6, marker="s")
    plt.colorbar(sc, ax=ax, label="complementaridade kappa (maior = melhor)")
    ax.set_title("Complementaridade temporal vento-sol no MM grid — %s" % label.upper())
    ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude"); ax.set_aspect("equal")
    fig.tight_layout()
    fn = FIG / ("contrib_kappa_%s.png" % label)
    fig.savefig(fn, dpi=130); plt.close(fig)
    print("  saved", fn.name)


def fig_hybrid_vs_magnitude(label="nasa"):
    """Mapa comparando os 10 melhores municipios so por magnitude (azul) com os 10 melhores
    pelo indice hibrido IPH (verde); roxo sao os que aparecem nos dois. Mostra o
    deslocamento causado pela complementaridade."""
    muni = pd.read_csv(config.PROCESSED / ("hybrid_index_%s.csv" % label))
    mun = _municipios(); mun["code"] = mun["code"].astype(str)
    muni["code"] = muni["code"].astype(str)
    top_iph = set(muni.sort_values("IPH", ascending=False).head(10)["code"])
    top_mag = set(muni.sort_values("M", ascending=False).head(10)["code"])
    g = mun.merge(muni, on="code", how="left")
    fig, ax = plt.subplots(figsize=(8, 5))
    g.plot(ax=ax, color="0.92", edgecolor="0.6", linewidth=0.3)
    g[g["code"].isin(top_mag)].plot(ax=ax, color="#1f77b4", edgecolor="k", linewidth=0.3)
    g[g["code"].isin(top_iph)].plot(ax=ax, color="#2ca02c", edgecolor="k", linewidth=0.3)
    g[g["code"].isin(top_iph & top_mag)].plot(ax=ax, color="#9467bd", edgecolor="k", linewidth=0.3)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color="#1f77b4", label="Top-10 so magnitude (paper)"),
                       Patch(color="#2ca02c", label="Top-10 indice hibrido IPH"),
                       Patch(color="#9467bd", label="nos dois")], fontsize=8)
    ax.set_title("Geracao hibrida: magnitude vs magnitude + complementaridade — %s" % label.upper())
    ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude"); ax.set_aspect("equal")
    fig.tight_layout()
    fn = FIG / ("contrib_hybrid_map_%s.png" % label)
    fig.savefig(fn, dpi=130); plt.close(fig)
    print("  saved", fn.name)


def fig_monthly_cycle():
    """Ciclo mensal de vento e sol para dois pontos: o de maior e o de menor kappa. Ilustra
    o conceito de complementaridade (curvas opostas quando kappa e alto)."""
    compl = pd.read_csv(config.PROCESSED / "compl_nasa.csv").dropna(subset=["kappa"])
    hi = compl.loc[compl["kappa"].idxmax()]    # ponto de maior complementaridade
    lo = compl.loc[compl["kappa"].idxmin()]    # ponto de menor complementaridade
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    for ax, pt, tag in zip(axes, [hi, lo], ["maior", "menor"]):
        f = config.RAW / "nasa" / ("nasa_%+.2f_%+.2f.csv" % (pt["lat"], pt["lon"]))
        d = pd.read_csv(f, parse_dates=["date"])
        m = d["date"].dt.month
        mw = d.groupby(m)["WS10M"].mean()
        ms = d.groupby(m)["ALLSKY_SFC_SW_DWN"].mean()
        # normaliza cada serie entre 0 e 1 para comparar as formas no mesmo grafico
        nw = (mw - mw.min()) / (mw.max() - mw.min())
        ns = (ms - ms.min()) / (ms.max() - ms.min())
        ax.plot(nw.index, nw.values, "-o", label="vento", color="#1f77b4")
        ax.plot(ns.index, ns.values, "-s", label="sol", color="#ff7f0e")
        ax.set_title("kappa %s (%.2f) em (%.1f, %.1f)" % (tag, pt["kappa"], pt["lat"], pt["lon"]))
        ax.set_xlabel("mes"); ax.legend(fontsize=8)
    axes[0].set_ylabel("valor mensal normalizado")
    fig.suptitle("Ciclo mensal de vento e sol: complementaridade alta (esq) vs baixa (dir)")
    fig.tight_layout()
    fn = FIG / "contrib_monthly_cycle.png"
    fig.savefig(fn, dpi=130); plt.close(fig)
    print("  saved", fn.name)


def main():
    print("=== contribution figures ===")
    for lbl in ("nasa", "inmet"):
        if (config.TABLES / ("contrib_ml_%s.csv" % lbl)).exists():
            fig_ml_comparison(lbl)
        if (config.PROCESSED / ("kappa_grid_%s.csv" % lbl)).exists():
            fig_kappa_map(lbl)
        if (config.PROCESSED / ("hybrid_index_%s.csv" % lbl)).exists():
            fig_hybrid_vs_magnitude(lbl)
    fig_monthly_cycle()


if __name__ == "__main__":
    main()
