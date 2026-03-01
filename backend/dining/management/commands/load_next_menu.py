import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from dining.api_wrapper import DiningAPIWrapper

from concurrent.futures import ThreadPoolExecutor

yes
class Command(BaseCommand):
    """
    Loads Menu for 1 week in advance.
    Invariant: For every date, the database should contain the menus for
    the next 7 days, including the original date.
    """

    def load_one_menu(self, delta, *args, **kwargs):
        d = DiningAPIWrapper()
        d.load_menu(timezone.now().date() + datetime.timedelta(days=delta))
        self.stdout.write("Loaded new Dining Menu for " + str(timezone.now().date() + datetime.timedelta(days=delta)))


    def handle(self, *args, **kwargs):
        with ThreadPoolExecutor() as executor:
            for i in range(7):
                executor.submit(self.load_one_menu, i, *args, **kwargs)        