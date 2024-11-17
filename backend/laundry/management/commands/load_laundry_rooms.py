import csv

from django.core.management.base import BaseCommand

from laundry.models import LaundryRoom


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        count = 0
        with open("laundry/data/laundry_data.csv") as data:
            reader = csv.DictReader(data)
            for row in reader:
                LaundryRoom.objects.get_or_create(
                    room_id=int(row["room_id"]),
                    defaults={
                        "name": row["room_name"],
                        "location": row["room_description"],
                        "location_id": int(row["room_location"]),
                        "total_washers": int(row["count_washers"]),
                        "total_dryers": int(row["count_dryers"]),
                    },
                )
                count += 1

        self.stdout.write("Uploaded Laundry Rooms!")
        (
            self.stdout.write(
                f"Warning: There are {LaundryRoom.objects.all().count() - count} rooms in the "
                f"database but not in the data file. If they are no longer supported by Penn's "
                f"servers, consider deleting them."
            )
            if count < LaundryRoom.objects.all().count()
            else None
        )
