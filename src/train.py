# -*- coding: utf-8 -*-
"""Treinamento e comparacao de modelos de aprendizado de maquina, com rastreamento no MLflow.

Este e o modulo de modelagem exigido pela disciplina. O problema e de regressao: estimar
WIND_SPEED e SOLAR_IRRAD a partir das features espaciais (lon, lat, elev, dist_coast).

Sao comparados os cinco modelos pedidos: KNN, Arvore de Decisao, Random Forest, AdaBoost e
MLP (rede neural). A avaliacao usa:
  - holdout: separacao em treino (75%) e teste (25%);
  - validacao cruzada (K-fold de 5 dobras) dentro do GridSearchCV, que ajusta os
    hiperparametros de cada modelo (busca exaustiva nas grades definidas);
  - registro no MLflow de parametros, metricas, varios experimentos e do proprio modelo.

Sao gerados 4 experimentos (NASA/INMET x vento/solar), cada um com os 5 modelos. O melhor
modelo de cada experimento (menor RMSE no teste) e salvo em models/.
"""
import sys, os
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in (_ROOT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import numpy as np
import pandas as pd
import joblib
import mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split, GridSearchCV, KFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.neighbors import KNeighborsRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, AdaBoostRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
import config

FEATURES = ["lon", "lat", "elev", "dist_coast"]   # variaveis de entrada dos modelos
MODELS_DIR = config.ROOT / "models"
MODELS_DIR.mkdir(exist_ok=True)


def _pipe(model):
    """Monta um pipeline que primeiro padroniza as features (StandardScaler) e depois aplica
    o modelo. A padronizacao e importante para KNN e MLP (que dependem da escala); para as
    arvores nao atrapalha."""
    return Pipeline([("scaler", StandardScaler()), ("model", model)])


def model_space():
    """Define os cinco modelos e as grades de hiperparametros que o GridSearchCV vai testar.
    Cada item e uma tupla (pipeline, grade de parametros)."""
    return {
        "KNN": (_pipe(KNeighborsRegressor()),
                {"model__n_neighbors": [3, 5, 7, 9], "model__weights": ["uniform", "distance"]}),
        "DecisionTree": (_pipe(DecisionTreeRegressor(random_state=42)),
                         {"model__max_depth": [3, 5, 8, None], "model__min_samples_leaf": [1, 2, 4]}),
        "RandomForest": (_pipe(RandomForestRegressor(random_state=42)),
                         {"model__n_estimators": [100, 300], "model__max_depth": [None, 8],
                          "model__min_samples_leaf": [1, 2]}),
        "AdaBoost": (_pipe(AdaBoostRegressor(random_state=42)),
                     {"model__n_estimators": [50, 100, 200], "model__learning_rate": [0.5, 1.0]}),
        "MLP": (_pipe(MLPRegressor(random_state=42, max_iter=3000)),
                {"model__hidden_layer_sizes": [(50,), (100,), (50, 50)], "model__alpha": [1e-4, 1e-3]}),
    }


def metrics(y, yhat):
    """Calcula RMSE, MAE e R2 entre os valores reais (y) e os previstos (yhat)."""
    return (float(np.sqrt(mean_squared_error(y, yhat))),
            float(mean_absolute_error(y, yhat)),
            float(r2_score(y, yhat)))


def run_target(df, target, source, all_rows):
    """Treina e compara os cinco modelos para uma variavel (target) de uma base (source).
    Cada modelo vira um run no MLflow, com seus parametros, metricas e o modelo salvo. O
    melhor (menor RMSE no teste) e exportado para models/."""
    X = df[FEATURES].values
    y = df[target].values
    # holdout: 75% treino e 25% teste (semente fixa para reproduzir)
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42)
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    # cada combinacao base x variavel e um experimento separado no MLflow
    mlflow.set_experiment("renovatlas_%s_%s" % (source, target))
    best = {"rmse": np.inf}
    print("\n=== %s | %s (holdout: %d treino, %d teste) ===" % (source, target, len(X_tr), len(X_te)))
    for name, (pipe, grid) in model_space().items():
        with mlflow.start_run(run_name=name):
            # GridSearchCV testa todas as combinacoes da grade e escolhe a de menor RMSE na CV
            gs = GridSearchCV(pipe, grid, cv=cv, scoring="neg_root_mean_squared_error", n_jobs=-1)
            gs.fit(X_tr, y_tr)
            est = gs.best_estimator_                          # melhor combinacao de hiperparametros
            rmse, mae, r2 = metrics(y_te, est.predict(X_te))  # avalia no conjunto de teste
            cv_rmse = -gs.best_score_                         # RMSE medio na validacao cruzada
            # registra no MLflow: parametros, metricas e o modelo treinado
            mlflow.log_param("model", name)
            mlflow.log_param("source", source)
            mlflow.log_param("target", target)
            mlflow.log_params(gs.best_params_)
            mlflow.log_metric("cv_rmse", cv_rmse)
            mlflow.log_metric("test_rmse", rmse)
            mlflow.log_metric("test_mae", mae)
            mlflow.log_metric("test_r2", r2)
            mlflow.sklearn.log_model(est, name="model")
            print("  %-13s cv_rmse=%.4f  test_rmse=%.4f mae=%.4f r2=%.4f" % (name, cv_rmse, rmse, mae, r2))
            all_rows.append(dict(source=source, target=target, model=name,
                                 cv_rmse=cv_rmse, test_rmse=rmse, test_mae=mae, test_r2=r2))
            if rmse < best["rmse"]:                           # guarda o melhor modelo ate agora
                best = {"rmse": rmse, "name": name, "est": est}
    # salva o melhor modelo desta base/variavel para o dashboard usar nas previsoes
    fn = MODELS_DIR / ("best_%s_%s.joblib" % (source, target))
    joblib.dump(best["est"], fn)
    print("  melhor: %s (test_rmse=%.4f) -> %s" % (best["name"], best["rmse"], fn.name))


def main():
    # aponta o MLflow para a pasta mlruns do projeto
    mlflow.set_tracking_uri((config.ROOT / "mlruns").as_uri())
    rows = []
    for source in ("nasa", "inmet"):
        pts = config.PROCESSED / ("%s_points_cov.csv" % source)
        if not pts.exists():
            print("faltam covariaveis:", pts); continue
        df = pd.read_csv(pts)
        for target in (config.WIND, config.SOLAR):
            run_target(df.dropna(subset=[target]), target, source, rows)
    # tabela consolidada com a comparacao de todos os modelos
    out = pd.DataFrame(rows)
    out.to_csv(config.TABLES / "model_comparison.csv", index=False)
    print("\nsalvo -> outputs/tables/model_comparison.csv  (%d linhas)" % len(out))


if __name__ == "__main__":
    main()
