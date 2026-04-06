"""Data collectors for environmental signal sources."""

from .weather import WeatherCollector
from .astronomy import AstronomyCollector
from .uv import UVCollector
from .nature import NatureCollector
from .climatewatch import ClimateWatchCollector
from .melbourne_water import MelbourneWaterCollector
from .city_of_melbourne import CityOfMelbourneCollector

__all__ = [
    "WeatherCollector",
    "AstronomyCollector",
    "UVCollector",
    "NatureCollector",
    "ClimateWatchCollector",
    "MelbourneWaterCollector",
    "CityOfMelbourneCollector",
]
