import datetime

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils import timezone

from penndata.models import Event


EVENT_SITES = [
    "https://rodin.house.upenn.edu",
    "https://harrison.house.upenn.edu",
    "https://harnwell.house.upenn.edu",
    "https://gutmann.house.upenn.edu",
    "https://radian.house.upenn.edu",
    "https://lauder.house.upenn.edu",
    "https://hill.house.upenn.edu",
    "https://kcech.house.upenn.edu",
    "https://ware.house.upenn.edu",
    "https://fh.house.upenn.edu",
    "https://riepe.house.upenn.edu",
    "https://dubois.house.upenn.edu",
    "https://gregory.house.upenn.edu",
    "https://stouffer.house.upenn.edu",
]

EVENT_TYPE_MAP = {
    "rodin": Event.TYPE_RODIN_COLLEGE_HOUSE,
    "harnwell": Event.TYPE_HARNWELL_COLLEGE_HOUSE,
    "harrison": Event.TYPE_HARRISON_COLLEGE_HOUSE,
    "gutmann": Event.TYPE_GUTMANN_COLLEGE_HOUSE,
    "radian": Event.TYPE_RADIAN_COLLEGE_HOUSE,
    "lauder": Event.TYPE_LAUDER_COLLEGE_HOUSE,
    "hill": Event.TYPE_HILL_COLLEGE_HOUSE,
    "kcech": Event.TYPE_KCECH_COLLEGE_HOUSE,
    "ware": Event.TYPE_WARE_COLLEGE_HOUSE,
    "fh": Event.TYPE_FH_COLLEGE_HOUSE,
    "riepe": Event.TYPE_RIEPE_COLLEGE_HOUSE,
    "dubois": Event.TYPE_DUBOIS_COLLEGE_HOUSE,
    "gregory": Event.TYPE_GREGORY_COLLEGE_HOUSE,
    "stouffer": Event.TYPE_STOUFFER_COLLEGE_HOUSE,
}


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for site in EVENT_SITES:
            self.scrape_calendar_page(f"{site}/calendar")
        now = timezone.localtime()
        if now.day > 25:
            next = now + datetime.timedelta(days=30)
            next_month, next_year = next.month, next.year
            for site in EVENT_SITES:
                self.scrape_calendar_page(f"{site}/calendar/{next_year}-{next_month:02d}")

        self.stdout.write("Uploaded Rodin College House Events!")

    def scrape_details(self, event_url):
        try:
            resp = requests.get(event_url)
        except ConnectionError:
            print("Error:", ConnectionError)
            return None
        soup = BeautifulSoup(resp.text, "html.parser")

        location = (
            soup.select_one(".field-name-field-room").text.strip()
            if soup.select_one(".field-name-field-room")
            else ""
        )
        start_time_str = (
            soup.select_one(".date-display-start").get("content")
            if soup.select_one(".date-display-start")
            else ""
        )
        end_time_str = (
            soup.select_one(".date-display-end").get("content")
            if soup.select_one(".date-display-end")
            else ""
        )
        start_time = (
            datetime.datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M:%S%z")
            if start_time_str
            else None
        )
        end_time = (
            datetime.datetime.strptime(end_time_str, "%Y-%m-%dT%H:%M:%S%z")
            if end_time_str
            else None
        )
        description = (
            soup.select_one(".field-name-body").text.strip()
            if soup.select_one(".field-name-body")
            else ""
        )
        return location, start_time, end_time, description

    def scrape_calendar_page(self, calendar_url):
        try:
            resp = requests.get(calendar_url)
        except ConnectionError:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")

        event_cells = soup.find_all("td", class_="single-day future")

        for cell in event_cells:
            item = cell.find("div", class_="item")
            if not item:
                continue
            event_link = item.find("a", href=True)
            if not event_link:
                continue
            name = event_link.text.strip()
            url = event_link["href"]
            index = calendar_url.find("/", calendar_url.find("://") + 3)
            base_url = calendar_url[:index]
            url = f"{base_url}{url}"

            location, start_time, end_time, description = self.scrape_details(url)

            house = calendar_url.split("/")[2].split(".")[0]

            event_type = EVENT_TYPE_MAP.get(house, None)
            Event.objects.update_or_create(
                name=name,
                defaults={
                    "event_type": event_type,
                    "image_url": "",
                    "start": timezone.make_aware(start_time),
                    "end": timezone.make_aware(end_time),
                    "location": location,
                    "website": url,
                    "description": description,
                    "email": "",
                },
            )
            if start_time > timezone.localtime() + datetime.timedelta(days=30):
                break
