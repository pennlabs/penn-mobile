import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from dining.api_wrapper import DiningAPIWrapper
from dining.utils.menu_view_cache import delete_menu_view_cache


class Command(BaseCommand):
    """
    Loads menu for the next 7 days, starting from today. Takes about 3 minutes to run.
    Invariant: For every date, the database should contain the menus for
    the next 7 days, including the original date.
    """

    def load_one_menu(self, today, delta, *args, **kwargs):
        """
        Loads menu for a single day
        """
        d = DiningAPIWrapper()
        d.load_menus(today + datetime.timedelta(days=delta))
        delete_menu_view_cache(today + datetime.timedelta(days=delta))
        self.stdout.write(
            "Loaded new Dining Menu for " + str(today + datetime.timedelta(days=delta))
        )

    def handle(self, *args, **kwargs):
        """
        Load menu for the next 7 days
        """
        today = timezone.now().date()

        for i in range(7):
            self.load_one_menu(today, i)
