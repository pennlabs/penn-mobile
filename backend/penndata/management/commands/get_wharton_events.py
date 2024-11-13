import datetime
import re
from typing import Any, Optional

import pytz
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand

from penndata.models import Event


WHARTON_EVENTS_WEBSITE = "https://events.wharton.upenn.edu/events-hq/#list"


class Command(BaseCommand):
    def handle(self, *args: Any, **kwargs: Any) -> None:
        eastern = pytz.timezone("US/Eastern")

        try:
            resp = requests.get(WHARTON_EVENTS_WEBSITE)
        except ConnectionError:
            print("Error:", ConnectionError)
            return None
        soup = BeautifulSoup(resp.content, "html.parser")

        event_entries = soup.find_all(class_="post-entry")

        for entry in event_entries:
            title = entry.find(class_="entry-title").text.strip()
            description = entry.find("p").text.strip()
            link = entry.find(class_="entry-title").a["href"]

            info = entry.find(class_="info").span.text.strip()
            # event has start and end times on same date
            match = re.match(r"(\w+\s+\d+) \| (\d{1,2}:\d{2} [AP]M) - (\d{1,2}:\d{2} [AP]M)", info)
            if match:
                _, start_time, end_time = match.groups()
                start_time_obj: Optional[datetime.datetime] = datetime.datetime.strptime(
                    start_time, "%I:%M %p"
                )
                end_time_obj: Optional[datetime.datetime] = datetime.datetime.strptime(
                    end_time, "%I:%M %p"
                )
            else:
                # event has start and end times on different dates
                match = re.match(
                    r"(\w+\s+\d+)(?: \| (\d{1,2}:\d{2} [AP]M))?"
                    r"(?: - (\w+\s+\d+ \| )?(\d{1,2}:\d{2} [AP]M))?",
                    info,
                )
                if match:
                    start_date, start_time, end_date, end_time = match.groups()
                    start_time_obj = (
                        datetime.datetime.strptime(start_time, "%I:%M %p") if start_time else None
                    )
                    end_time_obj = (
                        datetime.datetime.strptime(end_time, "%I:%M %p") if end_time else None
                    )
                else:
                    print("Error: Cannot find date, update scraper.")
                    return
            location = ",".join(info.split("•")[-2:])
            Event.objects.update_or_create(
                name=title,
                defaults={
                    "event_type": Event.TYPE_WHARTON,
                    "image_url": None,
                    "start": eastern.localize(start_time_obj) if start_time_obj else None,
                    "end": eastern.localize(end_time_obj) if end_time_obj else None,
                    "location": location.strip(),
                    "website": link,
                    "description": description,
                    "email": None,
                },
            )

        self.stdout.write("Uploaded Wharton Events!")
