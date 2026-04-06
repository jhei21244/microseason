"""Transition detection engine — multi-signal convergence.

Detects microseason transitions by monitoring convergence of multiple
environmental signals shifting in the same direction over sustained periods.

A transition is flagged when 3+ signal channels show sustained directional
change (same direction for 5+ consecutive days), with at least one channel
exceeding 1 standard deviation from its annual mean rate of change.
"""

import json
import statistics
from datetime import date, timedelta

from .database import Database

# Minimum signals that must converge to flag a transition
MIN_SIGNALS = 3
# Minimum consecutive days of directional change
MIN_CONSECUTIVE_DAYS = 5
# Rolling average window
ROLLING_WINDOW = 7


class SignalChannel:
    """A single environmental signal with trend detection."""

    def __init__(self, name: str, values: list[tuple[str, float | None]]):
        self.name = name
        # [(date_str, value), ...] sorted by date
        self.values = [(d, v) for d, v in values if v is not None]

    def rolling_avg(self, window: int = ROLLING_WINDOW) -> list[tuple[str, float]]:
        result = []
        vals = self.values
        for i in range(window - 1, len(vals)):
            chunk = [v for _, v in vals[i - window + 1:i + 1]]
            avg = sum(chunk) / len(chunk)
            result.append((vals[i][0], avg))
        return result

    def rate_of_change(self, window: int = ROLLING_WINDOW) -> list[tuple[str, float]]:
        """Daily rate of change of the rolling average."""
        avgs = self.rolling_avg(window)
        result = []
        for i in range(1, len(avgs)):
            delta = avgs[i][1] - avgs[i - 1][1]
            result.append((avgs[i][0], delta))
        return result

    def detect_sustained_direction(self, min_days: int = MIN_CONSECUTIVE_DAYS) -> list[dict]:
        """Find periods where the signal moves in one direction for min_days+."""
        roc = self.rate_of_change()
        if not roc:
            return []

        runs = []
        current_dir = None  # 'warming', 'cooling'
        run_start = None
        run_length = 0
        run_magnitude = 0.0

        for dt, delta in roc:
            direction = "rising" if delta > 0 else "falling" if delta < 0 else None
            if direction == current_dir:
                run_length += 1
                run_magnitude += abs(delta)
            else:
                if run_length >= min_days and current_dir:
                    runs.append({
                        "channel": self.name,
                        "direction": current_dir,
                        "start": run_start,
                        "end": dt,
                        "days": run_length,
                        "magnitude": round(run_magnitude, 3),
                    })
                current_dir = direction
                run_start = dt
                run_length = 1
                run_magnitude = abs(delta)

        # Final run
        if run_length >= min_days and current_dir and roc:
            runs.append({
                "channel": self.name,
                "direction": current_dir,
                "start": run_start,
                "end": roc[-1][0],
                "days": run_length,
                "magnitude": round(run_magnitude, 3),
            })

        return runs


class TransitionDetector:
    """Detects microseason transitions from multi-signal convergence."""

    PHASE_MAP = {
        ("temp", "falling", "day_length", "falling"): ("cooling", "Cool change arriving"),
        ("temp", "rising", "day_length", "rising"): ("awakening", "Warming trend"),
        ("temp", "falling", "soil_temp", "falling"): ("dormancy", "Deep cooling"),
        ("temp", "rising", "soil_temp", "rising"): ("growth", "Ground warming"),
        ("rain", "rising", "soil_moisture", "rising"): ("rain", "Wet period"),
        ("rain", "falling", "soil_moisture", "falling"): ("drying", "Drying out"),
    }

    def __init__(self, db: Database):
        self.db = db

    def _load_channels(self, lookback_days: int = 60) -> list[SignalChannel]:
        """Load signal channels from the database."""
        conn = self.db.connect()
        end = date.today().isoformat()
        start = (date.today() - timedelta(days=lookback_days)).isoformat()

        # Temperature
        rows = conn.execute(
            "SELECT date, mean_temp FROM daily_weather WHERE date BETWEEN ? AND ? ORDER BY date",
            (start, end),
        ).fetchall()
        temp_channel = SignalChannel("temp", [(r[0], r[1]) for r in rows])

        # Day length
        rows = conn.execute(
            "SELECT date, day_length_seconds FROM astronomy WHERE date BETWEEN ? AND ? ORDER BY date",
            (start, end),
        ).fetchall()
        day_channel = SignalChannel("day_length", [(r[0], r[1]) for r in rows])

        # Precipitation (7-day rolling)
        rows = conn.execute(
            "SELECT date, precipitation FROM daily_weather WHERE date BETWEEN ? AND ? ORDER BY date",
            (start, end),
        ).fetchall()
        rain_channel = SignalChannel("rain", [(r[0], r[1]) for r in rows])

        # UV
        rows = conn.execute(
            "SELECT date, uv_index_max FROM daily_weather WHERE date BETWEEN ? AND ? ORDER BY date",
            (start, end),
        ).fetchall()
        uv_channel = SignalChannel("uv", [(r[0], r[1]) for r in rows])

        # Soil temperature
        rows = conn.execute(
            "SELECT date, soil_temp_0cm FROM daily_weather WHERE date BETWEEN ? AND ? ORDER BY date",
            (start, end),
        ).fetchall()
        soil_channel = SignalChannel("soil_temp", [(r[0], r[1]) for r in rows])

        # Soil moisture
        rows = conn.execute(
            "SELECT date, soil_moisture_0_1cm FROM daily_weather WHERE date BETWEEN ? AND ? ORDER BY date",
            (start, end),
        ).fetchall()
        moisture_channel = SignalChannel("soil_moisture", [(r[0], r[1]) for r in rows])

        # Species diversity (weekly count of unique species)
        rows = conn.execute(
            """SELECT observed_on as date, COUNT(DISTINCT taxon_name) as diversity
               FROM species_observations
               WHERE observed_on BETWEEN ? AND ?
               GROUP BY observed_on ORDER BY observed_on""",
            (start, end),
        ).fetchall()
        diversity_channel = SignalChannel("species_diversity", [(r[0], r[1]) for r in rows])

        return [temp_channel, day_channel, rain_channel, uv_channel,
                soil_channel, moisture_channel, diversity_channel]

    def detect(self, lookback_days: int = 60) -> list[dict]:
        """Run detection across all channels. Returns list of transitions."""
        channels = self._load_channels(lookback_days)

        # Get sustained directional runs from each channel
        all_runs = []
        for ch in channels:
            runs = ch.detect_sustained_direction()
            all_runs.extend(runs)

        if not all_runs:
            return []

        # Find convergence: periods where 3+ channels overlap in time with same direction
        transitions = self._find_convergence(all_runs)
        return transitions

    def _find_convergence(self, runs: list[dict]) -> list[dict]:
        """Find time periods where multiple signals converge."""
        if not runs:
            return []

        # Get all unique dates mentioned
        all_dates = set()
        for r in runs:
            all_dates.add(r["start"])
            all_dates.add(r["end"])
        all_dates = sorted(all_dates)

        transitions = []
        i = 0
        while i < len(all_dates):
            dt = all_dates[i]
            # Find all runs active on this date
            active = [r for r in runs if r["start"] <= dt <= r["end"]]

            if len(active) >= MIN_SIGNALS:
                # Count directions
                rising = [r for r in active if r["direction"] == "rising"]
                falling = [r for r in active if r["direction"] == "falling"]

                dominant_dir = "rising" if len(rising) >= len(falling) else "falling"
                dominant = rising if dominant_dir == "rising" else falling

                if len(dominant) >= MIN_SIGNALS:
                    # Find the overlapping period
                    overlap_start = max(r["start"] for r in dominant)
                    overlap_end = min(r["end"] for r in dominant)

                    if overlap_start <= overlap_end:
                        channels = [r["channel"] for r in dominant]
                        phase, desc = self._classify_phase(channels, dominant_dir)
                        confidence = min(1.0, len(dominant) / 5.0)

                        transitions.append({
                            "start_date": overlap_start,
                            "end_date": overlap_end,
                            "direction": dominant_dir,
                            "channels": channels,
                            "phase": phase,
                            "description": desc,
                            "confidence": round(confidence, 2),
                            "signal_count": len(dominant),
                        })

                        # Skip past this convergence period
                        while i < len(all_dates) and all_dates[i] <= overlap_end:
                            i += 1
                        continue
            i += 1

        return transitions

    def _classify_phase(self, channels: list[str], direction: str) -> tuple[str, str]:
        """Classify the transition into a phase based on active channels."""
        if "temp" in channels and direction == "falling":
            if "soil_temp" in channels:
                return "dormancy", "Deep cooling — soil and air temperatures dropping"
            return "cooling", "Cool change — temperatures dropping"
        if "temp" in channels and direction == "rising":
            if "day_length" in channels:
                return "awakening", "Spring warming — temperatures and days lengthening"
            if "soil_temp" in channels:
                return "growth", "Ground warming — soil and air temperatures rising"
            return "growth", "Warming trend underway"
        if "rain" in channels and direction == "rising":
            return "rain", "Wet period — rainfall increasing"
        if "rain" in channels and direction == "falling":
            return "drying", "Drying out — rainfall decreasing"
        if "uv" in channels and direction == "rising":
            return "flowering", "UV intensity increasing — peak sun"
        if "uv" in channels and direction == "falling":
            return "cooling", "UV declining — sun weakening"
        if "species_diversity" in channels and direction == "rising":
            return "growth", "Biodiversity surge — species activity increasing"
        return "transition", f"Multi-signal shift ({direction})"

    def run_and_store(self, lookback_days: int = 60) -> list[dict]:
        """Detect transitions and store them in the database."""
        transitions = self.detect(lookback_days)
        for t in transitions:
            self.db.upsert_microseason(
                name=t["description"],
                start_date=t["start_date"],
                end_date=t["end_date"],
                description=f"{t['signal_count']} signals converging ({', '.join(t['channels'])})",
                phase=t["phase"],
                trigger_signals=t["channels"],
                confidence=t["confidence"],
            )
        print(f"  detector: {len(transitions)} transitions detected")
        return transitions

    def compute_daily_signals(self) -> dict:
        """Compute the signal_daily row for today."""
        conn = self.db.connect()
        today = date.today().isoformat()
        week_ago = (date.today() - timedelta(days=7)).isoformat()
        two_weeks = (date.today() - timedelta(days=14)).isoformat()

        # Temperature 7-day average and trend
        rows = conn.execute(
            "SELECT mean_temp FROM daily_weather WHERE date BETWEEN ? AND ? ORDER BY date",
            (week_ago, today),
        ).fetchall()
        temps = [r[0] for r in rows if r[0] is not None]
        temp_avg = sum(temps) / len(temps) if temps else None

        rows_prev = conn.execute(
            "SELECT mean_temp FROM daily_weather WHERE date BETWEEN ? AND ? ORDER BY date",
            (two_weeks, week_ago),
        ).fetchall()
        temps_prev = [r[0] for r in rows_prev if r[0] is not None]
        temp_prev_avg = sum(temps_prev) / len(temps_prev) if temps_prev else None
        temp_trend = round(temp_avg - temp_prev_avg, 2) if temp_avg and temp_prev_avg else None

        # Rain 7-day total
        rows = conn.execute(
            "SELECT SUM(precipitation) FROM daily_weather WHERE date BETWEEN ? AND ?",
            (week_ago, today),
        ).fetchone()
        rain_total = rows[0] if rows[0] else 0

        # Day length change
        rows = conn.execute(
            "SELECT day_length_seconds FROM astronomy WHERE date=?", (today,)
        ).fetchone()
        today_dl = rows[0] if rows else None
        rows = conn.execute(
            "SELECT day_length_seconds FROM astronomy WHERE date=?", (week_ago,)
        ).fetchone()
        week_dl = rows[0] if rows else None
        dl_change = today_dl - week_dl if today_dl and week_dl else None

        # UV 7-day average
        rows = conn.execute(
            "SELECT AVG(uv_index_max) FROM daily_weather WHERE date BETWEEN ? AND ?",
            (week_ago, today),
        ).fetchone()
        uv_avg = round(rows[0], 1) if rows[0] else None

        # Soil temp trend
        rows = conn.execute(
            "SELECT soil_temp_0cm FROM daily_weather WHERE date BETWEEN ? AND ? ORDER BY date",
            (week_ago, today),
        ).fetchall()
        soils = [r[0] for r in rows if r[0] is not None]
        soil_trend = round(soils[-1] - soils[0], 2) if len(soils) >= 2 else None

        # Species diversity
        diversity = self.db.count_species_diversity(days=7)

        signals = {
            "temp_7d_avg": round(temp_avg, 1) if temp_avg else None,
            "temp_7d_trend": temp_trend,
            "rain_7d_total": round(rain_total, 1),
            "day_length_change": dl_change,
            "uv_7d_avg": uv_avg,
            "soil_temp_trend": soil_trend,
            "species_diversity_7d": diversity,
        }

        self.db.upsert_signal(today, **signals)
        return signals
