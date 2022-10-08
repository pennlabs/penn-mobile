from django.core.management.base import BaseCommand

from dining.api_wrapper import DiningAPIWrapper


class Command(BaseCommand):
    """
    Loads Weekly Menu
    """

    def handle(self, *args, **kwargs):
        d = DiningAPIWrapper()
        d.load_weekly_menu()
        self.stdout.write("Uploaded Weekly Menus!")
