"""Feature importance for the fitness occupancy GBMs.

HistGradientBoostingRegressor has no built-in feature_importances_, so this uses
permutation importance on a chronological holdout: shuffle one feature (or a group of
related features) in the holdout set and measure how much the MAE gets worse. A big
increase means the model leans on that feature. ~0 means it ignores it. Negative means
the feature is adding noise on unseen data.

It also prints holdout MAE for the baselines to see whether the GBM beats them.

Usage:
    python3 feature_importance.py --csv penndata/muchdatastuff/data.csv
    python3 feature_importance.py --from-db --holdout-days 21
    python3 feature_importance.py --csv data.csv --horizon 24h --repeats 10
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pennmobile.settings.development")

import django 

django.setup()

from penndata.ml.baselines import historical_average, same_time_last_week 
from penndata.ml.constants import HORIZON_FEATURES 
from penndata.ml.features import add_lags 
from penndata.ml.train import _fit_gbm, snapshots_from_csv, snapshots_from_db

GROUPS = {
    "weekly lags (lag_7d, lag_wk_mean4)": ["lag_7d", "lag_wk_mean4"],
    "yesterday lag (lag_1d)": ["lag_1d"],
    "hour lag (lag_1h)": ["lag_1h"],
    "time of day/week": ["minute_of_day", "dow", "is_weekend", "is_open"],
    "calendar (month, holiday, session, finals)": [
        "month", "is_holiday", "in_session", "finals_window",
    ],
    "room": ["room_id"],
}


def mae(y, pred):
    y = np.asarray(y, dtype=float)
    pred = np.asarray(pred, dtype=float)
    ok = ~np.isnan(y) & ~np.isnan(pred)
    return float(np.abs(y[ok] - pred[ok]).mean()) if ok.any() else float("nan")


def predict(model, X):
    return np.clip(model.predict(X), 0, None)


def permutation_increase(model, X, y, cols, repeats, rng):
    cols = [c for c in cols if c in X.columns]
    if not cols:
        return None
    base = mae(y, predict(model, X))
    values = X[cols].to_numpy()
    deltas = []
    for _ in range(repeats):
        idx = rng.permutation(len(X))
        Xp = X.copy()
        Xp[cols] = values[idx]
        deltas.append(mae(y, predict(model, Xp)) - base)
    return float(np.mean(deltas)), float(np.std(deltas))


def report_horizon(name, train, test, repeats, rng):
    feats = HORIZON_FEATURES[name]
    print()
    print("=" * 78)
    print(f"GBM {name}-horizon")
    print("=" * 78)

    try:
        model, usable = _fit_gbm(train, feats)
    except ValueError as exc:
        print(f"Could not train: {exc}")
        return

    dropped = [f for f in feats if f not in usable]
    if dropped:
        print(f"Dropped (constant or missing in training data): {dropped}")

    X = test[usable]
    y = test["count"]
    base = mae(y, predict(model, X))
    print(f"Holdout MAE (people): {base:.3f}   ({len(test)} rows)")

    rows = []
    for col in usable:
        res = permutation_increase(model, X, y, [col], repeats, rng)
        if res:
            rows.append({"feature": col, "MAE_increase": res[0], "std": res[1]})
    single = pd.DataFrame(rows).sort_values("MAE_increase", ascending=False)
    single["pct_of_model_MAE"] = single["MAE_increase"] / base * 100

    print()
    print("Single-feature permutation importance (higher = model relies on it more):")
    print(single.to_string(index=False, float_format=lambda v: f"{v:.3f}"))

    grows = []
    for gname, cols in GROUPS.items():
        res = permutation_increase(model, X, y, cols, repeats, rng)
        if res:
            grows.append(
                {"group": gname, "MAE_increase": res[0], "std": res[1]}
            )
    if grows:
        grouped = pd.DataFrame(grows).sort_values("MAE_increase", ascending=False)
        print()
        print("Grouped permutation importance (related features shuffled together):")
        print(grouped.to_string(index=False, float_format=lambda v: f"{v:.3f}"))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--csv", help="CSV of snapshots (date,count,room_id,capacity)")
    src.add_argument("--from-db", action="store_true", help="Read FitnessSnapshot rows")
    p.add_argument("--holdout-days", type=int, default=28,
                   help="Newest N days are the test set; everything before trains (default 28)")
    p.add_argument("--horizon", choices=["1h", "24h", "7d", "all"], default="all",
                   help="'all' = 24h and 7d, the two that are actually trained")
    p.add_argument("--repeats", type=int, default=5, help="Shuffles per feature (default 5)")
    p.add_argument("--include-closed", action="store_true",
                   help="Score closed hours too (default: open hours only)")
    args = p.parse_args()

    df = snapshots_from_csv(args.csv) if args.csv else snapshots_from_db()
    if df.empty:
        sys.exit("No usable rows.")

    if args.from_db:
        print("NOTE: --from-db includes any fake rows from the debug script.\n")

    print(f"Rows: {len(df)}   rooms: {df['room_id'].nunique()}")
    print(f"Range: {df['ts_local'].min()}  ->  {df['ts_local'].max()}")
    print(f"Distinct days: {df['ts_local'].dt.date.nunique()}")

    df = add_lags(df)
    cutoff = df["ts_local"].max() - pd.Timedelta(days=args.holdout_days)
    train = df[df["ts_local"] < cutoff]
    test = df[df["ts_local"] >= cutoff]
    if not args.include_closed:
        test = test[test["is_open"] == 1]

    print(f"Train rows: {len(train)}   holdout rows: {len(test)}   cutoff: {cutoff}")
    if len(train) < 100 or len(test) < 50:
        sys.exit("Not enough data for a train/holdout split. Lower --holdout-days or collect more data.")

    # How much of each lag feature actually exists? Mostly-NaN lags mean the model
    # is effectively running on calendar features alone.
    lag_cols = [c for c in ("lag_1h", "lag_1d", "lag_7d", "lag_wk_mean4") if c in df.columns]
    avail = pd.DataFrame(
        {
            "train_non_null_%": [train[c].notna().mean() * 100 for c in lag_cols],
            "holdout_non_null_%": [test[c].notna().mean() * 100 for c in lag_cols],
        },
        index=lag_cols,
    )
    print()
    print("Lag availability:")
    print(avail.to_string(float_format=lambda v: f"{v:.1f}"))

    # Baselines on the same holdout.
    hist = historical_average(train, test)
    week = same_time_last_week(test, hist)
    print()
    print("Holdout MAE (people), same rows:")
    print(f"  hist avg (room,dow,hour):  {mae(test['count'], hist):.3f}")
    print(f"  same time last week:       {mae(test['count'], week):.3f}")
    unseen = float(hist.isna().mean() * 100)
    if unseen:
        print(f"  (hist avg had no value for {unseen:.1f}% of holdout rows; those are skipped)")

    rng = np.random.default_rng(0)
    horizons = ["24h", "7d"] if args.horizon == "all" else [args.horizon]
    for h in horizons:
        report_horizon(h, train, test, args.repeats, rng)

    print()
    print("How to read this:")
    print("  - MAE_increase is how many more people off the model gets when the feature is scrambled.")
    print("  - Near 0 or negative: the model isn't using it (or it hurts on new data).")
    print("  - Compare the GBM MAE to the baselines above. If the GBM isn't better, importance")
    print("    mostly tells you what it is leaning on, not that it is useful.")
    print("  - One holdout window is noisy. Try a few --holdout-days values.")


if __name__ == "__main__":
    main()