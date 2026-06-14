# -*- coding: utf-8 -*-
"""Dashboard interativo do RenovAtlas (Streamlit).

Mostra: mapa de potencial (vento, sol, IP-PB e indice hibrido), comparacao das metricas
dos modelos treinados (rastreados no MLflow), previsao interativa por coordenada e os
rankings de municipios.
"""
import sys, os
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in (_ROOT, os.path.join(_ROOT, "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
import pandas as pd
import joblib
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.spatial import cKDTree
import streamlit as st
import config

st.set_page_config(page_title="RenovAtlas", layout="wide")
P = config.PROCESSED
T = config.TABLES
FEATURES = ["lon", "lat", "elev", "dist_coast"]


@st.cache_data
def load_csv(path):
    return pd.read_csv(path) if os.path.exists(path) else None


@st.cache_data
def load_municipios():
    return gpd.read_file(config.EXTERNAL / "pb_municipios.gpkg").to_crs("EPSG:4326")


@st.cache_resource
def load_model(source, target):
    fn = config.ROOT / "models" / ("best_%s_%s.joblib" % (source, target))
    return joblib.load(fn) if fn.exists() else None


def map_layer(mun, pts, value, title, cmap):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    mun.boundary.plot(ax=ax, color="0.6", linewidth=0.4)
    sc = ax.scatter(pts["lon"], pts["lat"], c=value, cmap=cmap, s=7, marker="s")
    plt.colorbar(sc, ax=ax, label=title)
    ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude"); ax.set_aspect("equal")
    ax.set_title(title)
    fig.tight_layout()
    return fig


st.title("RenovAtlas")
st.caption("Potencial de geração de energia renovável (solar, eólica e híbrida) na Paraíba")

tab_map, tab_models, tab_pred, tab_rank = st.tabs(
    ["Mapa de potencial", "Modelos", "Previsão", "Rankings"])

# ---------------------------------------------------------------- Mapa
with tab_map:
    c1, c2 = st.columns(2)
    source = c1.selectbox("Base de dados", ["nasa", "inmet"], key="map_src")
    layer = c2.selectbox("Camada", ["SOLAR_IRRAD", "WIND_SPEED", "IP-PB", "IP-Hibrido (IPH)"], key="map_layer")
    mun = load_municipios()
    if layer in ("SOLAR_IRRAD", "WIND_SPEED"):
        grid = load_csv(P / ("mm_grid_%s.csv" % source))
        if grid is not None:
            cmap = "YlOrRd" if layer == "SOLAR_IRRAD" else "viridis"
            st.pyplot(map_layer(mun, grid, grid[layer], "%s (%s)" % (layer, source.upper()), cmap))
    elif layer == "IP-PB":
        muni = load_csv(P / ("ip_pb_%s.csv" % source))
        g = mun.merge(muni.astype({"code": str}), left_on="code", right_on="code", how="left")
        fig, ax = plt.subplots(figsize=(7, 4.5))
        g.plot(ax=ax, column="IP_PB", cmap="plasma", legend=True, edgecolor="0.7", linewidth=0.3)
        ax.set_title("IP-PB por municipio (%s)" % source.upper()); ax.set_aspect("equal")
        st.pyplot(fig)
    else:
        muni = load_csv(P / ("hybrid_index_%s.csv" % source))
        g = mun.merge(muni.astype({"code": str}), on="code", how="left")
        fig, ax = plt.subplots(figsize=(7, 4.5))
        g.plot(ax=ax, column="IPH", cmap="plasma", legend=True, edgecolor="0.7", linewidth=0.3)
        ax.set_title("Indice hibrido IPH por municipio (%s)" % source.upper()); ax.set_aspect("equal")
        st.pyplot(fig)

# ---------------------------------------------------------------- Modelos
with tab_models:
    st.subheader("Comparação dos modelos (rastreado no MLflow)")
    cmp = load_csv(T / "model_comparison.csv")
    if cmp is not None:
        st.dataframe(cmp, width="stretch")
        c1, c2 = st.columns(2)
        src = c1.selectbox("Base", sorted(cmp["source"].unique()), key="mdl_src")
        tgt = c2.selectbox("Variável", sorted(cmp["target"].unique()), key="mdl_tgt")
        sub = cmp[(cmp["source"] == src) & (cmp["target"] == tgt)].set_index("model")
        cc1, cc2 = st.columns(2)
        cc1.bar_chart(sub["test_rmse"])
        cc2.bar_chart(sub["test_r2"])
    else:
        st.info("Rode `python src/train.py` para gerar a comparação de modelos.")

# ---------------------------------------------------------------- Previsão
with tab_pred:
    st.subheader("Previsão por coordenada")
    b = config.PB_BBOX
    c1, c2 = st.columns(2)
    lat = c1.slider("Latitude", float(b["lat_min"]), float(b["lat_max"]), -7.12, 0.01)
    lon = c2.slider("Longitude", float(b["lon_min"]), float(b["lon_max"]), -35.0, 0.01)
    cov = load_csv(P / "mm_grid_cov.csv")
    if cov is not None:
        tree = cKDTree(cov[["lon", "lat"]].values)
        _, idx = tree.query([lon, lat], k=1)
        near = cov.iloc[idx]
        feat = pd.DataFrame([[near["lon"], near["lat"], near["elev"], near["dist_coast"]]], columns=FEATURES)
        st.write("Ponto de grade mais próximo: elevação %.0f m, distância à costa %.0f km" %
                 (near["elev"], near["dist_coast"]))
        cols = st.columns(2)
        for i, target in enumerate((config.WIND, config.SOLAR)):
            model = load_model("nasa", target)
            if model is not None:
                pred = float(model.predict(feat.values)[0])
                unit = "m/s" if target == config.WIND else "kWh/m²/dia"
                cols[i].metric(target, "%.2f %s" % (pred, unit))
            else:
                cols[i].info("Modelo não encontrado. Rode src/train.py.")

# ---------------------------------------------------------------- Rankings
with tab_rank:
    src = st.selectbox("Base de dados", ["nasa", "inmet"], key="rank_src")
    cols = st.columns(3)
    for col, kind, title in zip(cols, ["solar", "wind", "hybridplus"],
                                ["Solar", "Eólico", "Híbrido (IPH)"]):
        r = load_csv(T / ("rank_%s_%s.csv" % (kind, src)))
        col.markdown("**Top 10 " + title + "**")
        if r is not None:
            col.dataframe(r[["name"]].head(10), width="stretch", hide_index=True)
        else:
            col.info("indisponível")
