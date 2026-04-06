"""ARPANSA UV collector — real-time UV index for Melbourne."""

import httpx
import xml.etree.ElementTree as ET
from datetime import datetime

from ..config import ARPANSA_UV_URL, ARPANSA_MELBOURNE_ID
from ..database import Database


class UVCollector:
    def __init__(self, db: Database):
        self.db = db

    def collect_now(self) -> float | None:
        """Fetch current UV reading for Melbourne. Returns UV index or None."""
        resp = httpx.get(ARPANSA_UV_URL, timeout=15)
        resp.raise_for_status()

        root = ET.fromstring(resp.text)
        for loc in root.findall("location"):
            if loc.get("id") == ARPANSA_MELBOURNE_ID:
                uv_str = loc.findtext("index")
                ts_str = loc.findtext("utcdatetime")
                status = loc.findtext("status")

                if status != "ok" or uv_str is None:
                    print(f"  uv: Melbourne station status={status}")
                    return None

                uv_val = float(uv_str)
                timestamp = ts_str or datetime.utcnow().isoformat()

                self.db.insert_uv(timestamp, ARPANSA_MELBOURNE_ID, uv_val)
                print(f"  uv: Melbourne UV={uv_val} at {timestamp}")
                return uv_val

        print("  uv: Melbourne station not found")
        return None
