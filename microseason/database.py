"""SQLite database layer — schema, upserts, queries."""

import json
import sqlite3
import time
from pathlib import Path

from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS daily_weather (
    date TEXT PRIMARY KEY,
    max_temp REAL, min_temp REAL, mean_temp REAL,
    precipitation REAL, humidity REAL,
    wind_speed REAL, wind_direction REAL,
    pressure REAL, uv_index_max REAL,
    soil_temp_0cm REAL, soil_moisture_0_1cm REAL,
    cloud_cover REAL, evapotranspiration REAL,
    created_at REAL
);

CREATE TABLE IF NOT EXISTS astronomy (
    date TEXT PRIMARY KEY,
    sunrise TEXT, sunset TEXT,
    day_length_seconds INTEGER,
    civil_twilight_begin TEXT, civil_twilight_end TEXT,
    golden_hour_morning TEXT, golden_hour_evening TEXT,
    solar_noon TEXT,
    created_at REAL
);

CREATE TABLE IF NOT EXISTS species_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    source_id TEXT NOT NULL,
    observed_on TEXT,
    taxon_name TEXT,
    common_name TEXT,
    iconic_taxon TEXT,
    lat REAL, lon REAL,
    quality_grade TEXT,
    observer TEXT,
    photo_url TEXT,
    created_at REAL,
    UNIQUE(source, source_id)
);

CREATE TABLE IF NOT EXISTS uv_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    station TEXT,
    uv_index REAL,
    created_at REAL
);

CREATE TABLE IF NOT EXISTS air_quality (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT, hour INTEGER,
    station_name TEXT,
    pm25 REAL, pm10 REAL, ozone REAL, no2 REAL, aqi REAL,
    created_at REAL
);

CREATE TABLE IF NOT EXISTS personal_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    note TEXT NOT NULL,
    tags TEXT,
    photo_path TEXT,
    created_at REAL
);

CREATE TABLE IF NOT EXISTS microseasons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    start_date TEXT,
    end_date TEXT,
    description TEXT,
    phase TEXT,
    trigger_signals TEXT,
    confidence REAL,
    user_named INTEGER DEFAULT 0,
    created_at REAL
);

CREATE TABLE IF NOT EXISTS signal_daily (
    date TEXT PRIMARY KEY,
    temp_7d_avg REAL,
    temp_7d_trend REAL,
    rain_7d_total REAL,
    day_length_change REAL,
    uv_7d_avg REAL,
    soil_temp_trend REAL,
    species_diversity_7d INTEGER,
    ndvi REAL,
    created_at REAL
);

CREATE INDEX IF NOT EXISTS idx_species_observed ON species_observations(observed_on);
CREATE INDEX IF NOT EXISTS idx_species_taxon ON species_observations(iconic_taxon);
CREATE INDEX IF NOT EXISTS idx_species_source ON species_observations(source);
CREATE INDEX IF NOT EXISTS idx_uv_timestamp ON uv_readings(timestamp);
"""


class Database:
    def __init__(self, db_path: str | Path | None = None):
        self.path = str(db_path or DB_PATH)
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.path)
            self._conn.row_factory = sqlite3.Row
            self._conn.executescript(SCHEMA)
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA busy_timeout=5000")
        return self._conn

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()

    # ── Weather ────────────────────────────────────────────

    def upsert_weather(self, date: str, **data):
        conn = self.connect()
        cols = ["date", "created_at"] + list(data.keys())
        vals = [date, time.time()] + list(data.values())
        placeholders = ",".join("?" for _ in cols)
        updates = ",".join(f"{c}=excluded.{c}" for c in data.keys())
        conn.execute(
            f"INSERT INTO daily_weather ({','.join(cols)}) VALUES ({placeholders}) "
            f"ON CONFLICT(date) DO UPDATE SET {updates}, created_at=excluded.created_at",
            vals,
        )
        conn.commit()

    # ── Astronomy ──────────────────────────────────────────

    def upsert_astronomy(self, date: str, **data):
        conn = self.connect()
        cols = ["date", "created_at"] + list(data.keys())
        vals = [date, time.time()] + list(data.values())
        placeholders = ",".join("?" for _ in cols)
        updates = ",".join(f"{c}=excluded.{c}" for c in data.keys())
        conn.execute(
            f"INSERT INTO astronomy ({','.join(cols)}) VALUES ({placeholders}) "
            f"ON CONFLICT(date) DO UPDATE SET {updates}, created_at=excluded.created_at",
            vals,
        )
        conn.commit()

    # ── Species ────────────────────────────────────────────

    def upsert_species(self, source: str, source_id: str, **data):
        conn = self.connect()
        cols = ["source", "source_id", "created_at"] + list(data.keys())
        vals = [source, source_id, time.time()] + list(data.values())
        placeholders = ",".join("?" for _ in cols)
        conn.execute(
            f"INSERT OR IGNORE INTO species_observations ({','.join(cols)}) VALUES ({placeholders})",
            vals,
        )
        conn.commit()

    def upsert_species_batch(self, records: list[dict]):
        conn = self.connect()
        now = time.time()
        for r in records:
            source = r.pop("source")
            source_id = r.pop("source_id")
            cols = ["source", "source_id", "created_at"] + list(r.keys())
            vals = [source, source_id, now] + list(r.values())
            placeholders = ",".join("?" for _ in cols)
            conn.execute(
                f"INSERT OR IGNORE INTO species_observations ({','.join(cols)}) VALUES ({placeholders})",
                vals,
            )
        conn.commit()

    # ── UV ─────────────────────────────────────────────────

    def insert_uv(self, timestamp: str, station: str, uv_index: float):
        conn = self.connect()
        conn.execute(
            "INSERT INTO uv_readings (timestamp, station, uv_index, created_at) VALUES (?,?,?,?)",
            (timestamp, station, uv_index, time.time()),
        )
        conn.commit()

    # ── Personal observations ──────────────────────────────

    def add_observation(self, date: str, note: str, tags: str | None = None, source: str = "user"):
        conn = self.connect()
        conn.execute(
            "INSERT INTO personal_observations (date, note, tags, source, created_at) VALUES (?,?,?,?,?)",
            (date, note, tags, source, time.time()),
        )
        conn.commit()

    # ── Microseasons ───────────────────────────────────────

    def upsert_microseason(self, name: str, start_date: str, end_date: str,
                           description: str, phase: str, trigger_signals: list,
                           confidence: float, user_named: bool = False):
        conn = self.connect()
        signals_json = json.dumps(trigger_signals)
        conn.execute(
            """INSERT INTO microseasons (name, start_date, end_date, description, phase,
               trigger_signals, confidence, user_named, created_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (name, start_date, end_date, description, phase, signals_json,
             confidence, int(user_named), time.time()),
        )
        conn.commit()

    # ── Signal daily ───────────────────────────────────────

    def upsert_signal(self, date: str, **data):
        conn = self.connect()
        cols = ["date", "created_at"] + list(data.keys())
        vals = [date, time.time()] + list(data.values())
        placeholders = ",".join("?" for _ in cols)
        updates = ",".join(f"{c}=excluded.{c}" for c in data.keys())
        conn.execute(
            f"INSERT INTO signal_daily ({','.join(cols)}) VALUES ({placeholders}) "
            f"ON CONFLICT(date) DO UPDATE SET {updates}, created_at=excluded.created_at",
            vals,
        )
        conn.commit()

    # ── Queries ────────────────────────────────────────────

    def get_weather_range(self, start: str, end: str) -> list[dict]:
        conn = self.connect()
        cur = conn.execute(
            "SELECT * FROM daily_weather WHERE date BETWEEN ? AND ? ORDER BY date", (start, end)
        )
        return [dict(r) for r in cur.fetchall()]

    def get_species_recent(self, days: int = 7) -> list[dict]:
        conn = self.connect()
        cur = conn.execute(
            "SELECT * FROM species_observations WHERE observed_on >= date('now', ? || ' days') ORDER BY observed_on DESC",
            (f"-{days}",),
        )
        return [dict(r) for r in cur.fetchall()]

    def get_species_by_taxon(self, taxon: str, days: int = 30) -> list[dict]:
        conn = self.connect()
        cur = conn.execute(
            "SELECT * FROM species_observations WHERE iconic_taxon=? AND observed_on >= date('now', ? || ' days')",
            (taxon, f"-{days}"),
        )
        return [dict(r) for r in cur.fetchall()]

    def count_species_diversity(self, days: int = 7) -> int:
        conn = self.connect()
        cur = conn.execute(
            "SELECT COUNT(DISTINCT taxon_name) FROM species_observations WHERE observed_on >= date('now', ? || ' days')",
            (f"-{days}",),
        )
        return cur.fetchone()[0]

    def row_counts(self) -> dict:
        conn = self.connect()
        tables = ["daily_weather", "astronomy", "species_observations", "uv_readings",
                   "air_quality", "personal_observations", "microseasons", "signal_daily"]
        counts = {}
        for t in tables:
            cur = conn.execute(f"SELECT COUNT(*) FROM {t}")
            counts[t] = cur.fetchone()[0]
        return counts
