"""Walk-forward training for fitness occupancy.

Usage via manage.py::

    python manage.py train_fitness_model --csv penndata/muchdatastuff/data.csv
    python manage.py train_fitness_model --from-db
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from penndata.ml.baselines import (
    historical_average,
    room_mean,
    same_time_last_week,
    smoothed_historical_average,
)
from penndata.ml.constants import BUCKET_EDGES, GBM_PARAMS, HORIZON_FEATURES
from penndata.ml.features import (
    add_lags,
    infer_people_capacity,
    load_snapshot_frame,
    prepare_frame,
)


ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
MIN_TEST_ROWS = 250
MIN_TRAIN_ROWS = 5000


def bucket(rate) -> np.ndarray:
    return np.digitize(np.asarray(rate), BUCKET_EDGES)


def mae_people(y_true, y_pred) -> float:
    return float(np.abs(np.asarray(y_true) - np.asarray(y_pred)).mean())


def mae_pct_points(occ_rate, pred_count, capacity) -> float:
    pred_rate = np.asarray(pred_count) / np.asarray(capacity)
    return float(np.abs(np.asarray(occ_rate) - pred_rate).mean() * 100)


def bucket_accuracy(occ_rate, pred_count, capacity) -> float:
    actual = bucket(occ_rate)
    pred = bucket(np.asarray(pred_count) / np.asarray(capacity))
    return float((actual == pred).mean() * 100)


def _fit_gbm(
    train: pd.DataFrame,
    features: list[str],
    target: str = "count",
    loss: str = "poisson",
):
    from sklearn.ensemble import HistGradientBoostingRegressor

    usable = [
        f
        for f in features
        if f in train.columns
        and train[f].nunique(dropna=True) >= 2
    ]

    if not usable:
        raise ValueError(
            "No usable features available for GBM training."
        )

    training = train[
        usable + [target]
    ].copy()

    # The target must always exist.
    training = training.dropna(
        subset=[target]
    )

    if len(training) < 100:
        raise ValueError(
            f"Only {len(training)} usable training rows; "
            "need at least 100."
        )

    X = training[usable]
    y = training[target]

    categorical_features = [
        f == "room_id"
        for f in usable
    ]

    model = HistGradientBoostingRegressor(
        categorical_features=categorical_features,
        loss=loss,
        **GBM_PARAMS,
    )

    model.fit(X, y)

    return model, usable


def _predict_gbm(
    model,
    usable,
    test: pd.DataFrame,
    target: str = "count",
) -> np.ndarray:
    prediction = model.predict(test[usable])
    if target == "occ_rate":
        return np.clip(prediction, 0, 1) * test["room_capacity"].to_numpy()
    return np.minimum(
        np.clip(prediction, 0, None),
        test["room_capacity"].to_numpy(),
    )


def _with_fold_capacity(
    train: pd.DataFrame,
    test: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    capacities = infer_people_capacity(train)
    train = train.copy()
    test = test.copy()
    for frame in (train, test):
        frame["room_capacity"] = frame["room_id"].map(capacities)
        frame["occ_rate"] = frame["count"] / frame["room_capacity"]
    return train, test


def _append_metric_rows(
    rows: list[dict],
    scope: str,
    fold: str,
    method: str,
    test: pd.DataFrame,
    pred: np.ndarray,
) -> None:
    if test.empty:
        return

    rows.append(
        {
            "scope": scope,
            "fold": fold,
            "room_id": None,
            "method": method,
            "n_test": len(test),
            "MAE_people": mae_people(test["count"], pred),
            "MAE_pct_pts": mae_pct_points(
                test["occ_rate"], pred, test["room_capacity"]
            ),
            "bucket_exact_%": bucket_accuracy(
                test["occ_rate"], pred, test["room_capacity"]
            ),
        }
    )

    room_scope = "room" if scope == "fold" else "room_open"
    room_df = test[["room_id", "count", "occ_rate", "room_capacity"]].copy()
    room_df["pred"] = np.asarray(pred, dtype=float)
    for room_id, group in room_df.groupby("room_id"):
        rows.append(
            {
                "scope": room_scope,
                "fold": fold,
                "room_id": int(room_id),
                "method": method,
                "n_test": len(group),
                "MAE_people": mae_people(group["count"], group["pred"]),
                "MAE_pct_pts": mae_pct_points(
                    group["occ_rate"], group["pred"], group["room_capacity"]
                ),
                "bucket_exact_%": bucket_accuracy(
                    group["occ_rate"], group["pred"], group["room_capacity"]
                ),
            }
        )


def walk_forward(df: pd.DataFrame) -> pd.DataFrame:
    """Train on earlier months and score all rows and open hours in the next month."""
    df = add_lags(df)
    df["ym"] = df["ts_local"].dt.to_period("M")
    cov = df.groupby("ym").size()
    folds = [
        m
        for m in cov.index
        if cov.loc[m] >= MIN_TEST_ROWS and (df["ts_local"] < m.start_time).sum() >= MIN_TRAIN_ROWS
    ]
    if not folds:
        raise ValueError("No eligible walk-forward folds. Collect more data or lower thresholds.")

    model_specs = (
        ("gbm 7d-horizon", HORIZON_FEATURES["7d"], "count", "poisson"),
        ("gbm 24h-horizon", HORIZON_FEATURES["24h"], "count", "poisson"),
        ("gbm occupancy 7d-horizon", HORIZON_FEATURES["7d"], "occ_rate", "squared_error"),
        ("gbm occupancy 24h-horizon", HORIZON_FEATURES["24h"], "occ_rate", "squared_error"),
    )

    rows = []
    for month in folds:
        start, end = month.start_time, (month + 1).start_time
        train = df[df["ts_local"] < start]
        test = df[(df["ts_local"] >= start) & (df["ts_local"] < end)]
        train, test = _with_fold_capacity(train, test)
        preds = {
            "room mean": room_mean(train, test),
            "smoothed hist avg": smoothed_historical_average(train, test),
            "hist avg (room,dow,hour)": historical_average(train, test),
        }
        preds["same time last week"] = same_time_last_week(
            test, preds["hist avg (room,dow,hour)"]
        )
        for name, feats, target, loss in model_specs:
            try:
                model, usable = _fit_gbm(train, feats, target=target, loss=loss)
                preds[name] = _predict_gbm(model, usable, test, target=target)

            except ValueError as exc:
                print(f"Skipping {name} for fold {month}: {exc}")
        capacity = test["room_capacity"].to_numpy()
        for name, pred in preds.items():
            pred = np.minimum(np.clip(np.asarray(pred, dtype=float), 0, None), capacity)
            _append_metric_rows(rows, "fold", str(month), name, test, pred)
            open_mask = test["is_open"].to_numpy() == 1
            _append_metric_rows(
                rows,
                "fold_open",
                str(month),
                name,
                test.loc[open_mask],
                pred[open_mask],
            )
    return pd.DataFrame(rows)


def fit_final_models(df: pd.DataFrame, artifact_dir: Path | str | None = None) -> dict:
    import joblib

    df = add_lags(df)
    artifact_dir = Path(artifact_dir) if artifact_dir is not None else ARTIFACT_DIR
    artifact_dir.mkdir(parents=True, exist_ok=True)

    room_cap = df.groupby("room_id")["room_capacity"].median().to_dict()
    saved = {}
    for horizon, feats in (("7d", HORIZON_FEATURES["7d"]), ("24h", HORIZON_FEATURES["24h"])):
        model, usable = _fit_gbm(df, feats)
        payload = {
            "model": model,
            "features": usable,
            "target": "count",
            "horizon": horizon,
            "room_capacity": {int(k): float(v) for k, v in room_cap.items()},
            "hist_avg_room_dow_hour": df.groupby(["room_id", "dow", "hour"])["count"]
            .mean()
            .to_dict(),
            "hist_avg_room_hour": df.groupby(["room_id", "hour"])["count"].mean().to_dict(),
            "hist_avg_room": df.groupby("room_id")["count"].mean().to_dict(),
        }
        path = artifact_dir / f"model_{horizon}.joblib"
        joblib.dump(payload, path)
        saved[horizon] = str(path)
    return saved


def snapshots_from_db() -> pd.DataFrame:
    from penndata.models import FitnessSnapshot

    rows = FitnessSnapshot.objects.values("id", "date", "count", "room_id", "capacity")
    return load_snapshot_frame(rows)


def snapshots_from_csv(path: str) -> pd.DataFrame:
    return prepare_frame(pd.read_csv(path))
