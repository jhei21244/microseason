"""iNaturalist collector — species observations near Melbourne."""

import httpx
import time as _time
from datetime import date, timedelta

from ..config import LAT, LON, INAT_RADIUS_KM, INAT_API, INAT_RATE_LIMIT
from ..database import Database


class NatureCollector:
    def __init__(self, db: Database):
        self.db = db

    def _fetch_page(self, params: dict) -> dict:
        resp = httpx.get(INAT_API, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _parse_obs(self, obs: dict) -> dict | None:
        taxon = obs.get("taxon")
        if not taxon:
            return None
        return {
            "source": "inat",
            "source_id": str(obs["id"]),
            "observed_on": obs.get("observed_on"),
            "taxon_name": taxon.get("name"),
            "common_name": taxon.get("preferred_common_name"),
            "iconic_taxon": taxon.get("iconic_taxon_name"),
            "lat": obs.get("geojson", {}).get("coordinates", [None, None])[1] if obs.get("geojson") else None,
            "lon": obs.get("geojson", {}).get("coordinates", [None, None])[0] if obs.get("geojson") else None,
            "quality_grade": obs.get("quality_grade"),
            "observer": obs.get("user", {}).get("login"),
            "photo_url": obs.get("photos", [{}])[0].get("url") if obs.get("photos") else None,
        }

    def collect_recent(self, days: int = 7) -> int:
        """Fetch recent research-grade observations near Melbourne."""
        since = (date.today() - timedelta(days=days)).isoformat()
        params = {
            "lat": LAT, "lng": LON, "radius": INAT_RADIUS_KM,
            "quality_grade": "research",
            "d1": since,
            "per_page": 200, "page": 1,
            "order_by": "observed_on",
        }

        total = 0
        while True:
            data = self._fetch_page(params)
            results = data.get("results", [])
            if not results:
                break

            batch = []
            for obs in results:
                parsed = self._parse_obs(obs)
                if parsed:
                    batch.append(parsed)

            if batch:
                self.db.upsert_species_batch(batch)
                total += len(batch)

            if len(results) < 200:
                break
            params["page"] += 1
            _time.sleep(INAT_RATE_LIMIT)

        print(f"  nature: {total} observations from last {days} days")
        return total

    def backfill(self, days: int = 365) -> int:
        """Fetch historical observations in 30-day chunks."""
        end = date.today()
        start = end - timedelta(days=days)
        total = 0
        chunk_days = 30

        current_start = start
        while current_start <= end:
            current_end = min(current_start + timedelta(days=chunk_days - 1), end)
            print(f"  nature backfill: {current_start} to {current_end}...")

            params = {
                "lat": LAT, "lng": LON, "radius": INAT_RADIUS_KM,
                "quality_grade": "research",
                "d1": current_start.isoformat(),
                "d2": current_end.isoformat(),
                "per_page": 200, "page": 1,
                "order_by": "observed_on",
            }

            chunk_total = 0
            while True:
                data = self._fetch_page(params)
                results = data.get("results", [])
                if not results:
                    break

                batch = []
                for obs in results:
                    parsed = self._parse_obs(obs)
                    if parsed:
                        batch.append(parsed)

                if batch:
                    self.db.upsert_species_batch(batch)
                    chunk_total += len(batch)
                    total += len(batch)

                if len(results) < 200:
                    break
                if params["page"] >= 40:
                    print(f"    → capping at page 40 to avoid rate limit")
                    break
                params["page"] += 1
                _time.sleep(INAT_RATE_LIMIT * 2)  # 2s between pages for backfill

            print(f"    → {chunk_total} observations")
            current_start = current_end + timedelta(days=1)

        print(f"  nature backfill complete: {total} observations")
        return total
