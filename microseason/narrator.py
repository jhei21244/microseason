"""Narrative engine — LLM-generated ecological interpretation of signal data.

Generates a daily narrative that interprets what the data means for someone
living in Melbourne right now. Cached in the database, regenerated once per day.
"""

import json
import os
import time
from datetime import date, timedelta
from pathlib import Path

from .database import Database


# Load .env
_env_file = Path(__file__).parent.parent / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())


def generate_narrative(db: Database) -> dict | None:
    """Generate today's narrative from the current signal state.

    Returns dict with 'headline', 'body', 'forecast', 'generated_at'
    or None if generation fails.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    conn = db.connect()
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    week_ago = (date.today() - timedelta(days=7)).isoformat()

    # Gather all signal data
    weather = conn.execute(
        "SELECT * FROM daily_weather WHERE date IN (?, ?) ORDER BY date DESC LIMIT 1",
        (today, yesterday),
    ).fetchone()

    astro = conn.execute(
        "SELECT * FROM astronomy WHERE date IN (?, ?) ORDER BY date DESC LIMIT 1",
        (today, yesterday),
    ).fetchone()

    # 7-day weather trend
    week_weather = conn.execute(
        "SELECT date, mean_temp, precipitation, soil_temp_0cm, soil_moisture_0_1cm, evapotranspiration "
        "FROM daily_weather WHERE date >= ? ORDER BY date",
        (week_ago,),
    ).fetchall()

    # Recent transitions
    transitions = conn.execute(
        "SELECT name, phase, start_date, end_date, description FROM microseasons "
        "ORDER BY created_at DESC LIMIT 5"
    ).fetchall()

    # Species this week
    species_pulse = conn.execute(
        """SELECT iconic_taxon, COUNT(*) as count, COUNT(DISTINCT taxon_name) as species
           FROM species_observations WHERE observed_on >= ? GROUP BY iconic_taxon ORDER BY count DESC""",
        (week_ago,),
    ).fetchall()

    top_species = conn.execute(
        """SELECT common_name, iconic_taxon, COUNT(*) as count
           FROM species_observations WHERE observed_on >= ? AND common_name IS NOT NULL
           GROUP BY taxon_name ORDER BY count DESC LIMIT 8""",
        (week_ago,),
    ).fetchall()

    # Signal summary
    signal = conn.execute(
        "SELECT * FROM signal_daily ORDER BY date DESC LIMIT 1"
    ).fetchone()

    # Previous narrative (for continuity)
    prev = conn.execute(
        "SELECT headline, body FROM narratives ORDER BY date DESC LIMIT 1"
    ).fetchone()

    # Build the context
    w = dict(weather) if weather else {}
    a = dict(astro) if astro else {}
    sig = dict(signal) if signal else {}

    day_length_h = a.get("day_length_seconds", 0) // 3600
    day_length_m = (a.get("day_length_seconds", 0) % 3600) // 60

    context = f"""Today is {today} in Melbourne, Australia (-37.81, 144.96).

WEATHER TODAY:
- Temperature: {w.get('min_temp', '?')}° to {w.get('max_temp', '?')}°C (mean {w.get('mean_temp', '?')}°C)
- Rain: {w.get('precipitation', 0)}mm
- Cloud cover: {w.get('cloud_cover', '?')}%
- Humidity: {w.get('humidity', '?')}%
- Wind: {w.get('wind_speed', '?')} km/h
- UV index: {w.get('uv_index_max', '?')}
- Soil temperature: {w.get('soil_temp_0cm', '?')}°C
- Soil moisture: {w.get('soil_moisture_0_1cm', '?')} m³/m³
- Evapotranspiration: {w.get('evapotranspiration', '?')} mm

ASTRONOMY:
- Day length: {day_length_h}h {day_length_m}m
- Sunrise: {a.get('sunrise', '?')}
- Sunset: {a.get('sunset', '?')}

7-DAY SIGNALS:
- Temperature 7d average: {sig.get('temp_7d_avg', '?')}°C
- Temperature trend: {sig.get('temp_7d_trend', '?')}°C vs last week
- Rain 7d total: {sig.get('rain_7d_total', '?')}mm
- UV 7d average: {sig.get('uv_7d_avg', '?')}
- Day length change: {sig.get('day_length_change', '?')} seconds vs last week
- Species diversity: {sig.get('species_diversity_7d', '?')} unique species

SPECIES THIS WEEK:
{chr(10).join(f'- {r[0] or "?"}: {r[1]} observations, {r[2]} species' for r in species_pulse[:6])}

TOP OBSERVED SPECIES:
{chr(10).join(f'- {r[0]} ({r[1]}): {r[2]} observations' for r in top_species)}

RECENT TRANSITIONS DETECTED:
{chr(10).join(f'- {r[0]} ({r[1]}): {r[2]} to {r[3]}' for r in transitions[:5]) if transitions else 'None recent'}

MELBOURNE ECOLOGICAL CONTEXT:
- Melbourne's seasons are asymmetric: summer is dormant for ground flora, winter is the growing season
- The Wurundjeri seven-season framework recognises ~7 ecological phases, not 4
- Key autumn signals: eel migration (March), wombat visibility, rain moth emergence, fungi flush after first rains on warm soil, morning mists, liquidambar colour change
- Silver wattle (July) is the first herald of spring; jacaranda (November) signals summer's approach

PREVIOUS NARRATIVE:
{f'"{prev[0]}: {prev[1][:200]}"' if prev else 'None — this is the first narrative'}
"""

    prompt = f"""You are the voice of a hyperlocal ecological calendar for Melbourne, Australia. Your job is to interpret environmental data and tell someone what the land is doing RIGHT NOW — not what the numbers say, but what they MEAN for someone standing outside.

Write like a naturalist who lives here. Be specific. Be poetic but grounded. Reference actual species, actual phenomena. No generic weather-report language.

{context}

Respond with EXACTLY this JSON format, nothing else:
{{
  "headline": "3-6 word seasonal headline (e.g., 'Autumn arrived. The insects know.')",
  "body": "2-3 sentences interpreting what the data means. What should someone notice if they stepped outside right now? What's the landscape doing? Reference specific signals — don't just restate numbers.",
  "forecast": "1 sentence about what's coming next based on the trends."
}}"""

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text.strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            import re
            text = re.sub(r"^```\w*\n?", "", text)
            text = re.sub(r"\n?```$", "", text)

        result = json.loads(text)
        result["generated_at"] = time.time()
        result["date"] = today

        # Store in database
        _store_narrative(db, today, result)

        return result
    except Exception as e:
        print(f"  narrator error: {e}")
        return None


def get_todays_narrative(db: Database) -> dict | None:
    """Get today's narrative, generating if needed."""
    conn = db.connect()

    # Ensure narratives table exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS narratives (
            date TEXT PRIMARY KEY,
            headline TEXT,
            body TEXT,
            forecast TEXT,
            generated_at REAL
        )
    """)
    conn.commit()

    today = date.today().isoformat()
    row = conn.execute("SELECT * FROM narratives WHERE date = ?", (today,)).fetchone()

    if row:
        return {
            "date": row[0],
            "headline": row[1],
            "body": row[2],
            "forecast": row[3],
            "generated_at": row[4],
        }

    # Generate new narrative
    return generate_narrative(db)


def _store_narrative(db: Database, dt: str, narrative: dict):
    conn = db.connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS narratives (
            date TEXT PRIMARY KEY,
            headline TEXT,
            body TEXT,
            forecast TEXT,
            generated_at REAL
        )
    """)
    conn.execute(
        "INSERT OR REPLACE INTO narratives (date, headline, body, forecast, generated_at) VALUES (?,?,?,?,?)",
        (dt, narrative["headline"], narrative["body"], narrative["forecast"], narrative.get("generated_at", time.time())),
    )
    conn.commit()
