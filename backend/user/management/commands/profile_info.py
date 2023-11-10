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
        else:
            users = User.objects.filter(email=kwargs["email"])

        if len(users) == 0:
            self.stdout.write("User not found.")
            return
        if len(users) > 1:
            self.stdout.write("Multiple users found? Huh?")
            return

        user = users[0]
        self.stdout.write(f"User: {user.username}")
        self.stdout.write(f"Email: {user.email}")
        self.stdout.write(f"First name: {user.first_name}")
        self.stdout.write(f"Last name: {user.last_name}")
