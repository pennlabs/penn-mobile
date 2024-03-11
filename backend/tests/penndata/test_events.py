from django.core.management import call_command
from django.test import TestCase

from penndata.models import Event


class TestPennTodayEvents(TestCase):
    def setUp(self):
        call_command("get_penn_today_events")

    def test_event(self):
        events = Event.objects.all()
        self.assertLess(0, events.count())
