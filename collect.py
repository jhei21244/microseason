#!/usr/bin/env python3
"""Microseason data collection CLI.

Usage:
    python collect.py daily          # run all daily collectors
    python collect.py backfill       # backfill all sources (12 months)
    python collect.py backfill --source weather   # backfill specific source
    python collect.py backfill --days 30          # custom backfill range
"""

import argparse
import sys
import time

from microseason.database import Database
from microseason.collectors.weather import WeatherCollector
from microseason.collectors.astronomy import AstronomyCollector
from microseason.collectors.uv import UVCollector
from microseason.collectors.nature import NatureCollector
from microseason.collectors.climatewatch import ClimateWatchCollector
from microseason.collectors.melbourne_water import MelbourneWaterCollector
from microseason.collectors.city_of_melbourne import CityOfMelbourneCollector


def run_daily(db: Database):
    """Run all daily collectors."""
    print("── Daily collection ──")
    errors = []

    collectors = [
        ("weather", lambda: WeatherCollector(db).collect_today()),
        ("astronomy", lambda: AstronomyCollector(db).collect_today()),
        ("uv", lambda: UVCollector(db).collect_now()),
        ("nature", lambda: NatureCollector(db).collect_recent(days=7)),
        ("melbourne_water", lambda: MelbourneWaterCollector(db).collect_recent()),
        ("city_of_melbourne", lambda: CityOfMelbourneCollector(db).collect_all()),
    ]

    for name, fn in collectors:
        try:
            fn()
        except Exception as e:
            print(f"  ERROR [{name}]: {e}")
            errors.append(name)

    counts = db.row_counts()
    print(f"\n── Database totals ──")
    for table, count in counts.items():
        print(f"  {table}: {count:,}")

    if errors:
        print(f"\n⚠ Errors in: {', '.join(errors)}")
    else:
        print(f"\n✓ All collectors succeeded")


def run_backfill(db: Database, source: str | None = None, days: int = 365):
    """Run backfill for one or all sources."""
    print(f"── Backfill ({days} days) ──")
    start = time.time()

    sources = {
        "weather": lambda: WeatherCollector(db).backfill(days),
        "astronomy": lambda: AstronomyCollector(db).backfill(days),
        "nature": lambda: NatureCollector(db).backfill(days),
        "climatewatch": lambda: ClimateWatchCollector(db).collect_all(),
    }

    if source:
        if source not in sources:
            print(f"Unknown source: {source}. Available: {', '.join(sources.keys())}")
            sys.exit(1)
        sources = {source: sources[source]}

    for name, fn in sources.items():
        print(f"\n── {name} ──")
        try:
            fn()
        except Exception as e:
            print(f"  ERROR [{name}]: {e}")

    elapsed = time.time() - start
    counts = db.row_counts()
    print(f"\n── Database totals ({elapsed:.0f}s) ──")
    for table, count in counts.items():
        if count > 0:
            print(f"  {table}: {count:,}")


def main():
    parser = argparse.ArgumentParser(description="Microseason data collection")
    parser.add_argument("command", choices=["daily", "backfill"])
    parser.add_argument("--source", type=str, help="Specific source to backfill")
    parser.add_argument("--days", type=int, default=365, help="Days to backfill (default: 365)")
    args = parser.parse_args()

    db = Database()
    try:
        if args.command == "daily":
            run_daily(db)
        elif args.command == "backfill":
            run_backfill(db, source=args.source, days=args.days)
    finally:
        db.close()


if __name__ == "__main__":
    main()
