import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from penndata.models import Event


PENN_TODAY_WEBSITE = "https://penntoday.upenn.edu/events"


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        now = datetime.datetime.now()
        current_month = now.month
        current_year = now.year

        # Clears out previous Events
        past_events = Event.objects.filter(end__lt=now.date())
        past_events.delete()

        # Scrapes Penn Today
        try:
            driver = webdriver.Chrome()

            driver.get(PENN_TODAY_WEBSITE)
            events_list = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "events-list"))
            )

            html_content = events_list.get_attribute("innerHTML")
            driver.quit()
        except ConnectionError:
            return None

        soup = BeautifulSoup(html_content, "html.parser")

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
                start_time_str = "All day"
                location = None

            end_date_elem = article.find(
                "p", class_="tease__meta--sm", string=lambda x: "Through" in str(x)
            )
            end_date = None
            if end_date_elem:
                end_date_str = end_date_elem.text.strip().split(" ")[-1]
                end_date = (
                    datetime.datetime.strptime(end_date_str, "%m/%d/%Y")
                    + datetime.timedelta(days=1)
                    - datetime.timedelta(seconds=1)
                )

            if start_date_str == "02/29" or start_date_str == "2/29":
                # If it's February 29th
                start_date = datetime.datetime.strptime("02/28", "%m/%d").replace(
                    year=current_year
                ) + datetime.timedelta(days=1)
            else:
                start_date = datetime.datetime.strptime(start_date_str, "%m/%d").replace(
                    year=current_year
                )
                if start_date.month < current_month:
                    # If scraped month is before current month, increment year
                    start_date = start_date.replace(year=current_year + 1)
            if start_time_str == "All day":
                start_time = datetime.time(0, 0)
            else:
                start_time = datetime.datetime.strptime(start_time_str, "%I:%M%p").time()
            start_date = datetime.datetime.combine(start_date, start_time)

            event_url = urljoin(PENN_TODAY_WEBSITE, article.find("a", class_="tease__link")["href"])

            Event.objects.update_or_create(
                name=name,
                defaults={
                    "event_type": "",
                    "image_url": "",
                    "start": start_date,
                    "end": end_date,
                    "location": location,
                    "website": event_url,
                    "description": description,
                    "email": "",
                    "facebook": "",
                },
            )

        self.stdout.write("Uploaded Events!")
