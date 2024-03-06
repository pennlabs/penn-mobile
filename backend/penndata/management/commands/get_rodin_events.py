import datetime

import requests
from bs4 import BeautifulSoup

from django.core.management.base import BaseCommand
from django.utils import timezone

from penndata.models import Event


RODIN_EVENTS_WEBSITE = "https://rodin.house.upenn.edu"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Apple" +
    "WebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        self.scrape_calendar_page(RODIN_EVENTS_WEBSITE + "/calendar")
        now = timezone.localtime()
        current_day, current_month, current_year = now.day, now.month, now.year
        if current_day > 25:
            next_month_year = current_year if current_month < 12 else current_year + 1
            next_month = current_month + 1 if current_month < 12 else 1
            next_month_url = f"{RODIN_EVENTS_WEBSITE}/calendar/{next_month_year}-{next_month:02d}"
            self.scrape_calendar_page(next_month_url)

        self.stdout.write("Uploaded Rodin College House Events!")

    def scrape_details(self, event_url):
        try:
            resp = requests.get(event_url, headers=HEADERS)
        except ConnectionError:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")

        location = soup.select_one(".field-name-field-room").text.strip() if soup.select_one(
            ".field-name-field-room") else ""
        start_time_str = soup.select_one(".date-display-start").get("content") if soup.select_one(
            ".date-display-start") else ""
        end_time_str = soup.select_one(
            ".date-display-end").get("content") if soup.select_one(".date-display-end") else ""
        start_time = datetime.datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M:%S%z"
                                                ) if start_time_str else None
        end_time = datetime.datetime.strptime(end_time_str, "%Y-%m-%dT%H:%M:%S%z"
                                              ) if end_time_str else None
        description = soup.select_one(
            ".field-name-body").text.strip() if soup.select_one(".field-name-body") else ""
        return location, start_time, end_time, description

    def scrape_calendar_page(self, calendar_url):
        try:
            resp = requests.get(calendar_url, headers=HEADERS)
        except ConnectionError:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")

        event_cells = soup.find_all("td", class_="single-day future")

        for cell in event_cells:
            item = cell.find("div", class_="item")
            if item:
                event_link = item.find("a", href=True)
                if event_link:
                    name = event_link.text.strip()
                    url = RODIN_EVENTS_WEBSITE + event_link["href"]

                    location, start_time, end_time, description = self.scrape_details(url)
                    print("Location:", location)
                    print("Start Time:", start_time)
                    print("End Time:", end_time)
                    print("Description:", description)
                    Event.objects.update_or_create(
                        name=name,
                        defaults={
                            "event_type": "Rodin College House",
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
