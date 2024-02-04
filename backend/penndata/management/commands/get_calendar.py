import datetime

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand

from penndata.models import CalendarEvent


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # scrapes almanac from upenn website
        try:
            resp = requests.get("https://almanac.upenn.edu/penn-academic-calendar")
        except ConnectionError:
            return None
        soup = BeautifulSoup(resp.content.decode("utf8"), "html5lib")
        # finds table with all information and gets the rows
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
        current_time = datetime.datetime.now()
        current_year = current_time.year
        row_year = 0
        # collect end dates on all events and filter based on that
        for row in rows:
            header = row.find_all("th")
            if len(header) > 0:
                row_year = header[0].get_text().split(" ")[0]
            # skips calculation if years don't align
            if int(row_year) != current_year:
                continue
            if len(header) == 0:
                data = row.find_all("td")
                date_info = data[1].get_text()
                date = None
                try:
                    # handles case for date ex. August 31
                    date = datetime.datetime.strptime(
                        date_info + str(current_year) + "-04:00", "%B %d%Y%z"
                    )
                except ValueError:
                    try:
                        # handles case for date ex. August 1-3
                        month = date_info.split(" ")[0]
                        day = date_info.split("-")[1]
                        date = datetime.datetime.strptime(
                            month + day + str(current_year) + "-04:00", "%B%d%Y%z"
                        )
                    except (ValueError, IndexError):
                        try:
                            # handles case for date ex. August 1-September 31
                            last_date = date_info.split("-")[0].split(" ")
                            month = last_date[0]
                            day = last_date[1]
                            date = datetime.datetime.strptime(
                                month + day + str(current_year) + "-04:00", "%B%d%Y%z"
                            )
                        except (ValueError, IndexError):
                            pass

                if date and current_time.replace(tzinfo=None) < date.replace(tzinfo=None) < (
                    current_time + datetime.timedelta(days=30)
                ).replace(tzinfo=None):

                    CalendarEvent.objects.get_or_create(
                        event=data[0].get_text(), date=date_info, date_obj=date
                    )

        self.stdout.write("Uploaded Calendar Events!")
