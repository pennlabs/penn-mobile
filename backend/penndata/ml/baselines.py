from __future__ import annotations

import numpy as np
import pandas as pd


def historical_average(train: pd.DataFrame, test: pd.DataFrame) -> pd.Series:
    a = train.groupby(["room_id", "dow", "hour"])["count"].mean().rename("a")
    b = train.groupby(["room_id", "hour"])["count"].mean().rename("b")
    c = train.groupby("room_id")["count"].mean().rename("c")
    t = test[["room_id", "dow", "hour"]].join(a, on=["room_id", "dow", "hour"])
    t = t.join(b, on=["room_id", "hour"]).join(c, on="room_id")
    return t["a"].fillna(t["b"]).fillna(t["c"])


def smoothed_historical_average(train: pd.DataFrame, test: pd.DataFrame) -> pd.Series:
    """Shrink noisy room/dow/hour estimates toward room-hour and room means."""
    a = train.groupby(["room_id", "dow", "hour"])["count"].mean().rename("a")
    a_n = train.groupby(["room_id", "dow", "hour"]).size().rename("a_n")
    b = train.groupby(["room_id", "hour"])["count"].mean().rename("b")
    b_n = train.groupby(["room_id", "hour"]).size().rename("b_n")
    c = train.groupby("room_id")["count"].mean().rename("c")

    t = test[["room_id", "dow", "hour"]].join(a, on=["room_id", "dow", "hour"])
    t = t.join(a_n, on=["room_id", "dow", "hour"]).join(b, on=["room_id", "hour"])
    t = t.join(b_n, on=["room_id", "hour"]).join(c, on="room_id")

    room_dow_hour = t["a"].fillna(t["b"]).fillna(t["c"])
    exact_weight = np.minimum(t["a_n"].fillna(0), 10) / 10.0
    room_hour_weight = np.maximum(1.0 - exact_weight, 0.0)

    exact_est = t["a"].fillna(t["b"]).fillna(t["c"])
    room_hour_est = t["b"].fillna(t["c"])
    pred = np.where(
        t["a_n"].fillna(0) > 0,
        exact_est * exact_weight + room_hour_est * (1.0 - exact_weight),
        np.where(
            t["b_n"].fillna(0) > 0,
            t["b"] * np.minimum(t["b_n"].fillna(0), 10) / 10.0 + t["c"] * (1.0 - np.minimum(t["b_n"].fillna(0), 10) / 10.0),
            t["c"],
        ),
    )
    return pd.Series(pred, index=test.index, name="smoothed_hist_avg").clip(lower=0)


def same_time_last_week(test: pd.DataFrame, fallback: pd.Series) -> pd.Series:
    return test["lag_7d"].fillna(fallback)


def room_mean(train: pd.DataFrame, test: pd.DataFrame) -> pd.Series:
    means = train.groupby("room_id")["count"].mean()
    return test["room_id"].map(means)
