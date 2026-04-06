"""Configuration constants."""

from pathlib import Path

# Melbourne coordinates
LAT = -37.8136
LON = 144.9631
LOCATION_NAME = "Melbourne"

# Database
DB_PATH = Path(__file__).parent.parent / "microseason.db"

# iNaturalist
INAT_RADIUS_KM = 50
INAT_API = "https://api.inaturalist.org/v1/observations"
INAT_TAXA = ["Plantae", "Aves", "Insecta", "Mammalia", "Reptilia", "Amphibia", "Fungi"]
INAT_RATE_LIMIT = 1.0  # seconds between requests

# Open-Meteo
OPENMETEO_FORECAST = "https://api.open-meteo.com/v1/forecast"
OPENMETEO_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"

# ARPANSA UV
ARPANSA_UV_URL = "https://uvdata.arpansa.gov.au/xml/uvvalues.xml"
ARPANSA_MELBOURNE_ID = "Melbourne"

# Sunrise-Sunset
SUNRISE_API = "https://api.sunrise-sunset.org/json"

# GBIF ClimateWatch
GBIF_API = "https://api.gbif.org/v1/occurrence/search"
CLIMATEWATCH_DATASET = "3fab912e-e927-4f1c-a97c-eb446cd609e0"
GBIF_LAT_RANGE = (-38.0, -37.0)
GBIF_LON_RANGE = (144.0, 146.0)
