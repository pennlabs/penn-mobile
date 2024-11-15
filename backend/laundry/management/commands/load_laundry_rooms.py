import csv

from django.core.management.base import BaseCommand

from laundry.models import LaundryRoom


class Command(BaseCommand):
    def handle(self, *args, **kwargs):

        with open("laundry/data/laundry_data.csv") as data:
            reader = csv.DictReader(data)

            for row in reader:
                LaundryRoom.objects.get_or_create(
                    room_id=int(row["room_id"]),
                    name=row["room_name"],
                    location=row["room_description"],
                    location_id=int(row["room_location"]),
                    total_washers=int(row["count_washers"]),
                    total_dryers=int(row["count_dryers"]),
                    new=True,
                )

        self.stdout.write("Uploaded Laundry Rooms!")
