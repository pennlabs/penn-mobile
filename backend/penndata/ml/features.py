from __future__ import annotations

import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar

from penndata.ml.constants import FINALS_MD, OPEN_TIMES, SESSION_MD, TIMEZONE


def load_snapshot_frame(rows) -> pd.DataFrame:
    df = pd.DataFrame(list(rows))
    if df.empty:
        return df
    return prepare_frame(df)


def prepare_frame(
    df: pd.DataFrame,
    *,
    keep_missing_count: bool = False,
) -> pd.DataFrame:
    #clean snapshots and create model features

    df = df.copy()

    if df.empty:
        return df

    if "capacity" not in df.columns:
        df["capacity"] = pd.NA

    df["count"] = pd.to_numeric(df["count"], errors="coerce")
    df["capacity"] = pd.to_numeric(df["capacity"], errors="coerce")
    df["room_id"] = pd.to_numeric(
        df["room_id"], errors="coerce"
    ).astype("Int64")

    df["ts"] = pd.to_datetime(
        df["date"],
        utc=True,
        format="mixed",
        errors="coerce",
    )

    df["ts_local"] = (
        df["ts"]
        .dt.tz_convert(TIMEZONE)
        .dt.tz_localize(None)
    )

    df = df.dropna(subset=["ts_local", "room_id"])

    if not keep_missing_count:
        df = df.dropna(subset=["count"])

    if df.empty:
        return df.reset_index(drop=True)

    df["room_id"] = df["room_id"].astype(int)

    df = (
        df.sort_values(["room_id", "ts_local"])
        .drop_duplicates(["room_id", "ts_local"])
        .reset_index(drop=True)
    )

    observed = df[df["count"].notna()]

    if not observed.empty:
        room_cap = infer_people_capacity(observed)
        df["room_capacity"] = df["room_id"].map(room_cap)
    else:
        df["room_capacity"] = pd.to_numeric(
            df["capacity"], errors="coerce"
        )

    missing_cap = df["room_capacity"].isna()
    df.loc[missing_cap, "room_capacity"] = df.loc[
        missing_cap, "capacity"
    ]

    df["occ_rate"] = df["count"] / df["room_capacity"]

    df["hour"] = df["ts_local"].dt.hour
    df["dow"] = df["ts_local"].dt.dayofweek
    df["minute_of_day"] = (
        df["ts_local"].dt.hour * 60
        + df["ts_local"].dt.minute
    )
    df["month"] = df["ts_local"].dt.month
    df["is_weekend"] = (df["dow"] >= 5).astype(int)

    df["is_open"] = [
        int(is_open_at(ts, dow))
        for ts, dow in zip(df["ts_local"], df["dow"])
    ]

    min_date = df["ts_local"].min()
    max_date = df["ts_local"].max()

    if pd.isna(min_date) or pd.isna(max_date):
        df["is_holiday"] = 0
    else:
        hol = USFederalHolidayCalendar().holidays(
            min_date.normalize(),
            max_date.normalize(),
        )
        df["is_holiday"] = (
            df["ts_local"].dt.normalize().isin(hol).astype(int)
        )

    md = df["ts_local"].dt.month * 100 + df["ts_local"].dt.day

    df["in_session"] = _in_ranges(md, SESSION_MD)
    df["finals_window"] = _in_ranges(md, FINALS_MD)

    return df


def is_open_at(ts, dow: int | None = None) -> bool:
    weekday = int(
        dow if dow is not None else getattr(ts, "dayofweek", ts.weekday())
    )

    open_h, close_h = OPEN_TIMES[weekday]
    hour = ts.hour + ts.minute / 60.0

    return open_h <= hour < close_h


def infer_people_capacity(df: pd.DataFrame) -> pd.Series:
    caps = {}

    for room_id, g in df.groupby("room_id"):
        raw = pd.to_numeric(g["capacity"], errors="coerce")

        recent = pd.to_numeric(
            g.sort_values("ts_local")
            .tail(200)["capacity"],
            errors="coerce",
        )

        people = (
            _stable_people_capacity(recent.dropna())
            or _stable_people_capacity(raw.dropna())
        )

        if people is not None:
            caps[int(room_id)] = people
            continue

        ok = g[
            (raw > 0)
            & (raw <= 200)
            & (g["count"] > 0)
        ]

        if len(ok):
            inferred = (
                ok["count"]
                / raw.loc[ok.index]
                * 100
            ).round()

            caps[int(room_id)] = float(
                inferred.mode().iloc[0]
            )
        else:
            caps[int(room_id)] = float(
                max(g["count"].max(), 1)
            )

    return pd.Series(caps)


def _stable_people_capacity(
    series: pd.Series,
) -> float | None:
    if series.empty:
        return None

    if series.nunique() > 8:
        return None

    mode = float(series.mode().iloc[0])

    if (
        10 <= mode <= 500
        and (series.max() - series.min()) <= 30
    ):
        return mode

    return None


def add_lags(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if df.empty:
        return df

    df = _add_lag(
        df,
        pd.Timedelta("1h"),
        "lag_1h",
        pd.Timedelta("45min"),
    )

    df = _add_lag(
        df,
        pd.Timedelta("1D"),
        "lag_1d",
        pd.Timedelta("90min"),
    )

    for weeks in (1, 2, 3, 4):
        df = _add_lag(
            df,
            pd.Timedelta(days=7 * weeks),
            f"lag_{weeks}w",
            pd.Timedelta("90min"),
        )

    df["lag_7d"] = df["lag_1w"]

    df["lag_wk_mean4"] = df[
        [
            "lag_1w",
            "lag_2w",
            "lag_3w",
            "lag_4w",
        ]
    ].mean(axis=1)

    return df


def _add_lag(
    d: pd.DataFrame,
    delta,
    name: str,
    tol,
) -> pd.DataFrame:
    left = d[
        ["room_id", "ts_local"]
    ].copy()

    left["orig"] = left.index
    left["asof"] = left["ts_local"] - delta

    right = d[
        ["room_id", "ts_local", "count"]
    ].rename(
        columns={"count": name}
    )

    right["asof"] = right["ts_local"]

    merged = pd.merge_asof(
        left.sort_values("asof"),
        right.sort_values("asof"),
        on="asof",
        by="room_id",
        tolerance=tol,
        direction="backward",
        allow_exact_matches=True,
        suffixes=("", "_snap"),
    )

    snap_ts = (
        merged
        .set_index("orig")["ts_local_snap"]
        .reindex(d.index)
    )

    aligned = (
        merged
        .set_index("orig")[name]
        .reindex(d.index)
    )

    aligned = aligned.mask(
        snap_ts >= d["ts_local"]
    )

    d[name] = aligned

    return d


def _in_ranges(
    md: pd.Series,
    ranges,
) -> pd.Series:
    flag = pd.Series(
        0,
        index=md.index,
    )

    for start, end in ranges:
        flag = flag | (
            (md >= start)
            & (md <= end)
        ).astype(int)

    return flag.clip(upper=1)


def coverage_summary(
    df: pd.DataFrame,
) -> dict:
    if df.empty:
        return {"rows": 0}

    times = (
        df.drop_duplicates("ts_local")[
            "ts_local"
        ]
        .sort_values()
    )

    gaps_h = (
        times.diff()
        .dt.total_seconds()
        / 3600
    )

    per_room = (
        df.groupby("room_id")
        .size()
        .to_dict()
    )

    return {
        "rows": int(len(df)),
        "rooms": int(df["room_id"].nunique()),
        "earliest": str(df["ts_local"].min()),
        "latest": str(df["ts_local"].max()),
        "distinct_days": int(
            df["ts_local"].dt.date.nunique()
        ),
        "median_gap_hours": (
            float(gaps_h.median())
            if len(gaps_h)
            else None
        ),
        "gaps_over_24h": int(
            (gaps_h > 24).sum()
        ),
        "capacity_null_rate": float(
            df["capacity"].isna().mean()
        ),
        "rows_per_room": {
            int(k): int(v)
            for k, v in per_room.items()
        },
    }