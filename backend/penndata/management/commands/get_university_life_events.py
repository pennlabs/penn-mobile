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

    def handle(self, *args, **kwargs):

        response = requests.get(UNIVERSITY_LIFE_URL)

        assert response.ok

        soup = BeautifulSoup(response.text, "html.parser")

        events_div = soup.find("div", class_="list events")

        # First <section> is not an event section
        event_sections = events_div.find_all("section")[1:]

        for event_section in event_sections:

            date_str = event_section.find(class_="heading").find("h2").get("id")

            events = event_section.find(class_="info").find_all("a", attrs={"attr-event-id": True})
            print(len(events))
            for event in events:
                location = event.get("attr-location")
                website = event.get("href")
                name = event.get("data-modal-title")

                start_str = event.find("span", class_="start").text
                start = self.to_datetime(f"{date_str} {start_str}")

                end_str = event.find("span", class_="end").text
                end = self.to_datetime(f"{date_str} {end_str}")

                event_type = Event.TYPE_UNIVERSITY_LIFE

                # print(event_type)
                # print(location)
                # print(website)
                # print(name)
                # print(start)
                # print(end)
                # print("---")

                event_response = requests.get(website)
                if not response.ok:
                    print("conitnued")
                    continue

                event_soup = BeautifulSoup(event_response.text, "html.parser")
                event_description = (
                    event_soup.find("div", class_="main")
                    .find("div", class_="content")
                    .find("p")
                    .text
                )

                Event.objects.create(
                    name=name,
                    event_type=event_type,
                    image_url=None,
                    start=start,
                    end=end,
                    location=location,
                    website=website,
                    description=event_description,
                    email=None,
                )

        self.stdout.write("Uploaded Calendar Events!")
