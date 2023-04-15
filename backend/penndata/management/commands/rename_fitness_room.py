from datetime import datetime

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils import timezone

from penndata.models import FitnessRoom, FitnessSnapshot

class Command(BaseCommand):
    help = "Renames a fitness room."

    def add_arguments(self, parser):
        parser.add_argument("old_name", type=str, help="Old name of the fitness room")
        parser.add_argument("new_name", type=str, help="New name of the fitness room")

    def handle(self, *args, **kwargs):
        old_name = kwargs["old_name"]
        new_name = kwargs["new_name"]

        if not (room := FitnessRoom.objects.filter(name=old_name).first()):
            self.stdout.write(f"Error: room {old_name} not found")
            return

        room.name = new_name
        room.save()

        self.stdout.write("Renamed room!")
