from django.core.management.base import BaseCommand, CommandError

from penndata.ml.features import add_lags, coverage_summary
from penndata.ml.train import (
    ARTIFACT_DIR,
    fit_final_models,
    snapshots_from_csv,
    snapshots_from_db,
    walk_forward,
)


class Command(BaseCommand):
    help = (
        "Evaluate fitness occupancy models with walk-forward MAE, then save "
        "7d and 24h HistGradientBoosting artifacts."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv",
            help="Path to a FitnessSnapshot CSV (id,date,count,room_id,capacity).",
        )
        parser.add_argument(
            "--from-db",
            action="store_true",
            help="Load snapshots from FitnessSnapshot instead of a CSV.",
        )
        parser.add_argument(
            "--skip-eval",
            action="store_true",
            help="Only fit final models; skip walk-forward evaluation.",
        )
        parser.add_argument(
            "--artifact-dir",
            default=str(ARTIFACT_DIR),
            help="Directory to write model_7d.joblib and model_24h.joblib.",
        )
        parser.add_argument(
            "--metrics-csv",
            help="Optional path for the raw walk-forward metrics CSV.",
        )

    def handle(self, *args, **options):
        if options["from_db"]:
            df = snapshots_from_db()
        elif options["csv"]:
            df = snapshots_from_csv(options["csv"])
        else:
            raise CommandError("Pass --csv PATH or --from-db.")

        summary = coverage_summary(df)
        self.stdout.write(f"Loaded {summary}")

        if df.empty or summary.get("rows", 0) < 100:
            raise CommandError(
                "Not enough snapshots to train. Keep get_fitness_snapshot running "
                "every 10 minutes and retry after more history accumulates."
            )

        if not options["skip_eval"]:
            metrics = walk_forward(df)
            fold_metrics = metrics[metrics["scope"] == "fold"].copy()
            open_metrics = metrics[metrics["scope"] == "fold_open"].copy()

            def summarize(frame):
                return (
                    frame.groupby("method", as_index=False)
                    .agg(
                        folds=("fold", "nunique"),
                        rows=("n_test", "sum"),
                        MAE_people=("MAE_people", "mean"),
                        MAE_people_fold_sd=("MAE_people", "std"),
                        MAE_pct_pts=("MAE_pct_pts", "mean"),
                        MAE_pct_pts_fold_sd=("MAE_pct_pts", "std"),
                        bucket_exact_pct=("bucket_exact_%", "mean"),
                    )
                    .sort_values("MAE_pct_pts")
                )

            grouped_open = summarize(open_metrics)
            grouped_all = summarize(fold_metrics)
            self.stdout.write(
                "Open-hours walk-forward summary (monthly fold mean; lower MAE is better):"
            )
            self.stdout.write(grouped_open.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
            self.stdout.write("\nAll-hours walk-forward summary:")
            self.stdout.write(grouped_all.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
            worst_fold = (
                open_metrics.groupby(["method", "fold"], as_index=False)["MAE_pct_pts"]
                .mean()
                .sort_values(["method", "MAE_pct_pts"], ascending=[True, False])
                .groupby("method")
                .head(1)
            )
            self.stdout.write("\nWorst open-hours fold by method (MAE percentage points):")
            self.stdout.write(worst_fold.to_string(index=False, float_format=lambda v: f"{v:.3f}"))

            room_metrics = metrics[metrics["scope"] == "room_open"].copy()
            room_summary = (
                room_metrics.groupby(["method", "room_id"], as_index=False)
                .agg(
                    MAE_people=("MAE_people", "mean"),
                    MAE_pct_pts=("MAE_pct_pts", "mean"),
                    bucket_exact_pct=("bucket_exact_%", "mean"),
                    rows=("n_test", "sum"),
                )
                .sort_values(["method", "MAE_people"], ascending=[True, False])
            )
            self.stdout.write("\nOpen-hours room-level summary (fold means):")
            for method in grouped_open["method"]:
                subset = room_summary[room_summary["method"] == method].copy()
                if subset.empty:
                    continue
                self.stdout.write(f"\n{method}:")
                self.stdout.write(
                    subset[
                        ["room_id", "rows", "MAE_people", "MAE_pct_pts", "bucket_exact_pct"]
                    ].to_string(index=False, float_format=lambda v: f"{v:.3f}")
                )

            best = grouped_open.iloc[0]["method"]
            self.stdout.write(
                self.style.SUCCESS(
                    f"Lowest open-hours fold-average MAE: {best}. "
                    "This is an evaluation result, not automatic model selection."
                )
            )
            if options["metrics_csv"]:
                metrics.to_csv(options["metrics_csv"], index=False)
                self.stdout.write(f"Wrote raw fold metrics to {options['metrics_csv']}")

        paths = fit_final_models(df, artifact_dir=options["artifact_dir"])
        self.stdout.write(self.style.SUCCESS(f"Wrote {paths}"))
