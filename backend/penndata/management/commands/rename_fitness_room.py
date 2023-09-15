from django.core.management.base import BaseCommand

from penndata.management.commands.get_fitness_snapshot import cap_string
from penndata.models import FitnessRoom


class Command(BaseCommand):
    help = "Renames fitness rooms."

    def handle(self, *args, **kwargs):
        for room in FitnessRoom.objects.all():
            room.name = cap_string(room.name)
            room.save()

        self.stdout.write("Renamed rooms!")
