from django.core.management.base import BaseCommand

from laundry.api_wrapper import Laundry


laundry = Laundry()


class Command(BaseCommand):
    help = "Captures a new Laundry Snapshot for every Laundry room."

    def handle(self, *args, **kwargs):
        laundry.save_data()
        self.stdout.write("Captured snapshots!")
