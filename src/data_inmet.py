# -*- coding: utf-8 -*-
"""Collect INMET automatic-station hourly data (wind speed m/s, global radiation
kJ/m2) for PB/CE/PE/RN stations from the yearly historical zips. One CSV per
station with [datetime_utc, rad_kj, wind]. Robust to format changes across years."""
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
KEEP_ZIPS = True  # keep yearly zips cached (already downloaded & valid)


def select_stations():
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
            continue
        if not (bb["lat_min"] <= la <= bb["lat_max"] and bb["lon_min"] <= lo <= bb["lon_max"]):
            continue
        rows.append(dict(code=s["CD_ESTACAO"], name=s["DC_NOME"], uf=s["SG_ESTADO"],
                         lat=la, lon=lo, start=str(s.get("DT_INICIO_OPERACAO", ""))[:10]))
    df = pd.DataFrame(rows).sort_values(["uf", "name"]).reset_index(drop=True)
    df.to_csv(INMET_DIR / "_stations.csv", index=False)
    return df


def download_year(year):
    zpath = config.EXTERNAL / ("inmet_%d.zip" % year)
    if zpath.exists() and zpath.stat().st_size > 1000:
        return zpath
    r = requests.get(config.INMET_HIST_URL.format(year=year), timeout=600,
                     headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    zpath.write_bytes(r.content)
    return zpath


def _find_col(cols, *subs):
    up = {c.upper(): c for c in cols}
    for cu, c in up.items():
        if all(s in cu for s in subs):
            return c
    return None


def parse_inmet_csv(raw):
    text = raw.decode("latin-1")
    lines = text.splitlines()
    # locate the column-header line (starts with 'Data')
    hidx = next((i for i, l in enumerate(lines[:15])
                 if l.upper().replace('"', '').startswith("DATA;")), 8)
    df = pd.read_csv(io.StringIO("\n".join(lines[hidx:])), sep=";", dtype=str,
                     keep_default_na=False, engine="python")
    df = df.loc[:, [c for c in df.columns if not c.startswith("Unnamed")]]
    c_data = _find_col(df.columns, "DATA")
    c_hora = _find_col(df.columns, "HORA")
    c_rad = _find_col(df.columns, "RADIACAO", "GLOBAL")
    c_wind = _find_col(df.columns, "VELOCIDADE", "HORARIA")
    if not all([c_data, c_hora, c_wind]):
        return None
    out = pd.DataFrame()
    ds = df[c_data].str.strip().str.replace("-", "/", regex=False)
    # year-first (YYYY/MM/DD, old format used '-') if first token is 4 digits,
    # otherwise day-first (DD/MM/YYYY).
    fmt = "%Y/%m/%d" if str(ds.iloc[0])[:4].isdigit() else "%d/%m/%Y"
    date = pd.to_datetime(ds, format=fmt, errors="coerce")
    hour = df[c_hora].str.extract(r"(\d{2})", expand=False).astype(float)
    out["datetime_utc"] = date + pd.to_timedelta(hour, unit="h")

    def tonum(col):
        # to_numeric(coerce) already turns "" into NaN; no explicit replace needed
        return pd.to_numeric(df[col].str.replace(",", ".", regex=False), errors="coerce")
    out["rad_kj"] = tonum(c_rad) if c_rad else np.nan
    out["wind"] = tonum(c_wind)
    for c in ("rad_kj", "wind"):
        out.loc[out[c] < 0, c] = np.nan      # -9999 fill -> NaN
    return out.dropna(subset=["datetime_utc"])


def process(years, stations):
    codes = set(stations["code"])
    acc = {c: [] for c in codes}
    for year in years:
        try:
            zpath = download_year(year)
        except Exception as e:
            print("year %d download FAIL: %s" % (year, repr(e)[:100]))
            continue
        try:
            with zipfile.ZipFile(zpath) as zf:   # 'with' ensures the file is closed
                members = [n for n in zf.namelist() if n.lower().endswith(".csv")]
                got = 0
                for code in codes:
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
            if not KEEP_ZIPS:
                try:
                    os.remove(zpath)
                except OSError:
                    pass
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
    years = range(2003, 2023)
    if len(sys.argv) > 1:  # test mode: specific year(s)
        years = [int(a) for a in sys.argv[1:]]
    st = select_stations()
    print("stations selected:", len(st), "| years:", list(years)[0], "-", list(years)[-1])
    process(years, st)


if __name__ == "__main__":
    main()
