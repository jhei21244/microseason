"""Sunrise-Sunset.org collector — day length, twilight, golden hour."""

import httpx
import time as _time
from datetime import date, timedelta, datetime

from ..config import LAT, LON, SUNRISE_API
from ..database import Database


class AstronomyCollector:
    def __init__(self, db: Database):
        self.db = db

    def _fetch_date(self, dt: date) -> dict | None:
        params = {"lat": LAT, "lng": LON, "formatted": 0, "date": dt.isoformat()}
        resp = httpx.get(SUNRISE_API, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data["status"] != "OK":
            return None
        return data["results"]

    def _store(self, dt: date, r: dict):
        self.db.upsert_astronomy(
            dt.isoformat(),
            sunrise=r["sunrise"],
            sunset=r["sunset"],
            day_length_seconds=r["day_length"],
            civil_twilight_begin=r["civil_twilight_begin"],
            civil_twilight_end=r["civil_twilight_end"],
            golden_hour_morning=r["civil_twilight_begin"],  # approximation
            golden_hour_evening=r["civil_twilight_end"],     # approximation
            solar_noon=r["solar_noon"],
        )

    def collect_today(self) -> int:
        today = date.today()
        r = self._fetch_date(today)
        if r:
            self._store(today, r)
            dl_min = r["day_length"] // 60
            dl_sec = r["day_length"] % 60
            print(f"  astronomy: {today} — day length {dl_min}m{dl_sec}s")
            return 1
        return 0

    def backfill(self, days: int = 365) -> int:
        """Fetch historical astronomy data day by day (API only does one date)."""
        end = date.today()
        start = end - timedelta(days=days)
        total = 0

        current = start
        while current <= end:
            try:
                r = self._fetch_date(current)
                if r:
                    self._store(current, r)
                    total += 1
                if total % 30 == 0 and total > 0:
                    print(f"  astronomy backfill: {total} days ({current})...")
            except Exception as e:
                print(f"  astronomy error {current}: {e}")
            current += timedelta(days=1)
            _time.sleep(0.3)  # be polite to the API

        print(f"  astronomy backfill complete: {total} days")
        return total
