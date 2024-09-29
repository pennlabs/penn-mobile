import csv

from django.core.management.base import BaseCommand

from laundry.models import LaundryRoom


class Command(BaseCommand):
    def handle(self, *args, **kwargs):

        with open("laundry/data/laundry_data_new.csv") as data:
            reader = csv.reader(data)

            for i, row in enumerate(reader):
                room_id, name, location, location_id, total_washers, total_dryers = row

                LaundryRoom.objects.create(
                    room_id=room_id,
                    name=name,
                    location=location,
                    location_id=location_id,
                    total_washers=total_washers,
                    total_dryers=total_dryers,
                    new=True,
                )

        self.stdout.write("Uploaded Laundry Rooms!")
