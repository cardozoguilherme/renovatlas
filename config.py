# -*- coding: utf-8 -*-
"""Configuracao central do projeto RenovAtlas.

O projeto reproduz e estende o artigo de Ferreira et al. (2023), "A new index to
evaluate renewable energy potential" (Renewable Energy 217, 119182).

Todos os parametros ajustaveis ficam reunidos aqui. Assim, para mudar a area de estudo,
a resolucao das grades, os periodos ou os enderecos das fontes de dados, basta editar
este arquivo, sem mexer no resto do codigo. Todos os modulos importam deste arquivo.
"""
from pathlib import Path

# ----------------------------------------------------------------------------
# Caminhos das pastas
# ROOT e a pasta onde este arquivo esta (a raiz do projeto). Os demais caminhos sao
# montados a partir dela, entao o codigo funciona em qualquer maquina, sem caminho fixo.
# ----------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
RAW = DATA / "raw"              # dados brutos baixados (NASA e INMET)
PROCESSED = DATA / "processed"  # dados ja tratados (medias, grids, indices)
EXTERNAL = DATA / "external"    # dados de apoio (malha do IBGE, zips do INMET)
OUTPUTS = ROOT / "outputs"
FIGURES = OUTPUTS / "figures"   # figuras geradas (mapas e graficos)
TABLES = OUTPUTS / "tables"     # tabelas geradas (arquivos CSV)
# Cria as pastas caso ainda nao existam, evitando erro na hora de salvar os arquivos.
for _d in (RAW, PROCESSED, EXTERNAL, FIGURES, TABLES):
    _d.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------------
# Extensao geografica
# ----------------------------------------------------------------------------
# Caixa que envolve a Paraiba (bounding box). O ponto mais a leste das Americas, a Ponta
# do Seixas, fica em longitude ~-34,79; a divisa oeste com o Ceara fica em ~-38,77.
PB_BBOX = dict(lat_min=-8.35, lat_max=-5.98, lon_min=-38.85, lon_max=-34.75)

# Caixa maior, usada para coletar pontos (satelite e estacoes) na Paraiba e nos estados
# vizinhos (RN ao norte, PE ao sul, CE a oeste). Coletar uma faixa alem da fronteira evita
# o "efeito de borda": a interpolacao perto do limite do estado fica mais confiavel quando
# ha pontos do lado de fora tambem.
COLLECT_BBOX = dict(lat_min=-9.6, lat_max=-4.8, lon_min=-40.2, lon_max=-34.4)

# ----------------------------------------------------------------------------
# NASA POWER (dados de satelite) -- https://power.larc.nasa.gov/
# ----------------------------------------------------------------------------
NASA_RES = 0.5  # espacamento entre pontos da grade, em graus (~55 km), como no artigo
# Grade que cobre a Paraiba mais um anel de pontos vizinhos.
NASA_GRID = dict(lat_min=-9.0, lat_max=-5.5, lon_min=-39.0, lon_max=-34.5)
# Variaveis coletadas: vento a 10 m (m/s) e radiacao solar diaria (kWh/m2/dia).
NASA_PARAMS = ["WS10M", "ALLSKY_SFC_SW_DWN"]
NASA_COMMUNITY = "RE"     # comunidade "Renewable Energy" da API POWER
NASA_START = "19850101"   # inicio do periodo (1 de janeiro de 1985)
NASA_END = "20220820"     # fim do periodo (20 de agosto de 2022)
NASA_API = "https://power.larc.nasa.gov/api/temporal/daily/point"

# ----------------------------------------------------------------------------
# INMET (estacoes no chao) -- https://portal.inmet.gov.br/dadoshistoricos
# ----------------------------------------------------------------------------
INMET_STATIONS_API = "https://apitempo.inmet.gov.br/estacoes/T"  # catalogo das estacoes automaticas
# Os dados historicos vem em um arquivo zip por ano (cada zip traz todas as estacoes do Brasil).
INMET_HIST_URL = "https://portal.inmet.gov.br/uploads/dadoshistoricos/{year}.zip"
INMET_END = "20220820"
# As 9 estacoes da Paraiba citadas no artigo (usadas para conferencia dos resultados).
INMET_PB_MUNICIPALITIES = [
    "AREIA", "CAMPINA GRANDE", "JOAO PESSOA", "PATOS", "SAO GONCALO",
    "MONTEIRO", "CABACEIRAS", "CAMARATUBA", "ITAPORANGA",
]
# Estados cujas estacoes de fronteira tambem sao coletadas.
INMET_STATES = ["PB", "CE", "PE", "RN"]

# Trechos dos nomes das colunas de interesse nos CSVs do INMET (variam de ano para ano).
INMET_WIND_COL_HINTS = ["VENTO, VELOCIDADE HORARIA"]          # vento (m/s)
INMET_RAD_COL_HINTS = ["RADIACAO GLOBAL"]                     # radiacao (kJ/m2)

# ----------------------------------------------------------------------------
# Grade MM (Multi-Map) -- o produto interpolado de alta resolucao
# ----------------------------------------------------------------------------
# Resolucao de 0,05 grau (~5,5 km). Usa-se os pontos dessa grade que caem dentro do
# poligono da Paraiba (o artigo cita ~2054 pontos; aqui obtem-se ~2016).
MM_RES = 0.05

# ----------------------------------------------------------------------------
# Interpolacao
# ----------------------------------------------------------------------------
N_NEIGHBORS = 4   # numero de vizinhos mais proximos usados por IDW e Kriging (como no artigo)
IDW_POWER = 2     # expoente do IDW: peso ~ 1/distancia^p (a forma correta usa o inverso da distancia)
KRIGING_VARIOGRAM = "exponential"  # modelo de variograma; corresponde a Eq. (3): c0 + C[1 - exp(-h/a)]
CV_TEST_FRACTION = 0.16  # fracao removida na validacao (6 de 37 pontos NASA ~ 16%), como no artigo
CV_RANDOM_SEED = 42      # semente aleatoria, para os resultados serem reproduziveis

# Filtro da radiacao do INMET (dados horarios): mantem so o periodo diurno, das 5 as 18 h.
DAY_START_HOUR = 5
DAY_END_HOUR = 18

# ----------------------------------------------------------------------------
# IBGE (limites municipais) -- 223 municipios da Paraiba (codigo da UF = 25)
# ----------------------------------------------------------------------------
PB_UF_CODE = 25
# URL da malha (os poligonos dos municipios) em formato GeoJSON.
IBGE_MALHA_URL = (
    "https://servicodados.ibge.gov.br/api/v3/malhas/estados/25"
    "?formato=application/vnd.geo+json&intrarregiao=municipio&qualidade=intermediaria"
)
# URL com os nomes dos municipios (para cruzar com o codigo de cada um).
IBGE_MUNICIPIOS_URL = (
    "https://servicodados.ibge.gov.br/api/v1/localidades/estados/25/municipios"
)

# Nomes padronizados das colunas usadas em todo o pipeline.
WIND = "WIND_SPEED"      # vento (m/s)
SOLAR = "SOLAR_IRRAD"    # radiacao solar (kWh/m2/dia)
