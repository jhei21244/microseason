"""City of Melbourne collector — microclimate sensors + soil sensors + tree data."""

import httpx
from datetime import date

from ..config import COM_API
from ..database import Database


class CityOfMelbourneCollector:
    def __init__(self, db: Database):
        self.db = db

    def collect_microclimate(self) -> int:
        """Fetch microclimate sensor readings from City of Melbourne Open Data."""
        # Query sensor locations first to understand what's available
        url = f"{COM_API}/microclimate-sensor-locations/records"
        resp = httpx.get(url, params={"limit": 50}, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        locations = data.get("results", [])
        active = [l for l in locations if l.get("site_status") == "C"]  # C = Current
        print(f"  city_of_melbourne: {len(active)} active microclimate sensors, {len(locations)} total")

        for loc in active[:3]:
            print(f"    Site {loc.get('site_id')}: lat={loc.get('latitude')}, lon={loc.get('longitude')}")

        return len(active)

    def collect_soil_sensors(self) -> int:
        """Fetch soil sensor locations."""
        url = f"{COM_API}/soil-sensor-locations/records"
        resp = httpx.get(url, params={"limit": 100}, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        locations = data.get("results", [])
        print(f"  city_of_melbourne: {len(locations)} soil sensor sites")

        for loc in locations[:3]:
            print(f"    {loc.get('site_name', '?')} at {loc.get('property_name', '?')}")

        return len(locations)

    def collect_trees(self) -> dict:
        """Fetch urban forest tree data summary."""
        # Query tree canopy datasets
        url = f"{COM_API}"
        resp = httpx.get(url, params={"limit": 100, "q": "tree canopy urban forest"}, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        datasets = [ds for ds in data.get("results", [])
                    if "tree" in ds.get("metas", {}).get("default", {}).get("title", "").lower()]

        print(f"  city_of_melbourne: {len(datasets)} tree/canopy datasets available")
        for ds in datasets[:5]:
            title = ds.get("metas", {}).get("default", {}).get("title", "?")
            print(f"    {ds.get('dataset_id')}: {title}")

        return {"datasets": len(datasets)}

    def collect_all(self) -> dict:
        """Run all City of Melbourne collectors."""
        results = {}
        try:
            results["microclimate"] = self.collect_microclimate()
        except Exception as e:
            print(f"  ERROR [microclimate]: {e}")
        try:
            results["soil"] = self.collect_soil_sensors()
        except Exception as e:
            print(f"  ERROR [soil]: {e}")
        try:
            results["trees"] = self.collect_trees()
        except Exception as e:
            print(f"  ERROR [trees]: {e}")
        return results
