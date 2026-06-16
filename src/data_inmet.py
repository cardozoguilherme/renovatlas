# -*- coding: utf-8 -*-
"""Coleta os dados horarios das estacoes automaticas do INMET (vento em m/s e radiacao
global em kJ/m2) para a Paraiba e estados vizinhos (PB, CE, PE, RN), a partir dos arquivos
zip anuais do portal historico. Salva um CSV por estacao, com [datetime_utc, rad_kj, wind].
O leitor e robusto as mudancas de formato dos CSVs ao longo dos anos.

Etapa de COLETA (reproducao). A API estacao a estacao do INMET e instavel, por isso usamos
os zips anuais, mais confiaveis.
"""
import sys, os, io, zipfile, time
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in (_ROOT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import numpy as np
import pandas as pd
import requests
import config

INMET_DIR = config.RAW / "inmet"
INMET_DIR.mkdir(parents=True, exist_ok=True)
KEEP_ZIPS = True  # manter os zips anuais em cache (ja baixados e validos)


def select_stations():
    """Baixa o catalogo de estacoes automaticas do INMET e seleciona as que estao nos
    estados de interesse e dentro da caixa de coleta. Salva e devolve um DataFrame com
    codigo, nome, UF, latitude, longitude e data de inicio de cada estacao."""
    r = requests.get(config.INMET_STATIONS_API, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    cat = r.json()
    bb = config.COLLECT_BBOX
    rows = []
    for s in cat:
        if s.get("SG_ESTADO") not in config.INMET_STATES:
            continue
        try:
            la = float(s["VL_LATITUDE"]); lo = float(s["VL_LONGITUDE"])
        except Exception:
            continue                         # estacao sem coordenada valida: ignora
        if not (bb["lat_min"] <= la <= bb["lat_max"] and bb["lon_min"] <= lo <= bb["lon_max"]):
            continue                         # fora da caixa de coleta: ignora
        rows.append(dict(code=s["CD_ESTACAO"], name=s["DC_NOME"], uf=s["SG_ESTADO"],
                         lat=la, lon=lo, start=str(s.get("DT_INICIO_OPERACAO", ""))[:10]))
    df = pd.DataFrame(rows).sort_values(["uf", "name"]).reset_index(drop=True)
    df.to_csv(INMET_DIR / "_stations.csv", index=False)
    return df


def download_year(year):
    """Baixa (ou reaproveita do cache) o zip historico de um ano. Os zips ficam em
    data/external. Retorna o caminho do arquivo."""
    zpath = config.EXTERNAL / ("inmet_%d.zip" % year)
    if zpath.exists() and zpath.stat().st_size > 1000:
        return zpath                         # ja existe: usa o cache
    r = requests.get(config.INMET_HIST_URL.format(year=year), timeout=600,
                     headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    zpath.write_bytes(r.content)
    return zpath


def _find_col(cols, *subs):
    """Acha o nome de uma coluna que contenha todos os trechos 'subs' (sem diferenciar
    maiusculas). Util porque os nomes das colunas do INMET variam de ano para ano."""
    up = {c.upper(): c for c in cols}
    for cu, c in up.items():
        if all(s in cu for s in subs):
            return c
    return None


def parse_inmet_csv(raw):
    """Le o conteudo de um CSV do INMET (em bytes) e devolve um DataFrame com as colunas
    datetime_utc, rad_kj (radiacao em kJ/m2) e wind (vento em m/s). Trata as variacoes de
    formato entre anos (cabecalho, separador de data, decimal com virgula)."""
    text = raw.decode("latin-1")             # os CSVs do INMET usam codificacao latin-1
    lines = text.splitlines()
    # Acha a linha de cabecalho das colunas (a que comeca com 'Data'); o topo do arquivo
    # tem ~8 linhas de metadados (regiao, UF, estacao, latitude, etc.).
    hidx = next((i for i, l in enumerate(lines[:15])
                 if l.upper().replace('"', '').startswith("DATA;")), 8)
    df = pd.read_csv(io.StringIO("\n".join(lines[hidx:])), sep=";", dtype=str,
                     keep_default_na=False, engine="python")
    df = df.loc[:, [c for c in df.columns if not c.startswith("Unnamed")]]
    # Localiza as colunas de interesse pelo nome.
    c_data = _find_col(df.columns, "DATA")
    c_hora = _find_col(df.columns, "HORA")
    c_rad = _find_col(df.columns, "RADIACAO", "GLOBAL")
    c_wind = _find_col(df.columns, "VELOCIDADE", "HORARIA")
    if not all([c_data, c_hora, c_wind]):
        return None                          # arquivo sem as colunas esperadas
    out = pd.DataFrame()
    ds = df[c_data].str.strip().str.replace("-", "/", regex=False)
    # Detecta o formato da data: ano primeiro (YYYY/MM/DD, formato antigo usava '-') se o
    # primeiro pedaco tem 4 digitos; senao, dia primeiro (DD/MM/YYYY).
    fmt = "%Y/%m/%d" if str(ds.iloc[0])[:4].isdigit() else "%d/%m/%Y"
    date = pd.to_datetime(ds, format=fmt, errors="coerce")
    hour = df[c_hora].str.extract(r"(\d{2})", expand=False).astype(float)  # pega a hora (2 digitos)
    out["datetime_utc"] = date + pd.to_timedelta(hour, unit="h")           # data + hora (em UTC)

    def tonum(col):
        # Converte texto em numero. O INMET usa virgula como decimal; trocamos por ponto.
        # to_numeric(coerce) ja transforma "" em NaN, entao nao precisa de replace extra.
        return pd.to_numeric(df[col].str.replace(",", ".", regex=False), errors="coerce")
    out["rad_kj"] = tonum(c_rad) if c_rad else np.nan
    out["wind"] = tonum(c_wind)
    for c in ("rad_kj", "wind"):
        out.loc[out[c] < 0, c] = np.nan      # valores negativos (-9999 = sem dado) viram NaN
    return out.dropna(subset=["datetime_utc"])


def process(years, stations):
    """Para cada ano: baixa o zip, acha o CSV de cada estacao de interesse, parseia e
    acumula. No fim, junta todos os anos por estacao e salva um CSV por estacao."""
    codes = set(stations["code"])
    acc = {c: [] for c in codes}             # acumula os DataFrames de cada estacao
    for year in years:
        try:
            zpath = download_year(year)
        except Exception as e:
            print("year %d download FAIL: %s" % (year, repr(e)[:100]))
            continue
        try:
            with zipfile.ZipFile(zpath) as zf:   # 'with' garante o fechamento do arquivo
                members = [n for n in zf.namelist() if n.lower().endswith(".csv")]
                got = 0
                for code in codes:
                    # acha o CSV da estacao pelo codigo no nome do arquivo (ex: "_A310_")
                    hit = next((m for m in members if ("_%s_" % code) in m.upper()), None)
                    if not hit:
                        continue
                    try:
                        parsed = parse_inmet_csv(zf.read(hit))
                    except Exception as e:
                        print("  parse FAIL %s %d: %s" % (code, year, repr(e)[:80]))
                        continue
                    if parsed is not None and len(parsed):
                        acc[code].append(parsed)
                        got += 1
            print("year %d: %d/%d stations parsed (members=%d)" % (year, got, len(codes), len(members)))
        except Exception as e:
            print("year %d process FAIL: %s" % (year, repr(e)[:120]))
        finally:
            if not KEEP_ZIPS:                # se nao for manter o cache, apaga o zip do ano
                try:
                    os.remove(zpath)
                except OSError:
                    pass
    # Junta todos os anos de cada estacao, remove horarios repetidos e salva um CSV por estacao.
    saved = 0
    for code, parts in acc.items():
        if not parts:
            continue
        full = pd.concat(parts, ignore_index=True).sort_values("datetime_utc")
        full = full.drop_duplicates(subset=["datetime_utc"])
        full.to_csv(INMET_DIR / ("%s.csv" % code), index=False)
        saved += 1
    print("DONE saved %d stations -> %s" % (saved, INMET_DIR))


def main():
    """Coleta os anos de 2003 a 2022. Aceita anos especificos por argumento, para teste
    (ex: "python data_inmet.py 2021")."""
    years = range(2003, 2023)
    if len(sys.argv) > 1:
        years = [int(a) for a in sys.argv[1:]]
    st = select_stations()
    print("stations selected:", len(st), "| years:", list(years)[0], "-", list(years)[-1])
    process(years, st)


if __name__ == "__main__":
    main()
