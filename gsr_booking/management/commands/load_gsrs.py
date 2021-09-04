import csv

from django.core.management.base import BaseCommand

from gsr_booking.models import GSR


class Command(BaseCommand):
    def handle(self, *args, **kwargs):

        with open("gsr_booking/data/gsr_data.csv") as data:
            reader = csv.reader(data)

            for i, row in enumerate(reader):
                if i == 0:
                    continue

                # collects room information from csv
                lid, gid, name, service = row

                # gets image from s3 given the lid and gid
                image_url = (
                    f"https://s3.us-east-2.amazonaws.com/labs.api/gsr/lid-{lid}-gid-{gid}.jpg"
                )
                kind = GSR.KIND_WHARTON if service == "wharton" else GSR.KIND_LIBCAL
                GSR.objects.create(lid=lid, gid=gid, name=name, kind=kind, image_url=image_url)

        self.stdout.write("Uploaded GSRs!")
