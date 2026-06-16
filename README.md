# RenovAtlas

RenovAtlas é uma solução de aprendizado de máquina que estima e ranqueia o potencial de
geração de energia renovável (solar, eólica e híbrida) nos 223 municípios da Paraíba.
A solução coleta dados públicos, treina e compara modelos de regressão para estimar
vento e radiação, calcula o índice de potencial e disponibiliza os resultados num
dashboard interativo, com rastreamento de experimentos e ambiente reproduzível.

## Equipe

- Guilherme Cardozo de Castro Melo (@cardozoguilherme)
- Henrique Lobo Queiroz Guimarães
- Rodrigo Leal Marques

## Disciplina e instituição

Machine Learning I e Projeto 3.
CESAR School.

## Sobre a solução

O trabalho parte do artigo "A new index to evaluate renewable energy potential: A case
study on solar, wind and hybrid generation in Northeast Brazil" (Ferreira et al.,
Renewable Energy 217, 2023). Primeiro o artigo é reproduzido (coleta de dados,
interpolação por IDW e Kriging, construção de um mapa de alta resolução e cálculo do
índice IP-PB). Depois o grupo contribui com modelos de aprendizado de máquina para a
estimativa das variáveis e com um índice de geração híbrida que considera a
complementaridade temporal entre vento e sol.

## Estrutura do repositório

```
data/        dados (brutos não versionados; processados versionados)
notebooks/   análise exploratória (EDA) e experimentos
src/         código de coleta, processamento, modelagem e índices
app/         dashboard interativo (Streamlit)
mlruns/      experimentos do MLflow (gerado em execução)
outputs/     tabelas e figuras
Dockerfile
requirements.txt
README.md
```

## Como executar

### Ambiente local

Pré-requisito: Python 3.10 ou mais novo.

```
pip install -r requirements.txt

# reprodução do artigo (coleta, interpolação, índice, figuras)
python run_all.py

# contribuição (modelos de ML, complementaridade, índice híbrido)
python run_contrib.py

# treinamento dos modelos com rastreamento no MLflow
python src/train.py

# visualizar os experimentos do MLflow
mlflow ui

# abrir o dashboard
streamlit run app/dashboard.py
```

### Com Docker

```
docker build -t renovatlas .
docker run -p 8501:8501 renovatlas
```

O dashboard fica disponível em http://localhost:8501.

## Documentos

- ARQUITETURA.md: o que é e para que serve cada diretório e arquivo.
- REPRODUCTION_REPORT.md: a reprodução do artigo, com instalação e comparação.
- CONTRIBUICAO.md: a contribuição do grupo (ML e complementaridade temporal).
- IDEIAS_DE_CONTRIBUICAO.md: propostas de continuação.

## Dependências

numpy, pandas, scipy, scikit-learn, matplotlib, pykrige, geopandas, requests, mlflow e
streamlit. As versões estão fixadas em requirements.txt.
