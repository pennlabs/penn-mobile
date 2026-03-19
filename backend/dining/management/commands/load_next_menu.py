import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.core.management.base import BaseCommand
from django.db import close_old_connections
from django.utils import timezone

from dining.api_wrapper import DiningAPIWrapper

class Command(BaseCommand):
    """
    Loads menu for the next 7 days, starting from today. Takes about 3 minutes to run.
    Invariant: For every date, the database should contain the menus for
    the next 7 days, including the original date.
    """

    def load_one_menu(self, delta, *args, **kwargs):
        """
        Loads menu for a single day
        """
        d = DiningAPIWrapper()
        d.load_menu(timezone.now().date() + datetime.timedelta(days=delta))
        self.stdout.write("Loaded new Dining Menu for " + str(timezone.now().date() + datetime.timedelta(days=delta)))


    def handle(self, *args, **kwargs):
        """
        Load menu for the next 7 days
        """
        start_time = timezone.now()

        for i in range(7):
            self.load_one_menu(i)
        
        end_time = timezone.now()
        elapsed_time = end_time - start_time
        self.stdout.write(f"TOTAL menu stuff for today took {elapsed_time} seconds")

        