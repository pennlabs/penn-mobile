from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from user.models import NotificationSetting, NotificationToken


User = get_user_model()


class Command(BaseCommand):
    help = """Fix user settings"""

    def handle(self, *args, **kwargs):
        # delete all settings
        NotificationSetting.objects.all().delete()
        self.stdout.write("All settings deleted!")

        # create the proper settings for all users
        SERVICE_OPTIONS = NotificationSetting.SERVICE_OPTIONS
        for user in User.objects.all():
            token, _ = NotificationToken.objects.get_or_create(user=user)
            for service, _ in SERVICE_OPTIONS:
                NotificationSetting.objects.update_or_create(
                    token=token, service=service, defaults={"enabled": False}
                )

        self.stdout.write("New settings created!")
