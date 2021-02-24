import csv

from django.core.management.base import BaseCommand

from laundry.api_wrapper import HALL_URL, parse_a_hall
from laundry.models import LaundryRoom


class Command(BaseCommand):
    def handle(self, *args, **kwargs):

        with open("laundry/data/laundry_data.csv") as data:
            reader = csv.reader(data)

            for i, row in enumerate(reader):
                hall_id, hall_name, location, uuid = row

                machines = parse_a_hall(HALL_URL + uuid)
                total_washers = sum(
                    [machines["washers"][x] for x in ["open", "running", "offline", "out_of_order"]]
                )
                total_dryers = sum(
                    [machines["dryers"][x] for x in ["open", "running", "offline", "out_of_order"]]
                )

                LaundryRoom.objects.get_or_create(
                    hall_id=int(hall_id),
                    name=hall_name,
                    location=location,
                    uuid=uuid,
                    total_washers=total_washers,
                    total_dryers=total_dryers,
                )

        self.stdout.write("Uploaded Laundry Rooms!")
