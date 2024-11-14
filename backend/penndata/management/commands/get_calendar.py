import datetime
from typing import Any

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils import timezone

from penndata.models import CalendarEvent


UPENN_ALMANAC_WEBSITE = "https://almanac.upenn.edu/penn-academic-calendar"


class Command(BaseCommand):
    def handle(self, *args: Any, **kwargs: Any) -> None:

        # Clears out previous CalendarEvents
        CalendarEvent.objects.all().delete()

        # Scrapes UPenn Almanac
        try:
            resp = requests.get(UPENN_ALMANAC_WEBSITE)
        except ConnectionError:
            return None

        soup = BeautifulSoup(resp.content.decode("utf8"), "html5lib")

        # Relevant Table class
        table = soup.find(
            "table",
            {
                "class": (
                    "table table-bordered table-striped "
                    "table-condensed table-responsive calendar-table"
                )
            },
        )

        rows = table.find_all("tr")
        current_time = timezone.localtime()
        current_year = current_time.year
        row_year = 0

        for row in rows:
            header = row.find_all("th")

            # Gets data from header
            if len(header) > 0:
                row_year = header[0].get_text().split(" ")[0]
                continue

            # Only get data from relevant year
            if int(row_year) != current_year:
                continue

            data = row.find_all("td")
            event = data[0].get_text()
            date_info = data[1].get_text()

            """
            Match works for different date types; always matches begin date:
            - Range date in same month: August 1-3
            - Range date across months: August 1-September 1
            - Single date: August 1
            """
            try:
                month = date_info.split(" ")[0]
                day = date_info.split(" ")[1].split("-")[0]
                date = datetime.datetime.strptime(
                    month + day + str(current_year) + "-04:00", "%B%d%Y%z"
                )
                if date and date >= timezone.localtime():
                    CalendarEvent.objects.get_or_create(event=event, date=date_info, date_obj=date)
            except ValueError:
                continue

        self.stdout.write("Uploaded Calendar Events!")
