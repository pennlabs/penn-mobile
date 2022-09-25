import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils import timezone

from penndata.models import FitnessRoom, FitnessSnapshot


def get_capacities():

    # capacities default to 0 because spreadsheet number appears blank if 0 people at location
    capacities = {
        "4th Floor Fitness": 0,
        "3rd Floor Fitness": 0,
        "2nd Floor Strength": 0,
        "Basketball Courts": 0,
        "MPR": 0,
        "Climbing Wall": 0,
        "1st floor Fitness": 0,
        "Pool-Shallow": 0,
        "Pool-Deep": 0,
    }
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

    embedded_spreadsheet = soup.find("body", {"class": "docs-gm"})
    table_rows = embedded_spreadsheet.findChildren("tr")
    for row in table_rows:
        cells = row.findChildren("td")
        if len(cells) >= 2:
            location = cells[0].getText()
            if location in capacities:
                try:
                    count = int(cells[1].getText())
                    capacities[location] = count
                except ValueError:
                    capacities[location] = 0

    return capacities


class Command(BaseCommand):
    help = "Captures a new Fitness Snapshot for every Laundry room."

    def handle(self, *args, **kwargs):
        now = timezone.localtime()

        # prevent double creating FitnessSnapshots
        if FitnessSnapshot.objects.filter(date=now).count() == 0:

            data = get_capacities()

            for room_name, count in data.items():

                fitness_room = FitnessRoom.objects.get(name=room_name)

                FitnessSnapshot.objects.create(
                    room=fitness_room,
                    date=now,
                    count=count,
                )
        self.stdout.write("Captured fitness snapshots!")
