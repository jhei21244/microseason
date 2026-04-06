"""GBIF ClimateWatch collector — phenology-specific observations near Melbourne."""

import httpx
import time as _time

from ..config import GBIF_API, CLIMATEWATCH_DATASET, GBIF_LAT_RANGE, GBIF_LON_RANGE
from ..database import Database


class ClimateWatchCollector:
    def __init__(self, db: Database):
        self.db = db

    def collect_all(self) -> int:
        """Fetch all ClimateWatch records near Melbourne from GBIF."""
        total = 0
        offset = 0
        limit = 300

        while True:
            params = {
                "datasetKey": CLIMATEWATCH_DATASET,
                "decimalLatitude": f"{GBIF_LAT_RANGE[0]},{GBIF_LAT_RANGE[1]}",
                "decimalLongitude": f"{GBIF_LON_RANGE[0]},{GBIF_LON_RANGE[1]}",
                "limit": limit,
                "offset": offset,
            }

            resp = httpx.get(GBIF_API, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            results = data.get("results", [])
            if not results:
                break

            batch = []
            for r in results:
                event_date = r.get("eventDate", "")[:10] if r.get("eventDate") else None
                batch.append({
                    "source": "gbif",
                    "source_id": str(r.get("key", r.get("gbifID", ""))),
                    "observed_on": event_date,
                    "taxon_name": r.get("species") or r.get("scientificName"),
                    "common_name": r.get("vernacularName"),
                    "iconic_taxon": r.get("class"),
                    "lat": r.get("decimalLatitude"),
                    "lon": r.get("decimalLongitude"),
                    "quality_grade": "research",
                    "observer": r.get("recordedBy"),
                    "photo_url": None,
                })

            if batch:
                self.db.upsert_species_batch(batch)
                total += len(batch)

            if data.get("endOfRecords", True):
                break
            offset += limit
            _time.sleep(0.5)

            if offset % 3000 == 0:
                print(f"  climatewatch: {total} records so far...")

        print(f"  climatewatch: {total} total phenology records")
        return total
