from __future__ import annotations

from datetime import timedelta
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from django.utils import timezone

from penndata.ml.constants import BUCKET_EDGES, BUCKET_NAMES, TIMEZONE
from penndata.ml.features import add_lags, is_open_at, prepare_frame
from penndata.ml.train import ARTIFACT_DIR

import logging
logger = logging.getLogger(__name__)


def occupancy_bucket(rate: float | None) -> str | None:
    if rate is None or (isinstance(rate, float) and np.isnan(rate)):
        return None
    return BUCKET_NAMES[int(np.digitize([rate], BUCKET_EDGES)[0])]


def choose_horizon(now, target) -> str:
    ahead = (target - now).total_seconds() / 3600
    if ahead <= 2:
        return "1h"
    if ahead <= 36:
        return "24h"
    return "7d"


@lru_cache(maxsize=4)
def load_artifact(horizon: str, artifact_dir: str | None = None):
    import joblib

    directory = Path(artifact_dir) if artifact_dir else ARTIFACT_DIR
    for name in dict.fromkeys((horizon, "24h", "7d")):
        path = directory / f"model_{name}.joblib"
        if not path.exists():
            continue
        try:
            return joblib.load(path)
        except Exception:
            logger.exception("Could not load model artifact %s", path)
    return None


def _hist_avg_from_artifact(artifact: dict, room_id: int, dow: int, hour: int) -> float | None:
    key = (room_id, dow, hour)
    if key in artifact.get("hist_avg_room_dow_hour", {}):
        return float(artifact["hist_avg_room_dow_hour"][key])
    if (room_id, hour) in artifact.get("hist_avg_room_hour", {}):
        return float(artifact["hist_avg_room_hour"][(room_id, hour)])
    if room_id in artifact.get("hist_avg_room", {}):
        return float(artifact["hist_avg_room"][room_id])
    return None


def _hist_avg_from_history(history: pd.DataFrame, room_id: int, dow: int, hour: int) -> float:
    room = history[history["room_id"] == room_id]
    exact = room[(room["dow"] == dow) & (room["hour"] == hour)]["count"]
    if len(exact):
        return float(exact.mean())
    by_hour = room[room["hour"] == hour]["count"]
    if len(by_hour):
        return float(by_hour.mean())
    return float(room["count"].mean()) if len(room) else 0.0


def _feature_row(
    history: pd.DataFrame,
    room_id: int,
    target_local: pd.Timestamp,
) -> pd.DataFrame:
    room_history = history[
        history["room_id"] == room_id
    ]

    if room_history.empty:
        raise ValueError(
            f"No history exists for room {room_id}"
        )

    capacities = room_history[
        "room_capacity"
    ].dropna()

    capacity = (
        float(capacities.iloc[-1])
        if len(capacities)
        else None
    )

    if capacity is None:
        raw_capacity = room_history[
            "capacity"
        ].dropna()

        if len(raw_capacity):
            capacity = float(
                raw_capacity.iloc[-1]
            )

    stub = pd.DataFrame(
        [
            {
                "date": (
                    target_local
                    .tz_localize(TIMEZONE)
                    .tz_convert("UTC")
                ),
                "count": np.nan,
                "room_id": room_id,
                "capacity": capacity,
            }
        ]
    )

    prepared_stub = prepare_frame(
        stub,
        keep_missing_count=True,
    )

    if prepared_stub.empty:
        raise ValueError(
            "Could not construct prediction feature row"
        )

    combined = pd.concat(
        [
            history,
            prepared_stub,
        ],
        ignore_index=True,
    )

    combined.loc[
        combined.index[-1],
        "count",
    ] = np.nan

    combined = add_lags(combined)

    return combined.iloc[[-1]]

def _predict_count(
    row: pd.DataFrame,
    history: pd.DataFrame,
    horizon: str,
    artifact,
) -> tuple[float, str]:
    room_id = int(
        row["room_id"].iloc[0]
    )

    dow = int(
        row["dow"].iloc[0]
    )

    hour = int(
        row["hour"].iloc[0]
    )

    fallback = _hist_avg_from_history(
        history,
        room_id,
        dow,
        hour,
    )

    if artifact:
        artifact_fallback = (
            _hist_avg_from_artifact(
                artifact,
                room_id,
                dow,
                hour,
            )
        )

        if artifact_fallback is not None:
            fallback = artifact_fallback

    # Try the ML model.
    if artifact is not None and horizon in (
        "24h",
        "7d",
    ):
        features = [
            f
            for f in artifact.get(
                "features",
                [],
            )
            if f in row.columns
        ]

        if features:
            X = row[features]

            try:
                pred = float(
                    np.clip(
                        artifact["model"].predict(X)[0],
                        0,
                        None,
                    )
                )

                return (
                    pred,
                    f"gbm-{artifact.get('horizon', horizon)}",
                )

            except Exception:
                pass

    return (
        float(max(fallback, 0)),
        "hist-avg",
    )
def predict_fitness(room, target_time=None, hours_ahead=None, artifact_dir=None):
    from penndata.models import FitnessSnapshot

    now = timezone.localtime()
    snapshots = list(
        FitnessSnapshot.objects.filter(room=room)
        .order_by("date")
        .values("date", "count", "room_id", "capacity")
    )
    history = prepare_frame(pd.DataFrame(snapshots)) if snapshots else pd.DataFrame()

    current = None
    latest = (
        FitnessSnapshot.objects.filter(room=room).order_by("-date").first()
        if snapshots
        else None
    )
    cap = None
    if not history.empty:
        cap = float(history["room_capacity"].dropna().iloc[-1])
    elif latest and latest.capacity:
        cap = float(latest.capacity)

    if latest:
        rate = (latest.count / cap) if cap else None
        current = {
            "time": timezone.localtime(latest.date).isoformat(),
            "count": latest.count,
            "occupancy": rate,
            "bucket": occupancy_bucket(rate),
        }

    targets = _target_times(now, target_time, hours_ahead)
    predictions = []
    for target in targets:
        local = target.astimezone(timezone.get_current_timezone()).replace(tzinfo=None)
        local = pd.Timestamp(local)
        if not is_open_at(local):
            predictions.append(_closed_payload(target, cap))
            continue
        if history.empty:
            predictions.append(
                {
                    "time": target.isoformat(),
                    "count": None,
                    "occupancy": None,
                    "bucket": None,
                    "method": "no-history",
                }
            )
            continue
        horizon = choose_horizon(now, target)
        artifact = load_artifact(horizon, str(artifact_dir) if artifact_dir else None)
        row = _feature_row(history, room.id, local)
        count, method = _predict_count(row, history, horizon, artifact)
        if cap:
            count = min(count, cap)
        rate = (count / cap) if cap else None
        predictions.append(
            {
                "time": target.isoformat(),
                "count": round(count, 1),
                "occupancy": round(rate, 4) if rate is not None else None,
                "bucket": occupancy_bucket(rate),
                "method": method,
            }
        )

    return {
        "room": room.name,
        "room_id": room.id,
        "capacity": cap,
        "current": current,
        "predictions": predictions,
    }


def _closed_payload(target, cap):
    return {
        "time": target.isoformat(),
        "count": 0,
        "occupancy": 0.0 if cap else None,
        "bucket": occupancy_bucket(0.0),
        "method": "closed",
    }


def _target_times(now, target_time, hours_ahead):
    if target_time is not None:
        return [timezone.localtime(target_time)]
    if hours_ahead is not None:
        return [now + timedelta(hours=int(hours_ahead))]
    hours = []
    for h in (1, 2, 3, 4):
        hours.append(now + timedelta(hours=h))
    return hours
