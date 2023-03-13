from datetime import datetime

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils import timezone

from penndata.models import FitnessRoom, FitnessSnapshot


def get_capacities():

    # capacities default to 0 because spreadsheet number appears blank if 0 people at location
    locations = [
        "4th Floor Fitness",
        "3rd Floor Fitness",
        "2nd Floor Strength",
        "Basketball Courts",
        "MPR",
        "Climbing Wall",
        "1st floor Fitness",
        "Pool-Shallow",
        "Pool-Deep",
    ]
    capacities = {location: {"count": 0, "capacity": 0} for location in locations}

    date = timezone.localtime()

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
        return None

    html = resp.content.decode("utf8")
    soup = BeautifulSoup(html, "html5lib")
    if not (embedded_spreadsheet := soup.find("tbody")):
        return None

    table_rows = embedded_spreadsheet.findChildren("tr")
    for i, row in enumerate(table_rows):
        cells = row.findChildren("td")
        if i == 0:
            date = timezone.make_aware(datetime.strptime(cells[1].getText(), "%m/%d/%Y %H:%M:%S"))
        elif (location := cells[0].getText()) in capacities:
            try:
                count = int(cells[1].getText())
                capacity = float(cells[2].getText().strip("%"))
                capacities[location] = {"count": count, "capacity": capacity}
            except ValueError:
                pass
    return capacities, date


class Command(BaseCommand):
    help = "Captures a new Fitness Snapshot for every Laundry room."

    def handle(self, *args, **kwargs):
        data, date = get_capacities()

        # prevent double creating FitnessSnapshots
        if FitnessSnapshot.objects.filter(date=date).exists():
            self.stdout.write("FitnessSnapshots already exist for this date!")
            return

        FitnessSnapshot.objects.bulk_create(
            [
                FitnessSnapshot(
                    room=FitnessRoom.objects.get_or_create(name=room_name)[0],
                    date=date,
                    count=info["count"],
                    capacity=info["capacity"],
                )
                for room_name, info in data.items()
            ]
        )

        self.stdout.write("Captured fitness snapshots!")
