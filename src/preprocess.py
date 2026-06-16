# -*- coding: utf-8 -*-
"""Calcula as medias historicas de WIND_SPEED (m/s) e SOLAR_IRRAD (kWh/m2/dia) para cada
ponto da NASA e cada estacao do INMET. Essas medias sao a base para a interpolacao e o indice.

Pontos importantes:
- A radiacao da NASA (ALLSKY_SFC_SW_DWN) ja vem como insolacao diaria em kWh/m2/dia, entao
  basta tirar a media.
- A radiacao do INMET vem hora a hora em kJ/m2: somam-se as horas de dia (das 5 as 18 h no
  horario local) para obter o total diario e divide-se por 3600 para passar de kJ para kWh.
  Os horarios do INMET estao em UTC e a Paraiba e UTC-3.

Etapa de PRE-PROCESSAMENTO (reproducao). Corresponde a Secao 2.5 do artigo.
"""
import sys, os
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in (_ROOT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import numpy as np
import pandas as pd
import config

TZ_LOCAL = -3  # diferenca do horario local da Paraiba para o UTC

# Limites fisicos para remocao de valores absurdos (outliers), como o artigo menciona.
WIND_MAX = 60.0          # vento maximo plausivel (m/s)
RAD_HOURLY_MAX = 6000.0  # radiacao horaria maxima plausivel (kJ/m2)
SOLAR_DAILY_MAX = 15.0   # radiacao diaria maxima plausivel (kWh/m2/dia)


def nasa_means():
    """Le todos os arquivos da NASA, remove valores fora dos limites fisicos e calcula a
    media historica de vento e de radiacao por ponto. Salva nasa_points.csv."""
    files = sorted((config.RAW / "nasa").glob("nasa_*.csv"))
    rows = []
    for f in files:
        df = pd.read_csv(f, parse_dates=["date"])
        # mantem so os valores dentro da faixa fisica; o resto vira NaN e nao entra na media
        ws = df["WS10M"].where((df["WS10M"] >= 0) & (df["WS10M"] < WIND_MAX))
        sw = df["ALLSKY_SFC_SW_DWN"].where(
            (df["ALLSKY_SFC_SW_DWN"] >= 0) & (df["ALLSKY_SFC_SW_DWN"] < SOLAR_DAILY_MAX))
        rows.append(dict(lat=float(df["lat"].iloc[0]), lon=float(df["lon"].iloc[0]),
                         WIND_SPEED=ws.mean(), SOLAR_IRRAD=sw.mean(),
                         n_days=int(ws.notna().sum())))
    out = pd.DataFrame(rows)
    out.to_csv(config.PROCESSED / "nasa_points.csv", index=False)
    print("NASA points:", len(out),
          "| WIND %.2f-%.2f m/s" % (out.WIND_SPEED.min(), out.WIND_SPEED.max()),
          "| SOLAR %.2f-%.2f kWh/m2/day" % (out.SOLAR_IRRAD.min(), out.SOLAR_IRRAD.max()))
    return out


def _daily_solar_kwh(df):
    """A partir da radiacao horaria (kJ/m2) de uma estacao, calcula a serie de irradiacao
    diaria (kWh/m2/dia): converte o horario para local (UTC-3), mantem so as horas de dia
    (5 as 18 h), soma por dia e divide por 3600 (kJ -> kWh)."""
    t_local = df["datetime_utc"] + pd.to_timedelta(TZ_LOCAL, unit="h")
    h = t_local.dt.hour
    mask = (h >= config.DAY_START_HOUR) & (h <= config.DAY_END_HOUR)
    daily = df.loc[mask].groupby(t_local.dt.date)["rad_kj"].sum(min_count=1) / 3600.0
    daily = daily.where((daily >= 0) & (daily < SOLAR_DAILY_MAX))   # remove dias absurdos
    return daily


def inmet_means():
    """Para cada estacao do INMET, remove outliers, calcula a media de vento e a media da
    irradiacao diaria, e junta com as coordenadas da estacao. Salva inmet_points.csv."""
    sp = config.RAW / "inmet" / "_stations.csv"
    if not sp.exists():
        print("INMET stations file not found; run data_inmet first.")
        return None
    st = pd.read_csv(sp)
    rows = []
    for _, s in st.iterrows():
        f = config.RAW / "inmet" / ("%s.csv" % s["code"])
        if not f.exists():
            continue
        df = pd.read_csv(f, parse_dates=["datetime_utc"])
        if not len(df):
            continue
        df["wind"] = df["wind"].where((df["wind"] >= 0) & (df["wind"] < WIND_MAX))
        df["rad_kj"] = df["rad_kj"].where((df["rad_kj"] >= 0) & (df["rad_kj"] < RAD_HOURLY_MAX))
        solar = _daily_solar_kwh(df)
        rows.append(dict(code=s["code"], name=s["name"], uf=s["uf"],
                         lat=float(s["lat"]), lon=float(s["lon"]),
                         WIND_SPEED=df["wind"].mean(),
                         SOLAR_IRRAD=solar.mean(),
                         n_wind=int(df["wind"].notna().sum()),
                         n_days_solar=int(solar.notna().sum())))
    out = pd.DataFrame(rows)
    out.to_csv(config.PROCESSED / "inmet_points.csv", index=False)
    ok = out.dropna(subset=["WIND_SPEED", "SOLAR_IRRAD"])
    print("INMET stations:", len(out), "| valid:", len(ok),
          "| WIND %.2f-%.2f" % (ok.WIND_SPEED.min(), ok.WIND_SPEED.max()),
          "| SOLAR %.2f-%.2f" % (ok.SOLAR_IRRAD.min(), ok.SOLAR_IRRAD.max()))
    return out


def main():
    # "nasa", "inmet" ou "all" (padrao) para escolher o que processar.
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("all", "nasa"):
        nasa_means()
    if which in ("all", "inmet"):
        inmet_means()


if __name__ == "__main__":
    main()
