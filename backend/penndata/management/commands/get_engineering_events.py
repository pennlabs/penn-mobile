import datetime
import json

import requests
from django.core.management.base import BaseCommand
from django.utils import timezone
import html

from penndata.models import Event


ENGINEERING_EVENTS_WEBSITE = "https://events.seas.upenn.edu/calendar/list/"


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        try:
            resp = requests.get(ENGINEERING_EVENTS_WEBSITE)
        except ConnectionError:
            return None

        html_content = resp.text

        start_marker = '<script type="application/ld+json">'
        end_marker = "</script>"
        start_index = html_content.find(start_marker)
        end_index = html_content.find(end_marker, start_index)
        json_ld_content = html_content[start_index + len(start_marker):end_index]

        events_data = json.loads(json_ld_content)

        for event in events_data:
            event_name = html.unescape(event.get("name", ""))
            description = html.unescape(event.get("description", "")).replace(
                "<p>", "").replace("</p>\n", "")
            url = event.get("url", "")

            start = datetime.datetime.fromisoformat(event.get("startDate"))
            end = event.get("endDate", "")
            if end != "":
                end = datetime.datetime.fromisoformat(end)
            else:
                end = None

            location = None
            if event.get("location"):
                location = event.get("location").get("name")

            email = None
            if event.get("organizer"):
                email = html.unescape(event.get("organizer").get("email"))

            Event.objects.update_or_create(
                name=event_name,
                defaults={
                    "event_type": "Engineering",
                    "image_url": "",
                    "start": timezone.make_aware(start),
                    "end": timezone.make_aware(end),
                    "location": location,
                    "website": url,
                    "description": description,
                    "email": email,
                },
            )

        self.stdout.write("Uploaded Engineering Events!")
