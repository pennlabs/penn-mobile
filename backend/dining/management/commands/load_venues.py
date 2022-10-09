import csv

from django.core.management.base import BaseCommand

from dining.models import Venue


class Command(BaseCommand):
    """
    Loads Venues based on CSV
    """

    def handle(self, *args, **kwargs):

        with open("dining/data/dining_images.csv") as data:
            reader = csv.reader(data)
            for i, row in enumerate(reader):
                venue_id, image_url = row
                Venue.objects.get_or_create(venue_id=venue_id, image_url=image_url)

        self.stdout.write("Uploaded Venues!")
