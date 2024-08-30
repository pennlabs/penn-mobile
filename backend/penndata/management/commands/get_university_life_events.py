import requests
from bs4 import BeautifulSoup
from dateutil import parser
from django.core.management.base import BaseCommand
from django.utils import timezone

from penndata.models import Event


UNIVERSITY_LIFE_URL = "https://ulife.vpul.upenn.edu/calendar/"


class Command(BaseCommand):

    def to_datetime(self, date_str):
        return timezone.make_aware(parser.parse(date_str))

    def parse_event_section(self, event_section):
        date_str = event_section.find(class_="heading").find("h2").get("id")

        events = event_section.find(class_="info").find_all("a", attrs={"attr-event-id": True})

        for event in events:
            location = event.get("attr-location")
            website = event.get("href")
            name = event.get("data-modal-title")

            start_str = event.find("span", class_="start").text
            start = self.to_datetime(f"{date_str} {start_str}")

            end_str = event.find("span", class_="end").text
            end = self.to_datetime(f"{date_str} {end_str}")

            event_response = requests.get(website)
            if not event_response.ok:
                print(f"Event: {name} had invalid website response")
                continue

            event_soup = BeautifulSoup(event_response.text, "html.parser")
            event_description = (
                event_soup.find("div", class_="main").find("div", class_="content").find("p").text
            )

            Event.objects.update_or_create(
                name=name,
                event_type=Event.TYPE_UNIVERSITY_LIFE,
                image_url=None,
                start=start,
                end=end,
                location=location,
                website=website,
                description=event_description,
                email=None,
            )

    def handle(self, *args, **kwargs):

        response = requests.get(UNIVERSITY_LIFE_URL)

        soup = BeautifulSoup(response.text, "html.parser")

        events_div = soup.find("div", class_="list events")

        # First <section> is not an event section
        event_sections = events_div.find_all("section")[1:]

        # TODO: Make sure all events are covered. There is one div with extra sections,
        # however those are far away events and could potentially be moved up to the
        # main div depending on website implementation
        for event_section in event_sections:
            self.parse_event_section(event_section)

        self.stdout.write("Uploaded Calendar Events!")
