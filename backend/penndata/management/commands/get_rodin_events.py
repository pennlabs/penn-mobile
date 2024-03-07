import datetime

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils import timezone

from penndata.models import Event


RODIN_EVENTS_WEBSITE = "https://rodin.house.upenn.edu"


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        self.scrape_calendar_page(f"{RODIN_EVENTS_WEBSITE}/calendar")
        now = timezone.localtime()
        current_day, current_month, current_year = now.day, now.month, now.year
        if current_day > 25:
            next = now + datetime.timedelta(months=1)
            next_month, next_year = next.month, next.year
            next_month_url = f"{RODIN_EVENTS_WEBSITE}/calendar/{next_year}-{next_month:02d}"
            self.scrape_calendar_page(next_month_url)

        self.stdout.write("Uploaded Rodin College House Events!")

    def scrape_details(self, event_url):
        try:
            resp = requests.get(event_url)
        except ConnectionError:
            print("Error:", ConnectionError)
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
            url = f"{RODIN_EVENTS_WEBSITE}{url}"

            location, start_time, end_time, description = self.scrape_details(url)
            Event.objects.update_or_create(
                name=name,
                defaults={
                    "event_type": Event.TYPE_RODIN_COLLEGE_HOUSE,
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
