#!/usr/bin/env python3
"""Parse the Penn Three-Year Academic Calendar (PDF or text) into CSV and ICS.

Usage:
    python parse_calendar.py calendar.pdf            # needs: pip install pdfplumber
    python parse_calendar.py calendar.txt
    python parse_calendar.py calendar.pdf -o out     # writes out.csv and out.ics
"""
import argparse
import csv
import re
from datetime import date, timedelta

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
MON = "(?:" + "|".join(MONTHS) + ")"

# One date cell: "October 12-15", "August 27-September 1", "November 4 (Cornell)",
# or the placeholder "(to be decided)".
CELL = rf"(?:{MON} \d{{1,2}}(?:-(?:{MON} )?\d{{1,2}})?(?: \([^)]*\))?|\(to be decided\))"

SECTION_HDR = re.compile(
    r"(Fall|Spring|Summer) (\d{4}) \1 Term (\d{4}) \1 Term (\d{4}) \1 Term")
EVENT = re.compile(
    rf"(?P<label>.+?)\s+(?P<c1>{CELL})\s+(?P<c2>{CELL})\s+(?P<c3>{CELL})"
    r"(?=\s+[A-Z(]|\s*$)")
RANGE = re.compile(rf"({MON}) (\d{{1,2}})(?:-(?:({MON}) )?(\d{{1,2}}))?(?: \(([^)]*)\))?")


def read_text(path):
    if path.lower().endswith(".pdf"):
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    else:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    return re.sub(r"\s+", " ", text).replace("\u2019", "'")


def parse_cell(cell, year):
    """Return (start, end, note, tbd) for one date cell."""
    if cell.startswith("(to be decided)"):
        return None, None, "", True
    m = RANGE.fullmatch(cell)
    m1, d1, m2, d2, note = m.groups()
    start = date(year, MONTHS.index(m1) + 1, int(d1))
    if d2 is None:
        end = start
    else:
        end = date(year, MONTHS.index(m2 or m1) + 1, int(d2))
    return start, end, note or "", False


def parse_calendar(text):
    headers = list(SECTION_HDR.finditer(text))
    events = []
    for i, h in enumerate(headers):
        term = h.group(1)
        years = [int(h.group(n)) for n in (2, 3, 4)]
        stop = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        body = text[h.end():stop]
        body = body.split(" Notes:")[0]
        # drop the "Move-in Information / More Information" column headings
        body = re.sub(r"^\s*(?:Move-in Information\s*)?(?:More Information\s*)*", "", body)
        for m in EVENT.finditer(body):
            for year, key in zip(years, ("c1", "c2", "c3")):
                start, end, note, tbd = parse_cell(m.group(key), year)
                events.append({
                    "term": f"{term} {year}",
                    "event": m.group("label").strip(),
                    "start": start, "end": end,
                    "note": note, "tbd": tbd,
                })
    return events


def write_csv(events, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["term", "event", "start", "end", "note", "status"])
        for e in events:
            w.writerow([e["term"], e["event"],
                        e["start"] or "", e["end"] or "", e["note"],
                        "TBD" if e["tbd"] else ""])


def write_ics(events, path):
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//parse_calendar//EN"]
    for n, e in enumerate(events):
        if e["tbd"]:
            continue
        summary = e["event"] + (f" ({e['note']})" if e["note"] else "")
        lines += [
            "BEGIN:VEVENT",
            f"UID:{n}-{e['start']:%Y%m%d}@parse_calendar",
            f"DTSTAMP:{date.today():%Y%m%d}T000000Z",
            f"DTSTART;VALUE=DATE:{e['start']:%Y%m%d}",
            # ICS all-day end dates are exclusive
            f"DTEND;VALUE=DATE:{e['end'] + timedelta(days=1):%Y%m%d}",
            f"SUMMARY:{summary}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write("\r\n".join(lines) + "\r\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--out", default="calendar", help="output basename")
    args = ap.parse_args()

    events = parse_calendar(read_text(args.input))
    write_csv(events, args.out + ".csv")
    write_ics(events, args.out + ".ics")
    tbd = sum(e["tbd"] for e in events)
    print(f"Parsed {len(events)} entries ({tbd} still TBD) -> {args.out}.csv, {args.out}.ics")