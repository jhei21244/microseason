"""FastAPI server — REST API + dashboard."""

import json
from datetime import date, timedelta
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .database import Database
from .detector import TransitionDetector

STATIC_DIR = Path(__file__).parent / "static"


class ObservationRequest(BaseModel):
    date: str
    note: str
    tags: str | None = None


def create_app(db_path: str | None = None) -> FastAPI:
    app = FastAPI(title="Microseason", version="0.1.0")

    db = Database(db_path)
    detector = TransitionDetector(db)

    @app.on_event("startup")
    async def startup():
        db.connect()

    @app.on_event("shutdown")
    async def shutdown():
        db.close()

    # ── Dashboard ──────────────────────────────────────────

    @app.get("/")
    async def dashboard():
        html_path = STATIC_DIR / "index.html"
        if html_path.exists():
            return HTMLResponse(html_path.read_text())
        return HTMLResponse("<h1>Microseason</h1><p>Frontend not built yet.</p>")

    # ── Current state ──────────────────────────────────────

    @app.get("/api/now")
    async def current_state():
        """Current conditions, active microseason, signal summary."""
        conn = db.connect()
        today = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()

        # Today's weather (or yesterday if today not collected yet)
        weather = conn.execute(
            "SELECT * FROM daily_weather WHERE date IN (?, ?) ORDER BY date DESC LIMIT 1",
            (today, yesterday),
        ).fetchone()

        # Today's astronomy
        astro = conn.execute(
            "SELECT * FROM astronomy WHERE date IN (?, ?) ORDER BY date DESC LIMIT 1",
            (today, yesterday),
        ).fetchone()

        # Latest UV
        uv = conn.execute(
            "SELECT * FROM uv_readings ORDER BY timestamp DESC LIMIT 1"
        ).fetchone()

        # Compute daily signals
        signals = detector.compute_daily_signals()

        # Active microseasons
        seasons = conn.execute(
            "SELECT * FROM microseasons WHERE start_date <= ? AND end_date >= ? ORDER BY created_at DESC",
            (today, today),
        ).fetchall()

        # Recent species activity (last 7 days by taxon)
        species_pulse = conn.execute(
            """SELECT iconic_taxon, COUNT(*) as count, COUNT(DISTINCT taxon_name) as species
               FROM species_observations
               WHERE observed_on >= date('now', '-7 days')
               GROUP BY iconic_taxon ORDER BY count DESC""",
        ).fetchall()

        # Phenological markers — species typically active this month from ClimateWatch
        current_month = date.today().month
        month_str = f"{current_month:02d}"
        phenology_markers = conn.execute(
            """SELECT common_name, taxon_name, iconic_taxon, COUNT(*) as obs_count,
                      MIN(observed_on) as earliest, MAX(observed_on) as latest
               FROM species_observations
               WHERE source = 'gbif' AND common_name IS NOT NULL
                     AND substr(observed_on, 6, 2) = ?
               GROUP BY taxon_name
               ORDER BY obs_count DESC LIMIT 12""",
            (month_str,),
        ).fetchall()

        # Top species this week (most observed)
        top_species = conn.execute(
            """SELECT common_name, taxon_name, iconic_taxon, COUNT(*) as count
               FROM species_observations
               WHERE observed_on >= date('now', '-7 days') AND common_name IS NOT NULL
               GROUP BY taxon_name ORDER BY count DESC LIMIT 10"""
        ).fetchall()

        return {
            "date": today,
            "weather": dict(weather) if weather else None,
            "astronomy": dict(astro) if astro else None,
            "uv": dict(uv) if uv else None,
            "signals": signals,
            "active_microseasons": [dict(s) for s in seasons],
            "species_pulse": [{"taxon": r[0], "observations": r[1], "species": r[2]} for r in species_pulse],
            "phenology_markers": [{"name": r[0], "taxon": r[1], "iconic_taxon": r[2], "count": r[3]} for r in phenology_markers],
            "top_species": [{"name": r[0], "taxon": r[1], "iconic_taxon": r[2], "count": r[3]} for r in top_species],
        }

    # ── Weather ────────────────────────────────────────────

    @app.get("/api/weather")
    async def weather_range(
        start: str = Query(default=None),
        end: str = Query(default=None),
        days: int = Query(default=30),
    ):
        if not start:
            start = (date.today() - timedelta(days=days)).isoformat()
        if not end:
            end = date.today().isoformat()
        return db.get_weather_range(start, end)

    # ── Species ────────────────────────────────────────────

    @app.get("/api/species/recent")
    async def species_recent(days: int = 7):
        return db.get_species_recent(days)

    @app.get("/api/species/pulse")
    async def species_pulse(days: int = 7):
        """Species activity grouped by taxon."""
        conn = db.connect()
        rows = conn.execute(
            """SELECT iconic_taxon, COUNT(*) as count,
                      COUNT(DISTINCT taxon_name) as unique_species,
                      GROUP_CONCAT(DISTINCT common_name) as examples
               FROM species_observations
               WHERE observed_on >= date('now', ? || ' days')
               GROUP BY iconic_taxon ORDER BY count DESC""",
            (f"-{days}",),
        ).fetchall()
        return [{"taxon": r[0], "observations": r[1], "unique_species": r[2],
                 "examples": r[3][:200] if r[3] else None} for r in rows]

    @app.get("/api/species/top")
    async def species_top(days: int = 7, limit: int = 20):
        """Most observed species in the last N days."""
        conn = db.connect()
        rows = conn.execute(
            """SELECT common_name, taxon_name, iconic_taxon, COUNT(*) as count
               FROM species_observations
               WHERE observed_on >= date('now', ? || ' days') AND common_name IS NOT NULL
               GROUP BY taxon_name ORDER BY count DESC LIMIT ?""",
            (f"-{days}", limit),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Microseasons ───────────────────────────────────────

    @app.get("/api/microseasons")
    async def list_microseasons():
        conn = db.connect()
        rows = conn.execute(
            "SELECT * FROM microseasons ORDER BY start_date DESC"
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            if d.get("trigger_signals"):
                try:
                    d["trigger_signals"] = json.loads(d["trigger_signals"])
                except (json.JSONDecodeError, TypeError):
                    pass
            result.append(d)
        return result

    @app.get("/api/microseasons/detect")
    async def detect_transitions(lookback: int = 90):
        """Run transition detection and return results."""
        transitions = detector.run_and_store(lookback)
        return transitions

    # ── ClimateWatch phenology ──────────────────────────────

    @app.get("/api/phenology/recent")
    async def phenology_recent(months: int = 3):
        """Recent ClimateWatch phenological observations near Melbourne."""
        conn = db.connect()
        rows = conn.execute(
            """SELECT common_name, taxon_name, iconic_taxon, observed_on, observer
               FROM species_observations
               WHERE source = 'gbif' AND observed_on IS NOT NULL
               ORDER BY observed_on DESC LIMIT 50"""
        ).fetchall()
        return [dict(r) for r in rows]

    @app.get("/api/phenology/calendar")
    async def phenology_calendar():
        """Species first-observation dates by month — the phenological calendar."""
        conn = db.connect()
        rows = conn.execute(
            """SELECT common_name, taxon_name, iconic_taxon,
                      MIN(observed_on) as first_seen,
                      MAX(observed_on) as last_seen,
                      COUNT(*) as total_obs
               FROM species_observations
               WHERE common_name IS NOT NULL AND observed_on IS NOT NULL
               GROUP BY taxon_name
               HAVING total_obs >= 3
               ORDER BY first_seen"""
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Signal field ───────────────────────────────────────

    @app.get("/api/signals")
    async def signal_history(days: int = 30):
        conn = db.connect()
        start = (date.today() - timedelta(days=days)).isoformat()
        rows = conn.execute(
            "SELECT * FROM signal_daily WHERE date >= ? ORDER BY date", (start,)
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Observations ───────────────────────────────────────

    @app.get("/api/observations")
    async def list_observations():
        conn = db.connect()
        rows = conn.execute(
            "SELECT * FROM personal_observations ORDER BY date DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    @app.post("/api/observations")
    async def add_observation(req: ObservationRequest):
        db.add_observation(req.date, req.note, req.tags)
        return {"status": "ok", "date": req.date}

    # ── Core sample data ───────────────────────────────────

    @app.get("/api/core-sample")
    async def core_sample_data():
        """Data for the core sample ring visualization."""
        conn = db.connect()

        # All weather data for the ring
        weather = conn.execute(
            "SELECT date, mean_temp, precipitation, uv_index_max, soil_temp_0cm FROM daily_weather ORDER BY date"
        ).fetchall()

        # All microseasons
        seasons = conn.execute(
            "SELECT * FROM microseasons ORDER BY start_date"
        ).fetchall()

        # Personal observations
        observations = conn.execute(
            "SELECT date, note FROM personal_observations ORDER BY date"
        ).fetchall()

        # Astronomy for day length curve
        astro = conn.execute(
            "SELECT date, day_length_seconds FROM astronomy ORDER BY date"
        ).fetchall()

        return {
            "weather": [dict(r) for r in weather],
            "microseasons": [dict(r) for r in seasons],
            "observations": [dict(r) for r in observations],
            "day_length": [dict(r) for r in astro],
        }

    # ── Year-over-Year comparison ────────────────────────────

    @app.get("/api/yoy/temperature")
    async def yoy_temperature():
        """Monthly temperature averages for YoY comparison."""
        conn = db.connect()
        rows = conn.execute(
            """SELECT substr(date,1,7) as month,
                      AVG(mean_temp) as avg_temp,
                      MIN(min_temp) as coldest,
                      MAX(max_temp) as hottest,
                      SUM(precipitation) as total_rain,
                      COUNT(*) as days
               FROM daily_weather
               GROUP BY month ORDER BY month"""
        ).fetchall()
        return [dict(r) for r in rows]

    @app.get("/api/yoy/species")
    async def yoy_species():
        """Monthly species diversity for YoY comparison."""
        conn = db.connect()
        rows = conn.execute(
            """SELECT substr(observed_on,1,7) as month,
                      COUNT(*) as total_obs,
                      COUNT(DISTINCT taxon_name) as unique_species,
                      COUNT(DISTINCT CASE WHEN iconic_taxon='Aves' THEN taxon_name END) as bird_species,
                      COUNT(DISTINCT CASE WHEN iconic_taxon='Plantae' THEN taxon_name END) as plant_species,
                      COUNT(DISTINCT CASE WHEN iconic_taxon='Insecta' THEN taxon_name END) as insect_species,
                      COUNT(DISTINCT CASE WHEN iconic_taxon='Fungi' THEN taxon_name END) as fungi_species
               FROM species_observations
               WHERE observed_on IS NOT NULL
               GROUP BY month ORDER BY month"""
        ).fetchall()
        return [dict(r) for r in rows]

    @app.get("/api/yoy/transitions")
    async def yoy_transitions():
        """All detected transitions with timing data."""
        conn = db.connect()
        rows = conn.execute(
            """SELECT name, start_date, end_date, phase, confidence, trigger_signals,
                      julianday(end_date) - julianday(start_date) as duration_days
               FROM microseasons ORDER BY start_date"""
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            if d.get("trigger_signals"):
                try:
                    d["trigger_signals"] = json.loads(d["trigger_signals"])
                except (json.JSONDecodeError, TypeError):
                    pass
            result.append(d)
        return result

    @app.get("/api/yoy/day-length")
    async def yoy_day_length():
        """Day length curve across the year."""
        conn = db.connect()
        rows = conn.execute(
            "SELECT date, day_length_seconds FROM astronomy ORDER BY date"
        ).fetchall()
        return [{"date": r[0], "minutes": round(r[1] / 60, 1) if r[1] else None} for r in rows]

    # ── Stats ──────────────────────────────────────────────

    @app.get("/api/stats")
    async def database_stats():
        counts = db.row_counts()
        conn = db.connect()

        # Date ranges
        weather_range = conn.execute(
            "SELECT MIN(date), MAX(date) FROM daily_weather"
        ).fetchone()
        species_range = conn.execute(
            "SELECT MIN(observed_on), MAX(observed_on) FROM species_observations"
        ).fetchone()

        return {
            "row_counts": counts,
            "weather_range": {"start": weather_range[0], "end": weather_range[1]} if weather_range[0] else None,
            "species_range": {"start": species_range[0], "end": species_range[1]} if species_range[0] else None,
        }

    return app
