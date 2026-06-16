# -*- coding: utf-8 -*-
"""CONTRIBUICAO (Ideia 1): complementaridade temporal entre vento e sol.

O artigo usa apenas medias de longo prazo e ignora a dinamica temporal. Para geracao
hibrida, o que importa e se as duas fontes se completam ao longo do ano: quando uma cai, a
outra sobe. Isto e medido pela correlacao entre os ciclos mensais (climatologia) de vento e
de radiacao em cada ponto.

Indice de complementaridade: kappa = (1 - r) / 2, com r = correlacao de Pearson entre as 12
medias mensais de vento e de solar. kappa fica entre 0 e 1:
  kappa perto de 1   -> fontes anti-correlacionadas (otimo para hibrido)
  kappa perto de 0,5 -> fontes independentes
  kappa perto de 0   -> fontes sobem e descem juntas (ruim para hibrido)
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
# Reaproveita funcoes e constantes do pre-processamento e da interpolacao.
from preprocess import _daily_solar_kwh, TZ_LOCAL, WIND_MAX, RAD_HOURLY_MAX
from interpolation import kriging_interpolate


def kappa_from_monthly(mw, ms):
    """Calcula a correlacao r entre os ciclos mensais de vento (mw) e de solar (ms) e o
    indice kappa = (1 - r)/2. Devolve (nan, nan) se houver poucos meses ou variancia zero."""
    if len(mw) < 6 or np.std(mw) == 0 or np.std(ms) == 0:
        return np.nan, np.nan
    r = float(np.corrcoef(mw, ms)[0, 1])
    return r, (1.0 - r) / 2.0


def nasa_complementarity():
    """Calcula o kappa de cada ponto da NASA: agrupa a serie diaria por mes do ano (a
    climatologia), correlaciona vento e radiacao e aplica a formula. Salva compl_nasa.csv."""
    rows = []
    for f in sorted((config.RAW / "nasa").glob("nasa_*.csv")):
        df = pd.read_csv(f, parse_dates=["date"])
        m = df["date"].dt.month
        mw = df.groupby(m)["WS10M"].mean()                 # media de cada mes (vento)
        ms = df.groupby(m)["ALLSKY_SFC_SW_DWN"].mean()     # media de cada mes (radiacao)
        common = mw.index.intersection(ms.index)
        r, k = kappa_from_monthly(mw.loc[common].values, ms.loc[common].values)
        rows.append(dict(lat=float(df["lat"].iloc[0]), lon=float(df["lon"].iloc[0]),
                         r_month=r, kappa=k))
    out = pd.DataFrame(rows)
    out.to_csv(config.PROCESSED / "compl_nasa.csv", index=False)
    print("NASA  complementarity: n=%d | kappa %.3f-%.3f (mean %.3f)" %
          (len(out), out.kappa.min(), out.kappa.max(), out.kappa.mean()))
    return out


def inmet_complementarity():
    """Mesmo calculo do kappa, para as estacoes do INMET: usa o vento medio mensal e a
    irradiacao diaria media mensal (ja convertida e filtrada). Salva compl_inmet.csv."""
    st = pd.read_csv(config.RAW / "inmet" / "_stations.csv")
    rows = []
    for _, s in st.iterrows():
        f = config.RAW / "inmet" / ("%s.csv" % s["code"])
        if not f.exists():
            continue
        df = pd.read_csv(f, parse_dates=["datetime_utc"])
        df["wind"] = df["wind"].where((df["wind"] >= 0) & (df["wind"] < WIND_MAX))
        df["rad_kj"] = df["rad_kj"].where((df["rad_kj"] >= 0) & (df["rad_kj"] < RAD_HOURLY_MAX))
        t_local = df["datetime_utc"] + pd.to_timedelta(TZ_LOCAL, unit="h")
        mw = df.groupby(t_local.dt.month)["wind"].mean()       # vento medio por mes
        daily = _daily_solar_kwh(df)                           # irradiacao diaria (kWh)
        daily.index = pd.to_datetime(daily.index)
        ms = daily.groupby(daily.index.month).mean()           # irradiacao media por mes
        common = mw.index.intersection(ms.index)
        r, k = kappa_from_monthly(mw.loc[common].values, ms.loc[common].values)
        rows.append(dict(code=s["code"], name=s["name"], lat=float(s["lat"]),
                         lon=float(s["lon"]), r_month=r, kappa=k))
    out = pd.DataFrame(rows)
    out.to_csv(config.PROCESSED / "compl_inmet.csv", index=False)
    ok = out.dropna(subset=["kappa"])
    print("INMET complementarity: n=%d | kappa %.3f-%.3f (mean %.3f)" %
          (len(ok), ok.kappa.min(), ok.kappa.max(), ok.kappa.mean()))
    return out


def interpolate_kappa(compl_csv, grid_csv, out_csv, label):
    """Interpola o kappa (calculado nos pontos de origem) para toda a grade MM, por Kriging.
    Salva o arquivo da grade com a coluna kappa."""
    src = pd.read_csv(compl_csv).dropna(subset=["kappa"])
    grid = pd.read_csv(grid_csv)
    xy = src[["lon", "lat"]].values
    z = src["kappa"].values
    grid["kappa"] = kriging_interpolate(xy, z, grid[["lon", "lat"]].values, k=config.N_NEIGHBORS)
    grid.to_csv(out_csv, index=False)
    print("  kappa interpolated (%s): %.3f-%.3f -> %s" %
          (label, grid["kappa"].min(), grid["kappa"].max(), out_csv.name))
    return grid


def main():
    # Calcula o kappa nos pontos (NASA e INMET) e interpola para a grade.
    n = nasa_complementarity()
    i = inmet_complementarity()
    grid = config.PROCESSED / "mm_grid_points.csv"
    if grid.exists():
        interpolate_kappa(config.PROCESSED / "compl_nasa.csv", grid,
                          config.PROCESSED / "kappa_grid_nasa.csv", "nasa")
        interpolate_kappa(config.PROCESSED / "compl_inmet.csv", grid,
                          config.PROCESSED / "kappa_grid_inmet.csv", "inmet")


if __name__ == "__main__":
    main()
