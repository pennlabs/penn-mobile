from django.core.management.base import BaseCommand

from penndata.models import FitnessRoom


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        fitness_rooms = [
            "4th Floor Fitness",
            "3rd Floor Fitness",
            "2nd Floor Strength",
            "Basketball Courts",
            "MPR",
            "Climbing Wall",
            "1st floor Fitness",
            "Pool-Shallow",
            "Pool-Deep",
        ]
        for room in fitness_rooms:
            FitnessRoom.objects.get_or_create(name=room)

        self.stdout.write("Uploaded Fitness Rooms!")
