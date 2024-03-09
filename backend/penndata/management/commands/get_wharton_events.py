import datetime

import re
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils import timezone

from penndata.models import Event


WHARTON_EVENTS_WEBSITE = "https://events.wharton.upenn.edu/events-hq/#list"


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        now = timezone.localtime()

        try:
            resp = requests.get(WHARTON_EVENTS_WEBSITE)
        except ConnectionError:
            print("Error:", ConnectionError)
            return None
        
        soup = BeautifulSoup(resp.content, "html.parser")

        event_entries = soup.find_all(class_='post-entry')

        for entry in event_entries:
            title = entry.find(class_='entry-title').text.strip()
            description = entry.find('p').text.strip()
            link = entry.find(class_='entry-title').a['href']

            info = entry.find(class_='info').span.text.strip()
            match = re.match(r'(\w+\s+\d+) \| (\d{1,2}:\d{2} [AP]M) - (\d{1,2}:\d{2} [AP]M)', info)
            if match:
                _, start_time, end_time = match.groups()
                start_time_obj = datetime.datetime.strptime(start_time, '%I:%M %p')
                end_time_obj = datetime.datetime.strptime(end_time, '%I:%M %p')
            else:
                print("Error: Cannot find date, update scraper.")
                return

            location = ' '.join([info.split('•')[-2], info.split('•')[-1]])
            Event.objects.update_or_create(
                name=title,
                defaults={
                    "event_type": Event.TYPE_WHARTON,
                    "image_url": "",
                    "start": timezone.make_aware(start_time_obj),
                    "end": timezone.make_aware(end_time_obj),
                    "location": location.strip(),
                    "website": link,
                    "description": description,
                    "email": "",
                },
            )

        self.stdout.write("Uploaded Wharton Events!")