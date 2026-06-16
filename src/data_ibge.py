# -*- coding: utf-8 -*-
"""Baixa a malha municipal da Paraiba do IBGE (os 223 municipios) em GeoJSON, anexa o
nome de cada municipio e salva um GeoPackage (.gpkg) para uso no restante do projeto
(recorte da grade, agrupamento por municipio e desenho dos mapas).

Etapa de COLETA (reproducao). Fonte: API de malhas do IBGE.
"""
import sys, os, json
# Permite importar o config.py (que fica na pasta acima de src/), independentemente de
# onde o script seja executado: adiciona a raiz do projeto e a pasta src ao sys.path.
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in (_ROOT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import requests
import geopandas as gpd
import config


def _get(url, timeout=120):
    """Faz uma requisicao HTTP GET e devolve a resposta ja convertida de JSON.
    O cabecalho User-Agent evita bloqueio pelo servidor; raise_for_status() lanca erro
    se a resposta nao for bem-sucedida (codigo diferente de 2xx)."""
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout)
    r.raise_for_status()
    return r.json()


def main():
    geojson_path = config.EXTERNAL / "pb_municipios.geojson"
    # Baixa a malha (os poligonos) e a lista de municipios (para mapear codigo -> nome).
    gj = _get(config.IBGE_MALHA_URL)
    muns = _get(config.IBGE_MUNICIPIOS_URL)
    code2name = {str(m["id"]): m["nome"] for m in muns}
    # A malha so traz o codigo de cada municipio; aqui anexamos tambem o codigo e o nome.
    for f in gj["features"]:
        code = str(f["properties"].get("codarea"))
        f["properties"]["code"] = code
        f["properties"]["name"] = code2name.get(code, code)
    # Salva o GeoJSON ja com os nomes.
    with open(geojson_path, "w", encoding="utf-8") as fh:
        json.dump(gj, fh, ensure_ascii=False)

    # Le com o geopandas e padroniza o sistema de coordenadas para WGS84 (EPSG:4326), o
    # mesmo das latitudes/longitudes do projeto. O IBGE usa SIRGAS 2000 (EPSG:4674), que
    # e praticamente identico ao WGS84 para esta finalidade.
    gdf = gpd.read_file(geojson_path)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4674")
    gdf = gdf.to_crs("EPSG:4326")
    # Salva em GeoPackage, formato mais pratico para o restante do projeto.
    gpkg = config.EXTERNAL / "pb_municipios.gpkg"
    gdf.to_file(gpkg, driver="GPKG")
    print("municipios:", len(gdf))
    print("sample:", gdf[["code", "name"]].head(3).to_dict("records"))
    print("bounds (lon_min, lat_min, lon_max, lat_max):", [round(x, 3) for x in gdf.total_bounds])
    print("saved ->", gpkg)


if __name__ == "__main__":
    main()
