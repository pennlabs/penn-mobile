import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from dining.api_wrapper import DiningAPIWrapper


class Command(BaseCommand):
    """
    Loads Menu for 1 week in advance.
    Invariant: For every date, the database should contain the menus for
    the next 7 days, including the original date.
    """

    def handle(self, *args, **kwargs):
        d = DiningAPIWrapper()
        d.load_menu(timezone.now().date() + datetime.timedelta(days=6))
        self.stdout.write("Loaded new Dining Menu!")
