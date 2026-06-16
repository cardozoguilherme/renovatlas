# -*- coding: utf-8 -*-
"""Script de APOIO (investigacao; nao faz parte do pipeline). Explora o catalogo de estacoes
automaticas do INMET: lista as estacoes de PB/CE/PE/RN dentro da caixa de coleta e testa o
formato da API de dados por estacao (que se mostrou instavel, motivando o uso dos zips)."""
import sys, os, json, time, urllib.request
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in (_ROOT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import config


def get_json(url, timeout=60):
    """Baixa e converte um JSON de uma URL."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


stations = get_json(config.INMET_STATIONS_API)
print("catalog keys:", sorted(stations[0].keys()))
sel = [s for s in stations if s.get("SG_ESTADO") in config.INMET_STATES]
bb = config.COLLECT_BBOX


def inbb(s):
    """Verifica se a estacao esta dentro da caixa de coleta."""
    try:
        la = float(s["VL_LATITUDE"]); lo = float(s["VL_LONGITUDE"])
    except Exception:
        return False
    return bb["lat_min"] <= la <= bb["lat_max"] and bb["lon_min"] <= lo <= bb["lon_max"]


selb = [s for s in sel if inbb(s)]
print("PB/CE/PE/RN automatic stations:", len(sel), "| within bbox:", len(selb))
for s in sorted(selb, key=lambda s: (s["SG_ESTADO"], s["DC_NOME"])):
    print("  %s %s (%s,%s) start=%s %s" % (
        s["SG_ESTADO"], s["CD_ESTACAO"], s["VL_LATITUDE"], s["VL_LONGITUDE"],
        str(s.get("DT_INICIO_OPERACAO", ""))[:10], s["DC_NOME"]))

# Testa a API de dados por estacao em uma estacao da PB. Foi assim que descobrimos que ela
# estava instavel, o que levou a usar os zips anuais do portal historico.
pb = [s for s in selb if s["SG_ESTADO"] == "PB"]
if pb:
    cod = pb[0]["CD_ESTACAO"]
    url = "https://apitempo.inmet.gov.br/estacao/2022-01-01/2022-01-03/%s" % cod
    print("\nprobe data API:", url)
    try:
        t0 = time.time()
        data = get_json(url, timeout=60)
        print("OK %.1fs rows=%d" % (time.time() - t0, len(data)))
        if data:
            print("data keys:", sorted(data[0].keys()))
            print("sample row:", {k: data[0][k] for k in list(data[0])[:12]})
    except Exception as e:
        print("data API FAIL:", repr(e)[:160])
