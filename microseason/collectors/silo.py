"""SILO climate collector — daily gridded climate data from 1889 to present.

SILO (Scientific Information for Land Owners) is maintained by Queensland DES.
Provides interpolated daily climate for any Australian coordinate.
"""

import csv
import io
import httpx
from datetime import date, timedelta

from ..config import LAT, LON
from ..database import Database

SILO_URL = "https://www.longpaddock.qld.gov.au/cgi-bin/silo/DataDrillDataset.php"


class SILOCollector:
    def __init__(self, db: Database):
        self.db = db

    def _fetch_range(self, start: date, end: date) -> list[dict]:
        params = {
            "lat": LAT, "lon": LON,
            "start": start.strftime("%Y%m%d"),
            "finish": end.strftime("%Y%m%d"),
            "format": "csv",
            "comment": "microseason_calendar",
            "username": "microseason@noreply.dev",
            "password": "api",
        }
        resp = httpx.get(SILO_URL, params=params, timeout=60)
        resp.raise_for_status()

        reader = csv.DictReader(io.StringIO(resp.text))
        records = []
        for row in reader:
            records.append({
                "date": row.get("YYYY-MM-DD", "").strip(),
                "min_temp": _float(row.get("min_temp")),
                "daily_rain": _float(row.get("daily_rain")),
                "evap_pan": _float(row.get("evap_pan")),
                "mslp": _float(row.get("mslp")),
                "vp_deficit": _float(row.get("vp_deficit")),
            })
        return records

    def collect_recent(self, days: int = 7) -> int:
        """Fetch last N days of SILO climate data."""
        end = date.today() - timedelta(days=1)  # SILO lags by ~1 day
        start = end - timedelta(days=days)
        records = self._fetch_range(start, end)

        for r in records:
            if not r["date"]:
                continue
            # Supplement existing weather data with SILO fields
            self.db.upsert_weather(
                r["date"],
                pressure=r["mslp"],
            )

        print(f"  silo: {len(records)} days of climate data ({start} to {end})")
        return len(records)

    def backfill(self, days: int = 365) -> int:
        """Backfill historical SILO data in 90-day chunks."""
        end = date.today() - timedelta(days=1)
        start = end - timedelta(days=days)
        total = 0
        chunk = 90

        current = start
        while current <= end:
            chunk_end = min(current + timedelta(days=chunk - 1), end)
            print(f"  silo backfill: {current} to {chunk_end}...")

            try:
                records = self._fetch_range(current, chunk_end)
                for r in records:
                    if not r["date"]:
                        continue
                    self.db.upsert_weather(
                        r["date"],
                        pressure=r["mslp"],
                    )
                    total += 1
            except Exception as e:
                print(f"    ERROR: {e}")

            current = chunk_end + timedelta(days=1)

        print(f"  silo backfill complete: {total} days")
        return total


def _float(val):
    try:
        return float(val.strip()) if val and val.strip() else None
    except (ValueError, AttributeError):
        return None
