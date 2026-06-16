# -*- coding: utf-8 -*-
"""Gera as figuras que reproduzem o artigo: mapas do MM grid (Figs 5-8), dispersao dos
municipios no plano vento x solar com os grupos (Figs 10-13), mapa dos 10 melhores
municipios (Figs 14-15) e a correlacao do IP-PB entre NASA e INMET (Fig 16).

Etapa de FIGURAS (reproducao). Usa o backend "Agg" do matplotlib para salvar PNG sem
abrir janela.
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
import matplotlib
matplotlib.use("Agg")   # backend sem interface grafica (apenas salva arquivos)
import matplotlib.pyplot as plt
import config

# Cores de cada grupo (rotulo Vento/Solar) usadas na dispersao.
GROUP_COLORS = {"Good/Good": "#2ca02c", "Good/Bad": "#1f77b4",
                "Bad/Good": "#ff7f0e", "Bad/Bad": "#d62728"}


def _municipios():
    """Carrega a malha dos municipios da Paraiba (para desenhar os contornos nos mapas)."""
    return gpd.read_file(config.EXTERNAL / "pb_municipios.gpkg").to_crs("EPSG:4326")


def plot_mm_maps(label):
    """Desenha os mapas do MM grid: um para a radiacao solar e outro para o vento, com os
    pontos da grade coloridos pelo valor e o contorno dos municipios por cima."""
    mm = pd.read_csv(config.PROCESSED / ("mm_grid_%s.csv" % label))
    mun = _municipios()
    specs = [(config.SOLAR, "SOLAR_IRRAD (kWh/m2/day)", "YlOrRd"),
             (config.WIND, "WIND_SPEED (m/s)", "viridis")]
    for col, title, cmap in specs:
        fig, ax = plt.subplots(figsize=(8, 5))
        mun.boundary.plot(ax=ax, color="0.6", linewidth=0.4)
        sc = ax.scatter(mm["lon"], mm["lat"], c=mm[col], cmap=cmap, s=6, marker="s")
        plt.colorbar(sc, ax=ax, label=title)
        ax.set_title("MM grid (%s) — %s" % (label.upper(), title))
        ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
        ax.set_aspect("equal")
        fn = config.FIGURES / ("mm_%s_%s.png" % (label, col))
        fig.tight_layout(); fig.savefig(fn, dpi=130); plt.close(fig)
        print("  saved", fn.name)


def plot_scatter(label):
    """Dispersao dos municipios no plano vento (x) contra solar (y), com cada grupo numa cor
    e as linhas das medianas. Evidencia o padrao de troca entre as duas fontes."""
    muni = pd.read_csv(config.PROCESSED / ("ip_pb_%s.csv" % label))
    mx, my = muni["x"].median(), muni["y"].median()
    fig, ax = plt.subplots(figsize=(6.2, 6))
    for grp, c in GROUP_COLORS.items():
        s = muni[muni["group"] == grp]
        ax.scatter(s["x"], s["y"], c=c, s=18, label="%s (n=%d)" % (grp, len(s)), alpha=0.8)
    ax.axvline(mx, color="k", lw=0.8); ax.axhline(my, color="k", lw=0.8)  # linhas das medianas
    ax.set_xlabel("WIND_SPEED (normalized)"); ax.set_ylabel("SOLAR_IRRAD (normalized)")
    ax.set_title("IP-PB municipalities (%s) — groups Wind/Solar" % label.upper())
    ax.legend(fontsize=8, loc="lower left")
    fn = config.FIGURES / ("scatter_ippb_%s.png" % label)
    fig.tight_layout(); fig.savefig(fn, dpi=130); plt.close(fig)
    print("  saved", fn.name)


def plot_top10_map(label):
    """Mapa destacando os 10 melhores municipios para solar (laranja), vento (azul) e
    hibrido (verde) sobre o contorno do estado."""
    muni = pd.read_csv(config.PROCESSED / ("ip_pb_%s.csv" % label))
    mun = _municipios()
    mun["code"] = mun["code"].astype(str); muni["code"] = muni["code"].astype(str)
    g = mun.merge(muni, on="code", how="left")
    solar_top = set(muni.sort_values("SOLAR_IRRAD", ascending=False).head(10)["code"])
    wind_top = set(muni.sort_values("WIND_SPEED", ascending=False).head(10)["code"])
    hyb_top = set(muni[muni["group"] == "Good/Good"].sort_values("IP_PB", ascending=False).head(10)["code"])
    fig, ax = plt.subplots(figsize=(8, 5))
    g.plot(ax=ax, color="0.92", edgecolor="0.6", linewidth=0.3)
    for codes, color, lbl in [(solar_top, "#ff7f0e", "Top solar"),
                              (wind_top, "#1f77b4", "Top wind"),
                              (hyb_top, "#2ca02c", "Top hybrid")]:
        g[g["code"].isin(codes)].plot(ax=ax, color=color, edgecolor="k",
                                      linewidth=0.3, label=lbl, alpha=0.8)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color="#ff7f0e", label="Top-10 solar"),
                       Patch(color="#1f77b4", label="Top-10 wind"),
                       Patch(color="#2ca02c", label="Top-10 hybrid")], fontsize=8)
    ax.set_title("Top-10 municipalities (%s)" % label.upper())
    ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude"); ax.set_aspect("equal")
    fn = config.FIGURES / ("top10_%s.png" % label)
    fig.tight_layout(); fig.savefig(fn, dpi=130); plt.close(fig)
    print("  saved", fn.name)


def plot_correlation():
    """Dispersao do IP-PB de cada municipio calculado com NASA (x) contra INMET (y), com a
    reta de igualdade. Mostra o quanto as duas bases concordam (correlacao r)."""
    fn_n = config.PROCESSED / "ip_pb_nasa.csv"
    fn_i = config.PROCESSED / "ip_pb_inmet.csv"
    if not (fn_n.exists() and fn_i.exists()):
        print("  (need both NASA and INMET IP-PB for correlation plot)")
        return
    n = pd.read_csv(fn_n)[["code", "name", "IP_PB"]].rename(columns={"IP_PB": "IP_NASA"})
    i = pd.read_csv(fn_i)[["code", "IP_PB"]].rename(columns={"IP_PB": "IP_INMET"})
    n["code"] = n["code"].astype(str); i["code"] = i["code"].astype(str)
    m = n.merge(i, on="code")
    r = np.corrcoef(m["IP_NASA"], m["IP_INMET"])[0, 1]
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(m["IP_NASA"], m["IP_INMET"], s=16, alpha=0.7)
    lim = [min(m["IP_NASA"].min(), m["IP_INMET"].min()), max(m["IP_NASA"].max(), m["IP_INMET"].max())]
    ax.plot(lim, lim, "k--", lw=1, label="equality")  # reta y=x (concordancia perfeita)
    ax.set_xlabel("IP-PB (NASA)"); ax.set_ylabel("IP-PB (INMET)")
    ax.set_title("IP-PB correlation NASA vs INMET (r=%.3f)" % r)
    ax.legend(fontsize=9)
    fn = config.FIGURES / "correlation_ippb.png"
    fig.tight_layout(); fig.savefig(fn, dpi=130); plt.close(fig)
    print("  saved", fn.name, "| r=%.3f" % r)
    return r


def run(label):
    """Gera os mapas e a dispersao de uma base (nasa ou inmet)."""
    print("=== plots:", label, "===")
    plot_mm_maps(label)
    plot_scatter(label)
    plot_top10_map(label)


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    labels = ["nasa", "inmet"] if which == "all" else [which]
    for lbl in labels:
        if (config.PROCESSED / ("mm_grid_%s.csv" % lbl)).exists():
            run(lbl)
    plot_correlation()
