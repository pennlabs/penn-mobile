import csv

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from laundry.models import LaundryRoom


class Command(BaseCommand):
    def handle(self, *args, **kwargs):

        if not settings.DEBUG:
            raise CommandError("You probably do not want to run this script in production!")

        with open("laundry/data/laundry_data.csv") as data:
            reader = csv.reader(data)

            for i, row in enumerate(reader):
                hall_id, hall_name, location, uuid = row
                LaundryRoom.objects.create(
                    hall_id=int(hall_id), name=hall_name, location=location, uuid=uuid
                )
