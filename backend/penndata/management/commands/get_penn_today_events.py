import datetime
from typing import Any, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from django.core.management.base import BaseCommand
from django.utils import timezone
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.firefox import GeckoDriverManager

from penndata.models import Event


PENN_TODAY_WEBSITE = "https://penntoday.upenn.edu/events"
ALL_DAY = "all day"


class Command(BaseCommand):
    def handle(self, *args: Any, **kwargs: Any) -> None:
        now = timezone.localtime()
        current_month, current_year = now.month, now.year

        # Clears out previous Events
        # past_events = Event.objects.filter(end__lt=now.date())
        # past_events.delete()

        # Scrapes Penn Today
        if not (
            soup := self.connect_and_parse_html(
                PENN_TODAY_WEBSITE, EC.presence_of_element_located((By.ID, "events-list"))
            )
        ):
            return

        event_articles = soup.find_all("article", class_="tease")

        for article in event_articles:
            name = article.find("h3", class_="tease__head").text.strip()
            description = article.find("div", class_="tease__dek").text.strip()
            start_date_str = article.find("p", class_="tease__date").text.strip()
            meta_elements = article.find_all("p", class_="tease__meta--sm")
            if len(meta_elements) >= 2:
                start_time_str = meta_elements[0].text.strip().replace(".", "")
                location = meta_elements[1].text.strip()
            else:
                start_time_str = ALL_DAY
                location = None

            end_date_elem = article.find(
                "p", class_="tease__meta--sm", string=lambda x: "Through" in str(x)
            )

            start_date = self._parse_start_date(start_date_str, current_month, current_year)
            start_time = self._parse_start_time(start_time_str)
            start_datetime = datetime.datetime.combine(start_date, start_time)

            if start_datetime > now + datetime.timedelta(days=31):
                continue

            event_url = urljoin(PENN_TODAY_WEBSITE, article.find("a", class_="tease__link")["href"])
            end_time_str = self.get_end_time(event_url)
            end_datetime = self._calculate_end_datetime(end_time_str, end_date_elem, start_datetime)

            Event.objects.update_or_create(
                name=name,
                defaults={
                    "event_type": Event.TYPE_PENN_TODAY,
                    "image_url": None,
                    "start": timezone.make_aware(start_datetime),
                    "end": timezone.make_aware(end_datetime),
                    "location": location,
                    "website": event_url,
                    "description": description,
                    "email": None,
                },
            )

        self.stdout.write("Uploaded Penn Today Events!")

    def connect_and_parse_html(self, event_url: str, condition: EC) -> Optional[BeautifulSoup]:
        try:
            options = Options()
            options.add_argument("--headless")
            driver = webdriver.Firefox(
                service=FirefoxService(GeckoDriverManager().install()), options=options
            )

            driver.get(event_url)
            print("WAITING FOR ELEMENT")
            element = WebDriverWait(driver, 10).until(condition)
            print("ELEMENT FOUND")

            html_content = element.get_attribute("innerHTML")
            driver.quit()
            return BeautifulSoup(html_content, "html.parser")
        except ConnectionError:
            print("Connection Error to webdriver")
            return None

    def get_end_time(self, event_url: str) -> Optional[str]:
        end_time_soup = self.connect_and_parse_html(
            event_url, EC.presence_of_element_located((By.CLASS_NAME, "event__topper-content"))
        )

        if not end_time_soup:
            return None

        time_element = end_time_soup.find("p", class_="event__meta event__time")
        if not time_element:
            return None

        end_time_range_str = time_element.text.strip().replace(".", "")

        if (
            not end_time_range_str
            or ALL_DAY in end_time_range_str.lower()
            or len(times := end_time_range_str.split(" - ")) <= 1
        ):
            return None  # No end time if the event is all day

        return times[1]

    def _parse_start_date(
        self, date_str: str, current_month: int, current_year: int
    ) -> datetime.date:
        if date_str in ("02/29", "2/29"):
            start_date = datetime.datetime.strptime("02/28", "%m/%d").replace(year=current_year)
            if start_date.month < current_month:
                start_date = start_date.replace(year=current_year + 1)
            return (start_date + datetime.timedelta(days=1)).date()

        start_date = datetime.datetime.strptime(date_str, "%m/%d").replace(year=current_year)
        if start_date.month < current_month:
            start_date = start_date.replace(year=current_year + 1)
        return start_date.date()

    def _parse_start_time(self, time_str: str) -> datetime.time:
        if ALL_DAY in time_str.lower():
            return datetime.time(0, 0)
        return datetime.datetime.strptime(time_str, "%I:%M%p").time()

    def _calculate_end_datetime(
        self,
        end_time_str: Optional[str],
        end_date_elem: Optional[Tag],
        start_datetime: datetime.datetime,
    ) -> datetime.datetime:
        end_of_day = datetime.time(23, 59, 59)

        if end_time_str:
            end_time = datetime.datetime.strptime(end_time_str, "%I:%M %p").time()
            if end_date_elem:
                end_date_str = end_date_elem.text.strip().split(" ")[-1]
                end_date = datetime.datetime.strptime(end_date_str, "%m/%d/%Y").date()
                return datetime.datetime.combine(end_date, end_time)
            return datetime.datetime.combine(start_datetime.date(), end_time)

        if end_date_elem:
            end_date_str = end_date_elem.text.strip().split(" ")[-1]
            end_date = datetime.datetime.strptime(end_date_str, "%m/%d/%Y").date()
            return datetime.datetime.combine(end_date, end_of_day)

        return datetime.datetime.combine(start_datetime.date(), end_of_day)
