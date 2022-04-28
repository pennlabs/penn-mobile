import datetime

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone
from portal.models import Post

User = get_user_model()


class Command(BaseCommand):
    def handle(self, *args, **kwargs):

        call_command("load_target_populations")

        Post.objects.create(
            club_code="pennlabs",
            title="Test title 1",
            subtitle="Test subtitle 1",
            expire_date=timezone.localtime() + datetime.timedelta(days=10),
        )

        Post.objects.create(
            club_code="pennlabs",
            title="Test title 2",
            subtitle="Test subtitle 2",
            expire_date=timezone.localtime() + datetime.timedelta(days=10),
        )

        self.stdout.write("Uploaded database info!")
