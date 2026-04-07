"""Auto-generated observations from existing data.

These are computationally derived but phenomenologically real observations
that fill the observation log and teach the user what to notice.
"""

from datetime import date, timedelta
from .database import Database


def generate_observations(db: Database) -> list[dict]:
    """Scan the database for noteworthy events and generate observations."""
    conn = db.connect()
    observations = []

    # Day length milestones
    rows = conn.execute(
        """SELECT date, day_length_seconds FROM astronomy ORDER BY date"""
    ).fetchall()

    prev_dl = None
    for r in rows:
        dl = r[1]
        if dl is None:
            continue
        dl_min = dl / 60

        # Day length crossing notable thresholds
        if prev_dl is not None:
            prev_min = prev_dl / 60
            for threshold in [600, 630, 660, 690, 720, 750, 780, 810]:
                h = threshold // 60
                m = threshold % 60
                if (prev_min < threshold <= dl_min) or (prev_min > threshold >= dl_min):
                    direction = "rose above" if dl_min >= threshold else "dropped below"
                    observations.append({
                        "date": r[0],
                        "note": f"Day length {direction} {h}h{m:02d}m for the first time since the opposite crossing.",
                        "tags": "atmosphere",
                        "source": "auto",
                    })

            # Equinox detection (day length ~720 min = 12h)
            if abs(dl_min - 720) < 3 and abs(prev_min - 720) >= 3:
                observations.append({
                    "date": r[0],
                    "note": f"Near-equinox: day and night almost equal at {dl_min:.0f} minutes of daylight.",
                    "tags": "atmosphere",
                    "source": "auto",
                })

            # Shortest/longest day detection
            if dl_min == min(x[1] / 60 for x in rows if x[1]):
                observations.append({
                    "date": r[0],
                    "note": f"Winter solstice window — shortest day of the year at {dl_min:.0f} minutes.",
                    "tags": "atmosphere",
                    "source": "auto",
                })
            if dl_min == max(x[1] / 60 for x in rows if x[1]):
                observations.append({
                    "date": r[0],
                    "note": f"Summer solstice window — longest day of the year at {dl_min:.0f} minutes.",
                    "tags": "atmosphere",
                    "source": "auto",
                })

        prev_dl = dl

    # Temperature milestones
    rows = conn.execute(
        """SELECT date, max_temp, min_temp, mean_temp FROM daily_weather ORDER BY date"""
    ).fetchall()

    for i, r in enumerate(rows):
        if r[1] is None:
            continue

        # First frost (min_temp < 2)
        if r[2] is not None and r[2] < 2:
            if i == 0 or rows[i-1][2] is None or rows[i-1][2] >= 2:
                observations.append({
                    "date": r[0],
                    "note": f"First frost territory — minimum temperature hit {r[2]:.1f}°C.",
                    "tags": "atmosphere",
                    "source": "auto",
                })

        # First 30+ day
        if r[1] >= 30:
            if i == 0 or rows[i-1][1] is None or rows[i-1][1] < 30:
                observations.append({
                    "date": r[0],
                    "note": f"First 30°+ day — maximum hit {r[1]:.1f}°C.",
                    "tags": "atmosphere",
                    "source": "auto",
                })

        # First sub-10 max
        if r[1] < 10:
            if i == 0 or rows[i-1][1] is None or rows[i-1][1] >= 10:
                observations.append({
                    "date": r[0],
                    "note": f"Deep cold — daytime maximum only reached {r[1]:.1f}°C.",
                    "tags": "atmosphere",
                    "source": "auto",
                })

    # Species diversity peaks
    rows = conn.execute(
        """SELECT observed_on, COUNT(DISTINCT taxon_name) as diversity
           FROM species_observations
           WHERE observed_on IS NOT NULL
           GROUP BY observed_on
           ORDER BY diversity DESC LIMIT 10"""
    ).fetchall()

    for r in rows[:3]:
        observations.append({
            "date": r[0],
            "note": f"Species diversity peaked at {r[1]} unique species observed — a high point for the record.",
            "tags": "general",
            "source": "auto",
        })

    # First observation of notable taxa each season
    notable = conn.execute(
        """SELECT common_name, MIN(observed_on) as first_seen, iconic_taxon
           FROM species_observations
           WHERE common_name IS NOT NULL AND observed_on IS NOT NULL
                 AND common_name IN ('Silver Wattle', 'Golden Wattle', 'Jacaranda',
                     'Rainbow Lorikeet', 'Australian Magpie', 'Tawny Frogmouth',
                     'Common Brown Butterfly', 'Rain Moth', 'Laughing Kookaburra',
                     'Pied Currawong', 'Superb Fairywren')
           GROUP BY common_name"""
    ).fetchall()

    for r in notable:
        observations.append({
            "date": r[1],
            "note": f"First {r[0]} observation in the record — a phenological marker for this location.",
            "tags": "general",
            "source": "auto",
        })

    # Rainfall events > 15mm
    rows = conn.execute(
        """SELECT date, precipitation FROM daily_weather
           WHERE precipitation > 15 ORDER BY precipitation DESC LIMIT 5"""
    ).fetchall()

    for r in rows:
        observations.append({
            "date": r[0],
            "note": f"Significant rainfall: {r[1]:.1f}mm recorded. Watch for fungi emergence in coming days.",
            "tags": "water",
            "source": "auto",
        })

    # Sort by date
    observations.sort(key=lambda x: x["date"])

    return observations


def seed_auto_observations(db: Database) -> int:
    """Generate and store auto observations if the log is empty."""
    conn = db.connect()
    existing = conn.execute("SELECT COUNT(*) FROM personal_observations").fetchone()[0]
    if existing > 0:
        return 0  # Don't overwrite user observations

    observations = generate_observations(db)

    for obs in observations:
        db.add_observation(obs["date"], obs["note"], obs["tags"])

    return len(observations)
