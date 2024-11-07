import csv
from typing import Any

from django.core.management.base import BaseCommand

from laundry.models import LaundryRoom


class Command(BaseCommand):
    def handle(self, *args: Any, **kwargs: Any) -> None:

        with open("laundry/data/laundry_data.csv") as data:
            reader = csv.reader(data)

            for i, row in enumerate(reader):
                hall_id, hall_name, location, uuid, total_washers, total_dryers = row

                LaundryRoom.objects.get_or_create(
                    hall_id=int(hall_id),
                    name=hall_name,
                    location=location,
                    uuid=uuid,
                    total_washers=total_washers,
                    total_dryers=total_dryers,
                )

        self.stdout.write("Uploaded Laundry Rooms!")
