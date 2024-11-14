import datetime
from typing import Any, Optional

import requests
from bs4 import BeautifulSoup
from dateutil import parser
from django.core.management.base import BaseCommand
from django.utils import timezone

from penndata.models import FitnessRoom, FitnessSnapshot


def cap_string(s: str) -> str:
    return " ".join([word[0].upper() + word[1:] for word in s.split()])


def get_usages() -> tuple[Optional[dict[str, dict[str, int | float]]], datetime.datetime]:

    # count/capacities default to 0 since spreadsheet number appears blank if no one there
    locations = [
        "4th Floor Fitness",
        "3rd Floor Fitness",
        "2nd Floor Strength",
        "Basketball Courts",
        "MPR",
        "Climbing Wall",
        "1st Floor Fitness",
        "Pool-Shallow",
        "Pool-Deep",
    ]
    usages: dict[str, dict[str, int | float]] = {
        location: {"count": 0, "capacity": 0} for location in locations
    }

    date = timezone.localtime()  # default if can't get date from spreadsheet

    try:
        resp = requests.get(
            (
                "https://docs.google.com/spreadsheets/u/0/d/e/"
                "2PACX-1vSX91_MlAjJo5uVLznuy7BFnUgiBOI28oBCReLRKKo76L"
                "-k8EFgizAYXpIKPBX_c76wC3aztn3BogD4"
                "/pubhtml/sheet?headers=false&gid=0"
            )
        )
    except ConnectionError:
        return None, date

    html = resp.content.decode("utf8")
    soup = BeautifulSoup(html, "html5lib")
    if not (embedded_spreadsheet := soup.find("tbody")):
        return None, date

    table_rows = embedded_spreadsheet.findChildren("tr")
    for i, row in enumerate(table_rows):
        cells = row.findChildren("td")
        if i == 0:
            date = timezone.make_aware(parser.parse(cells[1].getText()))
        elif (location := cap_string(cells[0].getText())) in usages:
            try:
                count = int(cells[1].getText())
                capacity = float(cells[2].getText().strip("%"))
                usages[location] = {"count": count, "capacity": capacity}
            except ValueError:
                pass
        else:
            print(f"Unknown location: {location}")
    return usages, date


class Command(BaseCommand):
    help = "Captures a new Fitness Snapshot for every Laundry room."

    def handle(self, *args: Any, **kwargs: Any) -> None:
        usage_by_location, date = get_usages()

        # prevent double creating FitnessSnapshots
        if FitnessSnapshot.objects.filter(date=date).exists():
            self.stdout.write("FitnessSnapshots already exist for this date!")
            return

        if not usage_by_location:
            self.stdout.write("Failed to get usages from spreadsheet!")
            return

        FitnessSnapshot.objects.bulk_create(
            [
                FitnessSnapshot(
                    room=FitnessRoom.objects.get_or_create(name=room_name)[0],
                    date=date,
                    count=room_usage["count"],
                    capacity=room_usage["capacity"],
                )
                for room_name, room_usage in usage_by_location.items()
            ]
        )

        self.stdout.write("Captured fitness snapshots!")
