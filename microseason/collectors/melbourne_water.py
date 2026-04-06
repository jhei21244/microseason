"""Melbourne Water collector — river levels and rainfall from ArcGIS Open Data Hub."""

import httpx
from datetime import date, timedelta

from ..config import LAT, LON
from ..database import Database

# Key Melbourne Water datasets
RAINFALL_URL = "https://data-melbournewater.opendata.arcgis.com/api/v3/datasets"
# We'll query the ArcGIS feature service directly for recent data
FEATURE_BASE = "https://services5.arcgis.com/ZSYwjtv8RKVhkXIR/arcgis/rest/services"


class MelbourneWaterCollector:
    def __init__(self, db: Database):
        self.db = db

    def collect_datasets(self) -> list[dict]:
        """List available Melbourne Water datasets via ArcGIS Hub search."""
        resp = httpx.get(
            "https://data-melbournewater.opendata.arcgis.com/api/search/v1",
            params={"q": "rainfall streamflow", "num": 20},
            timeout=30,
        )
        if resp.status_code != 200:
            # Fallback: just confirm the hub is reachable
            resp2 = httpx.get("https://data-melbournewater.opendata.arcgis.com/", timeout=15)
            print(f"  melbourne_water: hub reachable (status {resp2.status_code})")
            return []
        data = resp.json()
        datasets = []
        for item in data.get("data", data.get("results", [])):
            name = item.get("title", item.get("name", ""))
            datasets.append({"name": name})
        return datasets

    def collect_recent(self) -> int:
        """Fetch recent rainfall and streamflow data from Melbourne Water.

        Melbourne Water publishes data through ArcGIS — we query the datasets
        API and store summary data. Detailed time-series requires specific
        station queries which we'll add when station IDs are confirmed.
        """
        # For now, record that we checked and log available datasets
        datasets = self.collect_datasets()
        print(f"  melbourne_water: {len(datasets)} water datasets available")
        for ds in datasets[:5]:
            print(f"    {ds['name']}")
        return len(datasets)
