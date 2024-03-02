import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils import timezone
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from penndata.models import Event


PENN_TODAY_WEBSITE = "https://penntoday.upenn.edu/events"
ALL_DAY = "all day"


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        now = timezone.localtime()
        current_month, current_year = now.month, now.year

        # Clears out previous Events
        # past_events = Event.objects.filter(end__lt=now.date())
        # past_events.delete()

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
                start_time_str = ALL_DAY
                location = None

            end_date_elem = article.find(
                "p", class_="tease__meta--sm", string=lambda x: "Through" in str(x)
            )

            if start_date_str == "02/29" or start_date_str == "2/29":
                # If it's February 29th
                start_date = datetime.datetime.strptime("02/28", "%m/%d").replace(year=current_year)
                if start_date.month < current_month:
                    # If scraped month is before current month, increment year
                    start_date = start_date.replace(year=current_year + 1)
                start_date = start_date + datetime.timedelta(days=1)
            else:
                start_date = datetime.datetime.strptime(start_date_str, "%m/%d").replace(
                    year=current_year
                )
                if start_date.month < current_month:
                    # If scraped month is before current month, increment year
                    start_date = start_date.replace(year=current_year + 1)
            if start_time_str == ALL_DAY:
                start_time = datetime.time(0, 0)
            else:
                start_time = datetime.datetime.strptime(start_time_str, "%I:%M%p").time()
            start_date = datetime.datetime.combine(start_date, start_time)

            event_url = urljoin(PENN_TODAY_WEBSITE, article.find("a", class_="tease__link")["href"])

            end_time = self.get_end_time(event_url)
            if end_time is not None:
                if end_date_elem:  # end date and end time
                    end_date_str = end_date_elem.text.strip().split(" ")[-1]
                    end_date = datetime.datetime.strptime(end_date_str, "%m/%d/%Y")
                    end_time = datetime.datetime.strptime(end_time, "%I:%M %p").time()
                    end_date = datetime.datetime.combine(end_date, end_time)
                else:  # no end date but end time
                    end_time = datetime.datetime.strptime(end_time, "%I:%M %p").time()
                    end_date = datetime.datetime.combine(start_date, end_time)
            else:
                end_of_day = datetime.time(23, 59, 59)
                if end_date_elem:  # end date but no end time
                    end_date_str = end_date_elem.text.strip().split(" ")[-1]
                    end_date = datetime.combine(
                        datetime.datetime.strptime(end_date_str, "%m/%d/%Y"), end_of_day
                    )
                else:  # no end date or end time
                    end_date = datetime.combine(start_date, end_of_day)

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
                },
            )

        self.stdout.write("Uploaded Events!")

    def get_end_time(self, event_url):
        driver = webdriver.Chrome()
        driver.get(event_url)
        event_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "event__topper-content"))
        )
        end_time_soup = BeautifulSoup(event_element.get_attribute("innerHTML"), "html.parser")

        end_time_range_str = (
            end_time_soup.find("p", class_="event__meta event__time").text.strip().replace(".", "")
        )
        print(end_time_range_str)
        if not end_time_range_str or ALL_DAY in end_time_range_str.lower():
            driver.quit()
            return None  # No end time if the event is all day
        times = end_time_range_str.split(" - ")
        if len(times) <= 1:
            driver.quit()
            return None
        end_time_str = times[1]
        driver.quit()
        return end_time_str
