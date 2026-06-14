# Arquitetura do projeto (RenovAtlas)

Este documento descreve a organização do repositório, explicando o que é e para que serve
cada diretório e cada arquivo. A ideia é permitir entender o projeto inteiro sem precisar
abrir todos os códigos.

A separação é simples. Os códigos ficam em `src`. O painel fica em `app`. A análise
exploratória fica em `notebooks`. Os parâmetros ficam em `config.py`. Os dados ficam em
`data` (brutos, tratados e de apoio). Os resultados ficam em `outputs` (tabelas e
figuras). Os modelos treinados ficam em `models` e os experimentos em `mlruns`. Os
arquivos que rodam tudo de uma vez e os documentos ficam na raiz.

## Visão geral em árvore

```
reproduction/
  config.py                 parametros centrais (area, resolucao, periodos, fontes)
  run_all.py                roda a reproducao do artigo
  run_contrib.py            roda a contribuicao do grupo
  requirements.txt          dependencias com versoes fixadas
  Dockerfile                imagem que serve o painel
  .dockerignore             o que nao entra na imagem
  .gitignore                o que nao entra no repositorio
  README.md                 visao geral, equipe e como rodar
  ARQUITETURA.md            este documento
  REPRODUCTION_REPORT.md    relatorio da reproducao do artigo
  CONTRIBUICAO.md           relatorio da contribuicao do grupo
  IDEIAS_DE_CONTRIBUICAO.md propostas de continuacao
  relatorio_sbc.docx        relatorio final no formato SBC
  src/                      codigo (coleta, processamento, modelagem, indices)
  app/                      painel interativo (Streamlit)
  notebooks/                analise exploratoria (EDA)
  models/                   melhores modelos salvos (.joblib)
  mlruns/                   experimentos do MLflow (gerado em execucao)
  data/
    raw/                    dados brutos baixados (nao versionado)
      nasa/                 80 CSVs (um por ponto) + _manifest.csv
      inmet/                36 CSVs (um por estacao) + _stations.csv
    processed/              dados tratados (medias, MM grid, indices, covariaveis)
    external/               malha do IBGE (versionada) e zips do INMET (nao versionado)
  outputs/
    tables/                 tabelas em CSV (Tabela 2, rankings, comparacao de modelos)
    figures/                mapas e graficos em PNG
```

## Convenções de nomes

- Muitos arquivos aparecem em par, um terminando em `_nasa` e outro em `_inmet`, porque o
  trabalho processa as duas fontes em paralelo (NASA e satelite, INMET sao estacoes).
- `mm_grid` e a grade fina de 0,05 grau (o Multi-Map grid) que cobre a Paraiba.
- O sufixo `_cov` indica arquivos com as covariaveis (elevacao e distancia a costa).
- O sufixo `_ml` indica resultado dos modelos de aprendizado de maquina.
- `compl` e `kappa` referem-se a complementaridade temporal.
- `hybrid_index` e `hybridplus` referem-se ao indice de geracao hibrida.
- `best_<fonte>_<variavel>.joblib` e o melhor modelo salvo para cada caso.

## Arquivos na raiz

| Arquivo | O que é e para que serve |
|---|---|
| config.py | Todos os parâmetros num lugar só: área da Paraíba, resolução das grades, períodos e endereços das fontes. Importado por todos os códigos. |
| run_all.py | Executa as etapas da reprodução do artigo na ordem certa. |
| run_contrib.py | Executa as etapas da contribuição (depois da reprodução). |
| requirements.txt | Lista as dependências com versões fixadas, para instalar o ambiente. |
| Dockerfile | Define a imagem que instala as dependências e serve o painel. |
| .dockerignore / .gitignore | Definem o que não entra na imagem e no repositório (dados pesados, mlruns, caches). |
| README.md | Visão geral, equipe, disciplina, instituição e instruções de uso. |
| ARQUITETURA.md | Este documento. |
| REPRODUCTION_REPORT.md | Relatório da reprodução do artigo. |
| CONTRIBUICAO.md | Relatório da contribuição do grupo. |
| IDEIAS_DE_CONTRIBUICAO.md | Propostas de continuação. |
| relatorio_sbc.docx | Relatório final no formato SBC. |

## Pasta src: o código

### Códigos da reprodução

| Arquivo | O que faz |
|---|---|
| data_ibge.py | Baixa a malha dos 223 municípios da Paraíba (IBGE). |
| data_nasa.py | Baixa as séries diárias de vento e radiação da NASA POWER (grade 0,5 grau). |
| data_inmet.py | Baixa e lê o histórico das 36 estações do INMET (2003 a 2022). |
| preprocess.py | Limpa os dados, converte unidades e calcula as médias históricas por ponto. |
| interpolation.py | Implementa IDW e Kriging e os compara por validação cruzada (gera a Tabela 2). |
| mm_grid.py | Cria a grade fina de 0,05 grau e interpola vento e radiação por Kriging. |
| ip_pb.py | Calcula o índice IP-PB por município, os grupos e os rankings. |
| plots.py | Gera os mapas e gráficos que correspondem às figuras do artigo. |

### Códigos da contribuição

| Arquivo | O que faz |
|---|---|
| covariates.py | Coleta as covariáveis físicas (elevação pela API Open-Meteo e distância à costa). |
| ml_interpolation.py | Compara o Kriging do artigo com Random Forest, Gradient Boosting e Regression Kriging na tarefa de interpolar o mapa, e gera o MM grid por ML. |
| complementarity.py | Calcula a complementaridade temporal kappa entre vento e sol e a interpola para a grade. |
| hybrid_index.py | Combina a magnitude do recurso com a complementaridade no índice híbrido IPH. |
| plots_contrib.py | Gera as figuras da contribuição (comparação de modelos, mapa de kappa, ranking híbrido, ciclo mensal). |

### Modelagem de aprendizado de máquina (disciplina)

| Arquivo | O que faz |
|---|---|
| train.py | Trata a estimativa de vento e radiação como regressão a partir de lon, lat, elevação e distância à costa. Treina e compara cinco modelos (KNN, Árvore de Decisão, Random Forest, AdaBoost e MLP) com holdout, validação cruzada e Grid Search, registra tudo no MLflow e salva o melhor modelo de cada caso. |

Observação sobre os dois módulos de ML: o `ml_interpolation.py` é a contribuição
científica (mostra que o aprendizado de máquina melhora a interpolação do artigo, em
comparação direta com o Kriging). O `train.py` é o pipeline de modelagem da disciplina
(cinco modelos com ajuste de hiperparâmetros e rastreamento no MLflow). Os dois usam as
mesmas covariáveis, com objetivos diferentes.

### Scripts de apoio

Usados apenas para investigar as fontes durante o desenvolvimento. Não fazem parte do
pipeline e não são chamados pelos orquestradores.

| Arquivo | O que faz |
|---|---|
| inmet_explore.py | Listou as estações do INMET e testou a API de dados. |
| inmet_inspect.py | Abriu um zip do INMET para descobrir o formato dos CSVs. |

## Pasta app: o painel

| Arquivo | O que faz |
|---|---|
| dashboard.py | Painel interativo em Streamlit com quatro abas: mapa de potencial (vento, sol, IP-PB e IPH), comparação das métricas dos modelos, previsão por coordenada e rankings de municípios. |

## Pasta notebooks: análise exploratória

| Arquivo | O que faz |
|---|---|
| eda.ipynb | Notebook de EDA com estatísticas descritivas, distribuições, relação das variáveis com relevo e costa, correlações e sazonalidade. |

## Pasta models: modelos salvos

Guarda o melhor modelo de cada combinação de fonte e variável, no formato joblib
(`best_nasa_WIND_SPEED.joblib`, `best_nasa_SOLAR_IRRAD.joblib`, e os equivalentes para o
INMET). São carregados pelo painel para a previsão por coordenada.

## Pasta mlruns: experimentos

Criada pelo MLflow ao rodar `src/train.py`. Guarda os parâmetros, as métricas e os
modelos de cada experimento. Pode ser explorada com o comando `mlflow ui`. Não é
versionada.

## Pasta data: os dados

### data/raw (dados brutos, não versionados)

| Caminho | O que contém |
|---|---|
| nasa/nasa_LAT_LON.csv | Série diária de vento e radiação por ponto da grade NASA (80 arquivos). |
| nasa/_manifest.csv | Lista dos pontos NASA baixados. |
| inmet/A###.csv | Série horária de vento e radiação por estação INMET (36 arquivos). |
| inmet/_stations.csv | Catálogo das estações usadas. |

### data/processed (dados tratados)

| Arquivo | O que contém |
|---|---|
| nasa_points.csv, inmet_points.csv | Médias históricas por ponto (reprodução). |
| mm_grid_points.csv | Pontos da grade fina dentro da Paraíba, com o município de cada um. |
| mm_grid_nasa.csv, mm_grid_inmet.csv | A grade fina interpolada por Kriging. |
| ip_pb_nasa.csv, ip_pb_inmet.csv | Índice IP-PB por município, com os grupos. |
| nasa_points_cov.csv, inmet_points_cov.csv | Pontos com as covariáveis elevação e distância à costa. |
| mm_grid_cov.csv | A grade fina com as covariáveis. |
| mm_grid_ml_nasa.csv, mm_grid_ml_inmet.csv | A grade fina interpolada por aprendizado de máquina. |
| compl_nasa.csv, compl_inmet.csv | Complementaridade kappa por ponto. |
| kappa_grid_nasa.csv, kappa_grid_inmet.csv | Complementaridade interpolada para a grade. |
| hybrid_index_nasa.csv, hybrid_index_inmet.csv | Índice híbrido IPH por município. |

### data/external (dados de apoio)

| Arquivo | O que contém |
|---|---|
| pb_municipios.geojson, pb_municipios.gpkg | Malha dos municípios da Paraíba (versionada, usada nos mapas e no painel). |
| inmet_AAAA.zip | Arquivos anuais do INMET em cache (não versionados). |

## Pasta outputs: os resultados

### outputs/tables

| Arquivo | O que contém |
|---|---|
| table2_nasa.csv, table2_inmet.csv | Comparação entre IDW e Kriging (a Tabela 2 do artigo). |
| rank_solar, rank_wind, rank_hybrid (nasa e inmet) | Os 10 melhores municípios por tipo (reprodução). |
| contrib_ml_nasa.csv, contrib_ml_inmet.csv | Comparação entre Kriging e os modelos de ML na interpolação (contribuição). |
| rank_hybridplus_nasa.csv, rank_hybridplus_inmet.csv | Os 10 melhores pelo índice híbrido IPH. |
| model_comparison.csv | Comparação dos cinco modelos da disciplina (de src/train.py). |

### outputs/figures

Guarda as figuras em PNG. As que começam com `mm_`, `scatter_ippb_`, `top10_` e
`correlation_` são da reprodução. As que começam com `contrib_` são da contribuição.
