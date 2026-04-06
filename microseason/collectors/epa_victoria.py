"""EPA Victoria air quality collector — via data.vic.gov.au open data.

Uses the Victorian Government open data portal which provides EPA air quality
data without requiring developer portal registration.
"""

import httpx
from datetime import date

from ..config import LAT, LON
from ..database import Database

# data.vic.gov.au CKAN API
DATAVIC_API = "https://discover.data.vic.gov.au/api/action"


class EPAVictoriaCollector:
    def __init__(self, db: Database):
        self.db = db

    def collect_recent(self) -> int:
        """Fetch recent EPA air quality data from data.vic.gov.au."""
        # Search for the latest hourly air quality dataset
        resp = httpx.get(
            f"{DATAVIC_API}/package_search",
            params={"q": "epa air quality hourly", "rows": 5},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        results = data.get("result", {}).get("results", [])
        print(f"  epa_victoria: {len(results)} air quality datasets found on data.vic.gov.au")

        for ds in results[:3]:
            name = ds.get("title", "?")
            resources = ds.get("resources", [])
            csv_resources = [r for r in resources if r.get("format", "").upper() == "CSV"]
            print(f"    {name} ({len(csv_resources)} CSV resources)")

            # Try to fetch the most recent CSV resource
            if csv_resources:
                resource = csv_resources[-1]  # Most recent
                resource_url = resource.get("url")
                if resource_url:
                    try:
                        csv_resp = httpx.get(resource_url, timeout=30, follow_redirects=True)
                        if csv_resp.status_code == 200:
                            lines = csv_resp.text.strip().split("\n")
                            print(f"      → {len(lines)-1} rows available")
                            return len(lines) - 1
                    except Exception as e:
                        print(f"      → error fetching CSV: {e}")

        return 0
