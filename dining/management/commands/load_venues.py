import csv

from django.core.management.base import BaseCommand

from dining.models import Venue


class Command(BaseCommand):
    def handle(self, *args, **kwargs):

        with open("dining/data/dining_images.csv") as data:
            reader = csv.reader(data)
            for i, row in enumerate(reader):
                venue_id, image_url = row
                Venue.objects.get_or_create(venue_id=venue_id, image_url=image_url)
<<<<<<< HEAD

        self.stdout.write("Uploaded Venues!")
=======
                
        self.stdout.write("Uploaded Venues!")
>>>>>>> d3f6306d09f285f0293e8c0148e17a34e80ff3d1
