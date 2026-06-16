# -*- coding: utf-8 -*-
"""Script de APOIO (investigacao; nao faz parte do pipeline). Baixa um zip anual do INMET e
inspeciona a estrutura de um CSV (cabecalho e colunas), para descobrir o formato dos
arquivos. Foi assim que identificamos o separador, a codificacao e os nomes das colunas."""
import sys, os, zipfile
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in (_ROOT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import requests
import config

year = int(sys.argv[1]) if len(sys.argv) > 1 else 2021   # ano a inspecionar (padrao 2021)
zpath = config.EXTERNAL / ("inmet_%d.zip" % year)
if not zpath.exists():
    print("downloading", year, "...")
    r = requests.get(config.INMET_HIST_URL.format(year=year), timeout=300,
                     headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    zpath.write_bytes(r.content)
print("zip size MB:", round(zpath.stat().st_size / 1e6, 1))

zf = zipfile.ZipFile(zpath)
names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
print("csv files in zip:", len(names))
print("first 5 names:")
for n in names[:5]:
    print("   ", n)
pb = [n for n in names if "_PB_" in n.upper()]
a310 = [n for n in names if "A310" in n.upper() or "AREIA" in n.upper()]
print("PB files:", len(pb), "| files matching A310/AREIA:", len(a310))
for n in (pb or a310)[:10]:
    print("  ", os.path.basename(n))

# Mostra o cabecalho e as primeiras linhas de um CSV da PB, para revelar o formato.
sample = [n for n in pb if "A310" in n] or pb[:1]
if sample:
    raw = zf.read(sample[0]).decode("latin-1")
    lines = raw.splitlines()
    print("\n=== HEADER (first 9 lines) of", os.path.basename(sample[0]), "===")
    for l in lines[:9]:
        print(repr(l))
    print("\n=== COLUMN line (line 9, idx 8) ===")
    print(repr(lines[8]))
    print("\n=== first data rows ===")
    for l in lines[9:12]:
        print(repr(l))
