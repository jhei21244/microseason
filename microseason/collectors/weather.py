"""Open-Meteo weather collector — daily forecast + historical archive."""

import httpx
from datetime import date, timedelta

from ..config import LAT, LON, OPENMETEO_FORECAST, OPENMETEO_ARCHIVE
from ..database import Database

DAILY_VARS = [
    "temperature_2m_max", "temperature_2m_min", "temperature_2m_mean",
    "precipitation_sum", "relative_humidity_2m_mean",
    "windspeed_10m_max", "winddirection_10m_dominant",
    "pressure_msl_mean", "uv_index_max",
    "shortwave_radiation_sum", "cloud_cover_mean",
]

HOURLY_VARS = ["soil_temperature_0cm", "soil_moisture_0_to_1cm"]


class WeatherCollector:
    def __init__(self, db: Database):
        self.db = db

    def collect_today(self) -> int:
        """Fetch today's weather. Returns rows stored."""
        today = date.today().isoformat()
        params = {
            "latitude": LAT, "longitude": LON,
            "daily": ",".join(DAILY_VARS),
            "hourly": ",".join(HOURLY_VARS),
            "timezone": "Australia/Sydney",
            "start_date": today, "end_date": today,
        }
        resp = httpx.get(OPENMETEO_FORECAST, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        d = data["daily"]
        # Average hourly soil readings for the day
        h = data.get("hourly", {})
        soil_temps = [v for v in (h.get("soil_temperature_0cm") or []) if v is not None]
        soil_moist = [v for v in (h.get("soil_moisture_0_to_1cm") or []) if v is not None]

        self.db.upsert_weather(
            today,
            max_temp=d["temperature_2m_max"][0],
            min_temp=d["temperature_2m_min"][0],
            mean_temp=d.get("temperature_2m_mean", [None])[0],
            precipitation=d["precipitation_sum"][0],
            humidity=d.get("relative_humidity_2m_mean", [None])[0],
            wind_speed=d["windspeed_10m_max"][0],
            wind_direction=d.get("winddirection_10m_dominant", [None])[0],
            pressure=d.get("pressure_msl_mean", [None])[0],
            uv_index_max=d.get("uv_index_max", [None])[0],
            soil_temp_0cm=sum(soil_temps) / len(soil_temps) if soil_temps else None,
            soil_moisture_0_1cm=sum(soil_moist) / len(soil_moist) if soil_moist else None,
            cloud_cover=d.get("cloud_cover_mean", [None])[0],
        )
        print(f"  weather: {today} — {d['temperature_2m_min'][0]}°/{d['temperature_2m_max'][0]}°")
        return 1

    def backfill(self, days: int = 365) -> int:
        """Fetch historical weather in 90-day chunks."""
        end = date.today() - timedelta(days=1)
        start = end - timedelta(days=days)
        total = 0
        chunk_size = 90

        current_start = start
        while current_start <= end:
            current_end = min(current_start + timedelta(days=chunk_size - 1), end)
            print(f"  weather backfill: {current_start} to {current_end}...")

            params = {
                "latitude": LAT, "longitude": LON,
                "daily": ",".join(DAILY_VARS),
                "hourly": ",".join(HOURLY_VARS),
                "timezone": "Australia/Sydney",
                "start_date": current_start.isoformat(),
                "end_date": current_end.isoformat(),
            }
            resp = httpx.get(OPENMETEO_ARCHIVE, params=params, timeout=60)
            resp.raise_for_status()
            data = resp.json()

            d = data["daily"]
            h = data.get("hourly", {})
            dates = d["time"]
            hours_per_day = 24

            for i, dt in enumerate(dates):
                # Extract hourly soil data for this day
                h_start = i * hours_per_day
                h_end = h_start + hours_per_day
                soil_t = [v for v in (h.get("soil_temperature_0cm") or [])[h_start:h_end] if v is not None]
                soil_m = [v for v in (h.get("soil_moisture_0_to_1cm") or [])[h_start:h_end] if v is not None]

                self.db.upsert_weather(
                    dt,
                    max_temp=d["temperature_2m_max"][i],
                    min_temp=d["temperature_2m_min"][i],
                    mean_temp=d.get("temperature_2m_mean", [None] * len(dates))[i],
                    precipitation=d["precipitation_sum"][i],
                    humidity=d.get("relative_humidity_2m_mean", [None] * len(dates))[i],
                    wind_speed=d["windspeed_10m_max"][i],
                    wind_direction=d.get("winddirection_10m_dominant", [None] * len(dates))[i],
                    pressure=d.get("pressure_msl_mean", [None] * len(dates))[i],
                    uv_index_max=d.get("uv_index_max", [None] * len(dates))[i],
                    soil_temp_0cm=sum(soil_t) / len(soil_t) if soil_t else None,
                    soil_moisture_0_1cm=sum(soil_m) / len(soil_m) if soil_m else None,
                    cloud_cover=d.get("cloud_cover_mean", [None] * len(dates))[i],
                )
                total += 1

            current_start = current_end + timedelta(days=1)

        print(f"  weather backfill complete: {total} days")
        return total
