"""Predict a fitness-room count at the current or a future local timestamp.

Run from backend/:
    python predict_fitness_count.py --csv penndata/muchdatastuff/data.csv
    python predict_fitness_count.py --from-db --room-id 3 --at 2026-10-15T18:00
    python predict_fitness_count.py --csv data.csv --room-id 3 --artifact-dir /path/to/artifacts
"""

import argparse
import os
import sys

import pandas as pd

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pennmobile.settings.development")

import django 

django.setup()

from penndata.ml.constants import TIMEZONE 
from penndata.ml.features import infer_people_capacity, is_open_at 
from penndata.ml.predict import (
    _feature_row,
    _predict_count,
    choose_horizon,
    load_artifact,
)
from penndata.ml.train import snapshots_from_csv, snapshots_from_db


def parse_local_timestamp(value: str | None, default: pd.Timestamp) -> pd.Timestamp:
    if value is None:
        return default

    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is not None:
        return timestamp.tz_convert(TIMEZONE).tz_localize(None)
    return timestamp


def predict_room(
    snapshots: pd.DataFrame,
    room_id: int,
    target: pd.Timestamp,
    origin: pd.Timestamp,
    artifact_dir: str | None,
) -> dict | None:
    history = snapshots[
        (snapshots["room_id"] == room_id)
        & (snapshots["ts_local"] <= origin)
    ].copy()
    if history.empty:
        return None

    capacities = infer_people_capacity(history)
    history["room_capacity"] = history["room_id"].map(capacities)
    history["occ_rate"] = history["count"] / history["room_capacity"]
    capacity = float(capacities[room_id])

    if not is_open_at(target):
        count, method = 0.0, "closed"
    else:
        horizon = choose_horizon(origin, target)
        row = _feature_row(history, room_id, target)
        artifact = load_artifact(horizon, artifact_dir)
        count, method = _predict_count(row, history, horizon, artifact)
        count = min(count, capacity)

    latest = history["ts_local"].max()
    return {
        "room_id": room_id,
        "target": target,
        "count": round(float(count), 1),
        "occupancy_pct": round(float(count / capacity * 100), 1),
        "capacity": round(capacity, 1),
        "method": method,
        "snapshots_used": len(history),
        "latest_snapshot": latest,
        "snapshot_age_hours": (origin - latest).total_seconds() / 3600,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--csv", help="Snapshot CSV with date,count,room_id,capacity columns.")
    source.add_argument("--from-db", action="store_true", help="Read FitnessSnapshot rows from Django.")
    parser.add_argument("--room-id", type=int, help="Predict one room; default is all rooms with history.")
    parser.add_argument(
        "--at",
        "--target",
        dest="target",
        help="Target local date/time or ISO timestamp; default is now.",
    )
    parser.add_argument("--artifact-dir", help="Directory containing model_24h.joblib and model_7d.joblib.")
    args = parser.parse_args()

    origin = pd.Timestamp.now(tz=TIMEZONE).tz_localize(None)
    try:
        target = parse_local_timestamp(args.target, origin)
    except (TypeError, ValueError) as exc:
        parser.error(f"Invalid --at timestamp: {exc}")
    if target < origin:
        parser.error("--at must be now or in the future; use walk-forward evaluation for historical backtests.")

    snapshots = snapshots_from_csv(args.csv) if args.csv else snapshots_from_db()
    room_ids = [args.room_id] if args.room_id is not None else sorted(snapshots["room_id"].unique())
    results = [
        result
        for room_id in room_ids
        if (result := predict_room(snapshots, int(room_id), target, origin, args.artifact_dir))
        is not None
    ]
    if not results:
        sys.exit("No prior snapshots found for the requested room(s).")

    print(f"Count predictions for {target} ({TIMEZONE}); forecast origin: {origin}")
    print("These are model estimates, not live head counts.")
    print(
        pd.DataFrame(results).to_string(
            index=False,
            formatters={
                "count": lambda value: f"{value:.1f}",
                "occupancy_pct": lambda value: f"{value:.1f}",
                "capacity": lambda value: f"{value:.1f}",
                "snapshot_age_hours": lambda value: f"{value:.1f}",
            },
        )
    )


if __name__ == "__main__":
    main()