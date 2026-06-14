# Arquitetura do projeto (pasta reproduction)

Este documento descreve a organização da pasta `reproduction`, explicando o que é e para
que serve cada diretório e cada arquivo. A ideia é permitir entender o projeto inteiro
sem precisar abrir todos os códigos.

A pasta segue uma separação simples. Os códigos ficam em `src`. Os parâmetros ficam em
`config.py`. Os dados ficam em `data` (divididos entre brutos, tratados e de apoio). Os
resultados ficam em `outputs` (tabelas e figuras). Os arquivos que rodam tudo de uma vez
e os documentos de texto ficam na raiz.

## Visão geral em árvore

```
reproduction/
  config.py                 parametros centrais (area, resolucao, periodos, fontes)
  run_all.py                roda a reproducao inteira
  run_contrib.py            roda a contribuicao inteira
  README.md                 visao geral e como rodar
  REPRODUCTION_REPORT.md    relatorio da reproducao do artigo
  CONTRIBUICAO.md           relatorio da contribuicao do grupo
  IDEIAS_DE_CONTRIBUICAO.md lista de propostas de continuacao
  ARQUITETURA.md            este documento
  src/                      todo o codigo, um arquivo por etapa
  data/
    raw/                    dados brutos baixados
      nasa/                 80 CSVs (um por ponto) + _manifest.csv
      inmet/                36 CSVs (um por estacao) + _stations.csv
    processed/              dados tratados (medias, MM grid, indices)
    external/               dados de apoio (malha do IBGE, zips do INMET)
  outputs/
    tables/                 tabelas em CSV (Tabela 2, rankings, comparacoes)
    figures/                mapas e graficos em PNG
```

## Convenções de nomes

Entender alguns padrões de nome ajuda a ler o resto:

- Muitos arquivos aparecem em par, um terminando em `_nasa` e outro em `_inmet`. Isso
  acontece porque o trabalho processa as duas fontes em paralelo, do mesmo jeito que o
  artigo: NASA são os dados de satélite e INMET são os dados das estações no chão.
- `mm_grid` se refere à grade fina de 0,05 grau (o Multi-Map grid) que cobre a Paraíba.
- O sufixo `_cov` indica que o arquivo tem as covariáveis da contribuição (elevação e
  distância à costa).
- O sufixo `_ml` indica que o resultado veio dos modelos de aprendizado de máquina.
- `compl` e `kappa` se referem à complementaridade temporal (a Ideia 1).
- `hybrid_index` e `hybridplus` se referem ao índice de geração híbrida da contribuição.

## Arquivos na raiz

| Arquivo | O que é e para que serve |
|---|---|
| config.py | Guarda todos os parâmetros num lugar só: área da Paraíba, resolução das grades, períodos, número de vizinhos da interpolação e os endereços das fontes de dados. Todos os códigos de `src` importam daqui. |
| run_all.py | Executa, na ordem certa, todas as etapas da reprodução do artigo. |
| run_contrib.py | Executa, na ordem certa, todas as etapas da contribuição. Pressupõe que a reprodução já foi rodada. |
| README.md | Visão geral curta do projeto, lista de documentos, como rodar e dependências. |
| REPRODUCTION_REPORT.md | Relatório da reprodução: fontes de dados, instalação passo a passo, fluxograma e comparação dos resultados com o artigo. |
| CONTRIBUICAO.md | Relatório da contribuição, separando o que é reprodução do que é novo. |
| IDEIAS_DE_CONTRIBUICAO.md | As cinco ideias de continuação que foram levantadas. |
| ARQUITETURA.md | Este documento. |

## Pasta src: o código

Cada arquivo cuida de uma etapa. Os de reprodução refazem passos do artigo. Os de
contribuição implementam o que foi acrescentado pelo grupo. Os de apoio foram usados só
para investigar as fontes de dados durante o desenvolvimento.

### Códigos da reprodução

| Arquivo | O que faz |
|---|---|
| data_ibge.py | Baixa a malha (o contorno) dos 223 municípios da Paraíba no IBGE e salva em `data/external`. |
| data_nasa.py | Monta a grade de 0,5 grau e baixa do NASA POWER as séries diárias de vento e radiação de cada ponto. Salva em `data/raw/nasa`. |
| data_inmet.py | Baixa os arquivos zip anuais do INMET (2003 a 2022), extrai as 36 estações de interesse e lê vento e radiação hora a hora. Salva em `data/raw/inmet`. |
| preprocess.py | Limpa os dados, converte a radiação do INMET (filtro de dia, kJ para kWh) e calcula a média histórica de vento e radiação por ponto. Gera os arquivos `nasa_points.csv` e `inmet_points.csv`. |
| interpolation.py | Implementa o IDW e o Kriging e os compara por validação cruzada (RMSE, MAE e R2). Gera a Tabela 2. |
| mm_grid.py | Cria a grade fina de 0,05 grau dentro da Paraíba e interpola vento e radiação por Kriging. Gera os arquivos `mm_grid_nasa.csv` e `mm_grid_inmet.csv`. |
| ip_pb.py | Normaliza as variáveis, calcula o índice IP-PB por município, separa os municípios em grupos e monta os rankings dos 10 melhores. |
| plots.py | Gera os mapas e gráficos que correspondem às Figuras 5 a 16 do artigo. |

### Códigos da contribuição

| Arquivo | O que faz |
|---|---|
| covariates.py | Coleta as covariáveis físicas: elevação (API Open-Meteo) e distância à costa. Gera as versões `_cov` dos pontos. |
| ml_interpolation.py | Treina e compara os modelos de aprendizado de máquina (Random Forest, Gradient Boosting e Regression Kriging) com o Kriging do artigo. Gera a tabela de comparação e o MM grid por aprendizado de máquina. |
| complementarity.py | Calcula a complementaridade temporal kappa entre vento e sol em cada ponto e a interpola para o MM grid. |
| hybrid_index.py | Junta a magnitude do recurso com a complementaridade no índice híbrido IPH e gera o ranking comparativo. |
| plots_contrib.py | Gera as figuras da contribuição (comparação dos modelos, mapa de kappa, ranking híbrido e ciclo mensal). |

### Scripts de apoio

Estes dois foram usados apenas para investigar as fontes de dados durante o
desenvolvimento. Eles não fazem parte do pipeline e não são chamados pelo `run_all.py`
nem pelo `run_contrib.py`. Ficam guardados para registro do que foi feito.

| Arquivo | O que faz |
|---|---|
| inmet_explore.py | Listou as estações automáticas do INMET na região e testou a API de dados (que se mostrou instável). |
| inmet_inspect.py | Abriu um arquivo zip do INMET para descobrir o formato dos CSVs (separador, cabeçalho, nomes das colunas). |

## Pasta data: os dados

### data/raw (dados brutos)

| Caminho | O que contém |
|---|---|
| nasa/nasa_LAT_LON.csv | Uma série diária de vento e radiação por ponto da grade NASA (80 arquivos). |
| nasa/_manifest.csv | Lista dos pontos NASA baixados. |
| inmet/A###.csv | Uma série horária de vento e radiação por estação INMET (36 arquivos, um por código de estação). |
| inmet/_stations.csv | Catálogo das estações usadas, com código, nome, estado e coordenadas. |

### data/processed (dados tratados)

Resultados intermediários, já limpos e prontos para as próximas etapas.

| Arquivo | O que contém |
|---|---|
| nasa_points.csv, inmet_points.csv | Médias históricas de vento e radiação por ponto (reprodução). |
| mm_grid_points.csv | Os pontos da grade fina dentro da Paraíba, com o município de cada um. |
| mm_grid_nasa.csv, mm_grid_inmet.csv | A grade fina com vento e radiação interpolados por Kriging (reprodução). |
| ip_pb_nasa.csv, ip_pb_inmet.csv | O índice IP-PB por município, com os grupos (reprodução). |
| nasa_points_cov.csv, inmet_points_cov.csv | Os pontos com as covariáveis elevação e distância à costa (contribuição). |
| mm_grid_cov.csv | A grade fina com as covariáveis (contribuição). |
| mm_grid_ml_nasa.csv, mm_grid_ml_inmet.csv | A grade fina interpolada por aprendizado de máquina (contribuição). |
| compl_nasa.csv, compl_inmet.csv | A complementaridade kappa por ponto (contribuição). |
| kappa_grid_nasa.csv, kappa_grid_inmet.csv | A complementaridade interpolada para a grade fina (contribuição). |
| hybrid_index_nasa.csv, hybrid_index_inmet.csv | O índice híbrido IPH por município, com os rankings (contribuição). |

### data/external (dados de apoio)

| Arquivo | O que contém |
|---|---|
| pb_municipios.geojson | A malha dos municípios como veio do IBGE. |
| pb_municipios.gpkg | A mesma malha já tratada, no formato lido pelo geopandas. |
| inmet_AAAA.zip | Os arquivos anuais do INMET (2003 a 2022) guardados em cache, para não baixar de novo. |

## Pasta outputs: os resultados

### outputs/tables

| Arquivo | O que contém |
|---|---|
| table2_nasa.csv, table2_inmet.csv | A comparação entre IDW e Kriging (a Tabela 2 do artigo). |
| rank_solar, rank_wind, rank_hybrid (nasa e inmet) | Os 10 melhores municípios para cada tipo de energia (reprodução). |
| contrib_ml_nasa.csv, contrib_ml_inmet.csv | A comparação entre o Kriging e os modelos de aprendizado de máquina (contribuição). |
| rank_hybridplus_nasa.csv, rank_hybridplus_inmet.csv | Os 10 melhores municípios pelo índice híbrido IPH (contribuição). |

### outputs/figures

Guarda as 16 figuras em PNG. As que começam com `mm_`, `scatter_ippb_`, `top10_` e
`correlation_` são da reprodução (correspondem às Figuras 5 a 16 do artigo). As que
começam com `contrib_` são da contribuição (comparação dos modelos, mapa de
complementaridade, ranking híbrido e ciclo mensal de vento e sol).
