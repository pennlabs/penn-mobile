import datetime
import html
from typing import Any

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils import timezone

from penndata.models import Event


VENTURE_EVENTS_WEBSITE = "https://venturelab.upenn.edu/venture-lab-events"
HEADERS = {"User-Agent": "Mozilla/5.0 AppleWebKit/537.36 Chrome/91.0.4472.124 Safari/537.36"}


class Command(BaseCommand):
    def handle(self, *args: Any, **kwargs: Any) -> None:
        now = timezone.localtime()
        current_month, current_year = now.month, now.year

        try:
            resp = requests.get(VENTURE_EVENTS_WEBSITE, headers=HEADERS)
        except ConnectionError:
            print("Error:", ConnectionError)
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        event_containers = soup.find_all("div", class_="PromoSearchResultEvent")
        last_start_datetime = None

        for event in event_containers:
            event_date_elem = event.find("div", class_="PromoSearchResultEvent-eventDate")
            event_start_datetime = None
            event_end_datetime = None
            # some events don't have a start/end date time or a year
            if event_date_elem:
                event_date_str = event_date_elem.text.strip()

                event_date_parts = event_date_str.split(" at ")
                event_start_str = event_date_parts[1].split(" - ")[0].strip()
                event_end_str = event_date_parts[1].split(" - ")[1].strip()

                event_start_datetime = datetime.datetime.strptime(
                    f"{event_date_parts[0]} {event_start_str}", "%B %d, %Y %I:%M%p"
                )
                event_end_datetime = datetime.datetime.strptime(
                    f"{event_date_parts[0]} {event_end_str}", "%B %d, %Y %I:%M%p"
                )
                last_start_datetime = event_start_datetime
            else:  # if no year given
                event_month_elem = event.find("div", class_="PromoSearchResultEvent-month")
                event_day_elem = event.find("div", class_="PromoSearchResultEvent-day")

                if event_month_elem and event_day_elem:
                    event_month = event_month_elem.text.strip()
                    event_day = int(event_day_elem.text.strip())

                    if last_start_datetime:  # has to be before any previous events
                        if (
                            datetime.datetime.strptime(event_month, "%B").month
                            > last_start_datetime.month
                        ):
                            start_year = current_year - 1
                        else:
                            start_year = current_year
                    else:  # if no date time yet
                        # if in future and next year
                        if current_month > datetime.datetime.strptime(event_month, "%B").month:
                            start_year = current_year + 1
                        else:
                            start_year = current_year

                    event_start_datetime = datetime.datetime(
                        start_year, datetime.datetime.strptime(event_month, "%B").month, event_day
                    )

            # events are ordered from future to past, so break once we find a past event
            if event_start_datetime < now.replace(tzinfo=None):
                break

            if title := event.find("div", class_="PromoSearchResultEvent-title"):
                title = html.unescape(title.text.strip())

            if location := event.find("div", class_="PromoSearchResultEvent-eventLocation"):
                location = location.text.strip()

            if description := event.find("div", class_="PromoSearchResultEvent-description"):
                description = html.unescape(description.text.strip())

            if url := event.find("div", class_="PromoSearchResultEvent-cta").find("a", href=True):
                url = url["href"]

            Event.objects.update_or_create(
                name=title,
                defaults={
                    "event_type": Event.TYPE_VENTURE_LAB,
                    "image_url": None,
                    "start": (
                        timezone.make_aware(event_start_datetime) if event_start_datetime else None
                    ),
                    "end": timezone.make_aware(event_end_datetime) if event_end_datetime else None,
                    "location": location,
                    "website": url,
                    "description": description,
                    "email": "venturelab@upenn.edu",
                },
            )

        self.stdout.write("Uploaded Venture Lab Events!")
