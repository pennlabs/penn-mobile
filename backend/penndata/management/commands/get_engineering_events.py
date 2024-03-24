import datetime
import html
import json

import requests
from django.core.management.base import BaseCommand

from penndata.models import Event


ENGINEERING_EVENTS_WEBSITE = "https://events.seas.upenn.edu/calendar/list/"


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        try:
            resp = requests.get(ENGINEERING_EVENTS_WEBSITE)
        except ConnectionError:
            print("Error:", ConnectionError)
            return None

        html_content = resp.text

        start_marker = '<script type="application/ld+json">'
        end_marker = "</script>"
        start_index = html_content.find(start_marker)
        end_index = html_content.find(end_marker, start_index)
        json_ld_content = html_content[start_index + len(start_marker) : end_index]

        events_data = json.loads(json_ld_content)

        for event in events_data:
            if (event_name := html.unescape(event.get("name", ""))) == "":
                continue

            description = (
                html.unescape(event.get("description", "")).replace("<p>", "").replace("</p>\n", "")
            )
            url = event.get("url", None)

            start = datetime.datetime.fromisoformat(event.get("startDate"))
            end = datetime.datetime.fromisoformat(event["endDate"]) if "endDate" in event else None

            location = event.get("location", dict()).get("name")
            if (organizer := event.get("organizer")) and (email := organizer.get("email")):
                email = html.unescape(email)
            else:
                email = None

            Event.objects.update_or_create(
                name=event_name,
                defaults={
                    "event_type": Event.TYPE_PENN_ENGINEERING,
                    "image_url": None,
                    "start": start,
                    "end": end,
                    "location": location,
                    "website": url,
                    "description": description,
                    "email": email,
                },
            )

        self.stdout.write("Uploaded Engineering Events!")
