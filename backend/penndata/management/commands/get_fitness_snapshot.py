from django.core.management.base import BaseCommand
from django.utils import timezone

from penndata.models import FitnessRoom, FitnessSnapshot
from penndata.views import Fitness


# from laundry.api_wrapper import save_data


class Command(BaseCommand):
    help = "Captures a new Fitness Snapshot for every Laundry room."

    def handle(self, *args, **kwargs):
        # save_data()
        now = timezone.localtime()

        if FitnessSnapshot.objects.filter(date=now).count() == 0:
            fitness = Fitness()
            data = fitness.get_capacities()

            for room_name, count in data.items():

                fitness_room = FitnessRoom.objects.get(name=room_name)

                FitnessSnapshot.objects.create(
                    room=fitness_room, date=now, count=count,
                )
        self.stdout.write("Captured fitness snapshots!")
