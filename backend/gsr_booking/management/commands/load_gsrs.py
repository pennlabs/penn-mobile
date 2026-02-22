import csv

from django.core.management.base import BaseCommand

from gsr_booking.models import GSR, clear_gsr_location_caches


class Command(BaseCommand):
    def handle(self, *args, **kwargs):

        with open("gsr_booking/data/gsr_data.csv") as data:
            reader = csv.reader(data)
            next(reader)
            for lid, gid, name, service, bookable_days in reader:
                # gets image from s3 given the lid and gid
                # TODO: fix image url!
                image_url = (
                    f"https://s3.us-east-2.amazonaws.com/labs.api/gsr/lid-{lid}-gid-{gid}.jpg"
                )
                kind = (
                    GSR.KIND_PENNGROUPS
                    if service == "penngroups"
                    else GSR.KIND_WHARTON if service == "wharton" else GSR.KIND_LIBCAL
                )
                GSR.objects.update_or_create(
                    lid=lid,
                    gid=gid,
                    defaults={
                        "name": name,
                        "kind": kind,
                        "image_url": image_url,
                        "bookable_days": int(bookable_days),
                    },
                )

        # Note: Caches are automatically cleared by post_save signals on GSR model
        # But we clear explicitly here as well for clarity and to handle edge cases
        clear_gsr_location_caches()

        self.stdout.write("Uploaded GSRs and cleared location caches!")
