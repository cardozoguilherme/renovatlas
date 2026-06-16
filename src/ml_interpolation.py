# -*- coding: utf-8 -*-
"""CONTRIBUICAO (Ideia 2): interpolacao por aprendizado de maquina com covariaveis.

O artigo interpola usando apenas latitude e longitude (IDW e Kriging). Aqui sao testados
modelos de aprendizado de maquina que tambem usam o relevo (elevacao) e a distancia ate a
costa, comparados com o Kriging do artigo na mesma validacao cruzada (leave-one-out). O
objetivo e verificar se o aprendizado de maquina e as covariaveis melhoram a estimativa,
em especial a do vento.

Modelos comparados:
  - Kriging lon/lat (4 vizinhos): reproducao do metodo do artigo (linha de base).
  - Random Forest lon/lat: ML so com posicao (para isolar o efeito das covariaveis).
  - Random Forest com elevacao e distancia da costa: contribuicao.
  - Gradient Boosting com elevacao e distancia da costa: contribuicao.
  - Regression Kriging: Random Forest nas covariaveis mais Kriging dos residuos.
"""
import sys, os
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in (_ROOT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import LeaveOneOut, cross_val_predict
import config
from interpolation import kriging_interpolate, loocv as kriging_loocv, metrics

FEATURES_GEO = ["lon", "lat"]                        # apenas a posicao
FEATURES_ALL = ["lon", "lat", "elev", "dist_coast"]  # posicao + covariaveis fisicas


def rf():
    """Cria um modelo Random Forest (floresta de arvores de decisao) para regressao."""
    return RandomForestRegressor(n_estimators=400, min_samples_leaf=2,
                                 random_state=42, n_jobs=-1)


def gbm():
    """Cria um modelo Gradient Boosting (arvores em sequencia, cada uma corrige o erro da anterior)."""
    return GradientBoostingRegressor(n_estimators=400, max_depth=3,
                                     learning_rate=0.05, random_state=42)


def loo_pred(model, X, y):
    """Faz a validacao cruzada deixa-um-de-fora de um modelo sklearn e devolve as previsoes
    (cada ponto e estimado sem ter participado do treino)."""
    return cross_val_predict(model, X, y, cv=LeaveOneOut())


def loo_regression_kriging(df, col, feats=FEATURES_ALL):
    """Regression Kriging com validacao deixa-um-de-fora: para cada ponto, ajusta uma
    Random Forest nas covariaveis dos demais, faz o Kriging dos residuos (a parte que a RF
    nao explicou) e soma as duas. Combina a tendencia das covariaveis com a estrutura
    espacial dos residuos."""
    sub = df.dropna(subset=[col])
    X = sub[feats].values
    y = sub[col].values
    lonlat = sub[["lon", "lat"]].values
    n = len(y)
    pred = np.full(n, np.nan)
    for i in range(n):
        tr = np.arange(n) != i
        reg = rf().fit(X[tr], y[tr])
        resid = y[tr] - reg.predict(X[tr])                 # residuos do modelo de regressao
        rk = kriging_interpolate(lonlat[tr], resid, lonlat[i:i + 1], k=config.N_NEIGHBORS)
        pred[i] = reg.predict(X[i:i + 1])[0] + rk[0]        # tendencia + residuo interpolado
    return y, pred


def compare(points_csv, label):
    """Compara, por validacao cruzada, o Kriging do artigo com os modelos de ML, para vento
    e radiacao. Salva a tabela de erros (RMSE, MAE, R2) em outputs/tables."""
    df = pd.read_csv(points_csv)
    rows = []
    for col, pretty in [(config.WIND, "WIND_SPEED (m/s)"), (config.SOLAR, "SOLAR_IRRAD (kWh/m2)")]:
        sub = df.dropna(subset=[col])
        y = sub[col].values
        # 1) Kriging so com lon/lat (linha de base, o metodo do artigo)
        yy, yhat = kriging_loocv(sub, col, "kriging")
        rows.append(dict(Variable=pretty, Model="Kriging lon/lat (paper)", **metrics(yy, yhat)))
        # 2) Random Forest so com lon/lat (mostra o efeito do modelo, sem as covariaveis)
        rows.append(dict(Variable=pretty, Model="RF lon/lat",
                         **metrics(y, loo_pred(rf(), sub[FEATURES_GEO].values, y))))
        # 3) Random Forest com elevacao e distancia da costa (a contribuicao)
        rows.append(dict(Variable=pretty, Model="RF +elev+coast",
                         **metrics(y, loo_pred(rf(), sub[FEATURES_ALL].values, y))))
        # 4) Gradient Boosting com as covariaveis
        rows.append(dict(Variable=pretty, Model="GBM +elev+coast",
                         **metrics(y, loo_pred(gbm(), sub[FEATURES_ALL].values, y))))
        # 5) Regression Kriging (regressao + Kriging dos residuos)
        yy, yhat = loo_regression_kriging(sub, col)
        rows.append(dict(Variable=pretty, Model="Regression Kriging", **metrics(yy, yhat)))
    out = pd.DataFrame(rows)
    out.to_csv(config.TABLES / ("contrib_ml_%s.csv" % label), index=False)
    print("=== ML interpolation comparison (LOOCV) — %s ===" % label.upper())
    for _, r in out.iterrows():
        print("  %-22s %-24s RMSE=%.4f MAE=%.4f R2=%.4f" %
              (r["Variable"], r["Model"], r["RMSE"], r["MAE"], r["R2"]))
    return out


def make_ml_grid(points_csv, grid_csv, label, feats=FEATURES_ALL):
    """Treina uma Random Forest com todos os pontos e a aplica para interpolar vento e
    radiacao em toda a grade MM. Salva mm_grid_ml_<label>.csv (a versao por ML do MM grid)."""
    df = pd.read_csv(points_csv)
    grid = pd.read_csv(grid_csv)
    out = grid.copy()
    for col in (config.WIND, config.SOLAR):
        sub = df.dropna(subset=[col])
        model = rf().fit(sub[feats].values, sub[col].values)
        out[col] = model.predict(grid[feats].values)
    fn = config.PROCESSED / ("mm_grid_ml_%s.csv" % label)
    out.to_csv(fn, index=False)
    print("  MM grid (ML, %s): WIND %.2f-%.2f | SOLAR %.2f-%.2f -> %s" %
          (label, out[config.WIND].min(), out[config.WIND].max(),
           out[config.SOLAR].min(), out[config.SOLAR].max(), fn.name))
    return out


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    labels = ["nasa", "inmet"] if which == "all" else [which]
    grid_cov = config.PROCESSED / "mm_grid_cov.csv"
    for lbl in labels:
        pts = config.PROCESSED / ("%s_points_cov.csv" % lbl)
        if not pts.exists():
            print("missing covariates:", pts); continue
        compare(pts, lbl)                       # compara os metodos
        if grid_cov.exists():
            make_ml_grid(pts, grid_cov, lbl)    # gera o MM grid por ML
        else:
            print("  (mm_grid_cov.csv not ready; skipping ML grid)")


if __name__ == "__main__":
    main()
