import csv
import hashlib
import os
import re
import shutil
import tempfile
from collections import Counter
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from penndata.ml.features import ACADEMIC_CALENDAR_PATH
from penndata.ml.parse_calendar import parse_calendar, read_text


FIELDNAMES = ["term", "event", "start", "end", "note", "status"]
TERM_PATTERN = re.compile(r"^(Fall|Spring|Summer) (\d{4})$")
ARCHIVE_DIR = Path(__file__).resolve().parents[2] / "ml" / "academic_calendar_sources"
MIN_EVENTS_PER_TERM = 5


def validate_events(events):
    if not events:
        raise ValueError("No calendar events were parsed.")

    term_counts = Counter()
    years_by_season = {"Fall": set(), "Spring": set(), "Summer": set()}
    for event in events:
        term = event["term"]
        match = TERM_PATTERN.fullmatch(term)
        if match is None:
            raise ValueError(f"Unrecognized term label: {term!r}")

        season, year_text = match.groups()
        year = int(year_text)
        years_by_season[season].add(year)
        term_counts[term] += 1

        if not event["event"].strip():
            raise ValueError(f"An event in {term} has no name.")

        start = event["start"]
        end = event["end"]
        if event["tbd"]:
            if start is not None or end is not None:
                raise ValueError(f"TBD event in {term} unexpectedly has dates.")
        elif start is None or end is None or start > end:
            raise ValueError(f"Invalid date range for {event['event']!r} in {term}.")

    incomplete_terms = sorted(
        term for term, count in term_counts.items() if count < MIN_EVENTS_PER_TERM
    )
    if incomplete_terms:
        raise ValueError(
            "Too few events parsed for these terms; refusing import: "
            + ", ".join(incomplete_terms)
        )

    incomplete_seasons = [
        season for season, years in years_by_season.items() if len(years) < 3
    ]
    if incomplete_seasons:
        raise ValueError(
            "Expected three years of entries for every season; missing coverage for: "
            + ", ".join(incomplete_seasons)
        )


def _read_existing_rows(path):
    if not path.exists():
        return []

    with path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        missing = set(FIELDNAMES).difference(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"{path} is missing columns: {', '.join(sorted(missing))}"
            )
        return [
            {field: (row.get(field) or "").strip() for field in FIELDNAMES}
            for row in reader
        ]


def _event_to_row(event):
    return {
        "term": event["term"],
        "event": event["event"],
        "start": event["start"].isoformat() if event["start"] else "",
        "end": event["end"].isoformat() if event["end"] else "",
        "note": event["note"],
        "status": "TBD" if event["tbd"] else "",
    }


def merge_calendar_rows(existing_rows, incoming_events):
    incoming_rows = [_event_to_row(event) for event in incoming_events]
    replaced_terms = {row["term"] for row in incoming_rows}
    retained = [row for row in existing_rows if row["term"] not in replaced_terms]
    merged = retained + incoming_rows

    def sort_key(row):
        match = TERM_PATTERN.fullmatch(row["term"])
        if match is None:
            return (9999, 3, row["term"], row["event"])
        season, year = match.groups()
        season_order = {"Fall": 0, "Spring": 1, "Summer": 2}[season]
        return (int(year), season_order, row["event"], row["start"])

    return sorted(merged, key=sort_key), replaced_terms, len(existing_rows) - len(retained)


def _write_csv_atomically(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            newline="",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as output:
            temporary_path = Path(output.name)
            writer = csv.DictWriter(output, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _archive_pdf(source, archive_dir):
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    archive_path = archive_dir / f"{source.stem}-{digest[:12]}{source.suffix.lower()}"
    archive_dir.mkdir(parents=True, exist_ok=True)
    if archive_path.exists():
        if hashlib.sha256(archive_path.read_bytes()).hexdigest() != digest:
            raise ValueError(f"Archive filename collision at {archive_path}.")
        return archive_path

    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "wb",
            dir=archive_dir,
            prefix=f".{archive_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as output:
            temporary_path = Path(output.name)
            with source.open("rb") as source_file:
                shutil.copyfileobj(source_file, output)
        os.replace(temporary_path, archive_path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return archive_path


class Command(BaseCommand):
    help = (
        "Preview or import a Penn academic-calendar PDF. Imports replace only "
        "the represented terms and preserve all other calendar history."
    )

    def add_arguments(self, parser):
        parser.add_argument("pdf", help="Path to the released academic-calendar PDF.")
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Archive the PDF and update the canonical CSV (otherwise preview only).",
        )
        parser.add_argument(
            "--calendar-csv",
            default=str(ACADEMIC_CALENDAR_PATH),
            help="Canonical calendar CSV path.",
        )
        parser.add_argument(
            "--archive-dir",
            default=str(ARCHIVE_DIR),
            help="Directory for hash-named source PDF archives.",
        )

    def handle(self, *args, **options):
        pdf_path = Path(options["pdf"]).expanduser().resolve()
        if not pdf_path.is_file():
            raise CommandError(f"PDF not found: {pdf_path}")
        if pdf_path.suffix.lower() != ".pdf":
            raise CommandError("The input must be a PDF file.")

        try:
            events = parse_calendar(read_text(str(pdf_path)))
            validate_events(events)
            calendar_path = Path(options["calendar_csv"]).expanduser().resolve()
            existing_rows = _read_existing_rows(calendar_path)
            merged_rows, replaced_terms, removed_count = merge_calendar_rows(
                existing_rows,
                events,
            )
        except (ImportError, OSError, ValueError) as exc:
            if isinstance(exc, ImportError) and "pdfplumber" in str(exc):
                raise CommandError(
                    "PDF support is not installed. Install the backend dependencies "
                    "to get pdfplumber."
                ) from exc
            raise CommandError(str(exc)) from exc

        event_count = len(events)
        tbd_count = sum(event["tbd"] for event in events)
        self.stdout.write(f"Parsed {event_count} events ({tbd_count} TBD).")
        self.stdout.write(
            "Terms to replace: "
            + ", ".join(sorted(replaced_terms))
        )
        self.stdout.write("Parsed event labels by term:")
        for term in sorted(replaced_terms):
            labels = [
                f"{event['event']}{' [TBD]' if event['tbd'] else ''}"
                for event in events
                if event["term"] == term
            ]
            self.stdout.write(f"  {term}: {'; '.join(labels)}")
        self.stdout.write(
            f"Existing rows in those terms: {removed_count}; "
            f"other historical rows retained: {len(existing_rows) - removed_count}."
        )

        if not options["apply"]:
            self.stdout.write(
                self.style.WARNING(
                    "Preview only; rerun with --apply to archive the PDF and update the CSV."
                )
            )
            return

        archive_path = Path(options["archive_dir"]).expanduser().resolve()
        try:
            archived_pdf = _archive_pdf(pdf_path, archive_path)
            _write_csv_atomically(calendar_path, merged_rows)
        except OSError as exc:
            raise CommandError(f"Could not save calendar import: {exc}") from exc

        self.stdout.write(self.style.SUCCESS(f"Archived PDF: {archived_pdf}"))
        self.stdout.write(self.style.SUCCESS(f"Updated calendar CSV: {calendar_path}"))
        self.stdout.write(
            "Next: retrain and evaluate the fitness model before deploying new artifacts."
        )
