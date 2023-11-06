from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = """
    Shows all user information given a pennkey or an email.
    """

    def add_arguments(self, parser):
        parser.add_argument("--pennkey", type=str, help="pennkey")
        parser.add_argument("--email", type=str, help="email")

    def handle(self, *args, **kwargs):
        if kwargs["pennkey"] is None and kwargs["email"] is None:
            self.stdout.write("Please provide a pennkey or an email.")
            return

        if kwargs["pennkey"] is not None:
            users = User.objects.filter(username=kwargs["pennkey"])
            if 
        else:
            users = User.objects.filter(email=kwargs["email"])
        

