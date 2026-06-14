# -*- coding: utf-8 -*-
"""Central configuration for the reproduction of Ferreira et al. (2023),
'A new index to evaluate renewable energy potential' (Renewable Energy 217, 119182).

All tunable parameters live here so the pipeline is reproducible end-to-end.
"""
from pathlib import Path

# ----------------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
RAW = DATA / "raw"
PROCESSED = DATA / "processed"
EXTERNAL = DATA / "external"
OUTPUTS = ROOT / "outputs"
FIGURES = OUTPUTS / "figures"
TABLES = OUTPUTS / "tables"
for _d in (RAW, PROCESSED, EXTERNAL, FIGURES, TABLES):
    _d.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------------
# Geographic extent
# ----------------------------------------------------------------------------
# Paraíba bounding box (the easternmost point of the Americas, Ponta do Seixas,
# is at lon ~-34.79; western border with Ceará ~-38.77).
PB_BBOX = dict(lat_min=-8.35, lat_max=-5.98, lon_min=-38.85, lon_max=-34.75)

# Wider box used to collect ground/satellite points in PB + neighbouring states
# (RN to the north, PE to the south, CE to the west) so that interpolation near
# the PB border is not affected by edge effects.
COLLECT_BBOX = dict(lat_min=-9.6, lat_max=-4.8, lon_min=-40.2, lon_max=-34.4)

# ----------------------------------------------------------------------------
# NASA POWER (satellite) — https://power.larc.nasa.gov/
# ----------------------------------------------------------------------------
NASA_RES = 0.5  # degrees between grid points (~55 km), as in the paper
# Grid covering PB + a 0.5-1.0 deg ring of neighbours
NASA_GRID = dict(lat_min=-9.0, lat_max=-5.5, lon_min=-39.0, lon_max=-34.5)
NASA_PARAMS = ["WS10M", "ALLSKY_SFC_SW_DWN"]  # wind @10m (m/s); insolation (kWh/m2/day)
NASA_COMMUNITY = "RE"  # Renewable Energy community
NASA_START = "19850101"
NASA_END = "20220820"
NASA_API = "https://power.larc.nasa.gov/api/temporal/daily/point"

# ----------------------------------------------------------------------------
# INMET (ground stations) — https://portal.inmet.gov.br/dadoshistoricos
# ----------------------------------------------------------------------------
INMET_STATIONS_API = "https://apitempo.inmet.gov.br/estacoes/T"  # automatic stations
INMET_HIST_URL = "https://portal.inmet.gov.br/uploads/dadoshistoricos/{year}.zip"
INMET_END = "20220820"
# The 9 PB municipalities named in the paper (for validation/labelling).
INMET_PB_MUNICIPALITIES = [
    "AREIA", "CAMPINA GRANDE", "JOAO PESSOA", "PATOS", "SAO GONCALO",
    "MONTEIRO", "CABACEIRAS", "CAMARATUBA", "ITAPORANGA",
]
# Neighbouring states whose border stations are also collected.
INMET_STATES = ["PB", "CE", "PE", "RN"]

# Column names of interest in INMET historical CSVs (vary slightly by year).
INMET_WIND_COL_HINTS = ["VENTO, VELOCIDADE HORARIA"]          # m/s
INMET_RAD_COL_HINTS = ["RADIACAO GLOBAL"]                      # KJ/m2

# ----------------------------------------------------------------------------
# MM (Multi-Map) grid — the interpolated high-resolution product
# ----------------------------------------------------------------------------
MM_RES = 0.05  # degrees (~5.5 km). Points inside the PB polygon (~2054 expected).

# ----------------------------------------------------------------------------
# Interpolation
# ----------------------------------------------------------------------------
N_NEIGHBORS = 4   # nearest neighbours used by IDW/kriging in the paper
IDW_POWER = 2     # inverse-distance exponent (corrected IDW: weight ~ 1/d^p)
KRIGING_VARIOGRAM = "exponential"  # matches Eq. (3): c0 + C[1 - exp(-h/a)]
CV_TEST_FRACTION = 0.16  # 6 of 37 NASA points (~16%) held out for cross-validation
CV_RANDOM_SEED = 42

# Solar irradiation filter (INMET hourly): keep daytime 05:00-18:00.
DAY_START_HOUR = 5
DAY_END_HOUR = 18

# ----------------------------------------------------------------------------
# IBGE (municipal boundaries) — 223 municipalities of Paraíba (UF code 25)
# ----------------------------------------------------------------------------
PB_UF_CODE = 25
IBGE_MALHA_URL = (
    "https://servicodados.ibge.gov.br/api/v3/malhas/estados/25"
    "?formato=application/vnd.geo+json&intrarregiao=municipio&qualidade=intermediaria"
)
IBGE_MUNICIPIOS_URL = (
    "https://servicodados.ibge.gov.br/api/v1/localidades/estados/25/municipios"
)

# Canonical column names used throughout the pipeline
WIND = "WIND_SPEED"      # m/s
SOLAR = "SOLAR_IRRAD"    # kWh/m2/day
