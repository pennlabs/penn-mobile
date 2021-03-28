import datetime
import re

import requests
from bs4 import BeautifulSoup
from django.utils import timezone
from requests.exceptions import ConnectionError
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from penndata.models import Event
from penndata.serializers import EventSerializer


class News(APIView):
    """
    GET: Get's news article from the DP
    """

    def get_article(self):
        try:
            resp = requests.get("https://www.thedp.com/")
        except ConnectionError:
            return None

        article = {}

        html = resp.content.decode("utf8")

        soup = BeautifulSoup(html, "html5lib")

        frontpage = soup.find("div", {"class": "col-lg-6 col-md-5 col-sm-12 frontpage-carousel"})

        # adds all variables for news object
        if frontpage:
            title_html = frontpage.find("a", {"class": "frontpage-link large-link"})
        if title_html:
            article["link"] = title_html["href"]
            article["title"] = title_html.get_text()

        subtitle_html = frontpage.find("p")
        if subtitle_html:
            article["subtitle"] = subtitle_html.get_text()

        timestamp_html = frontpage.find("div", {"class": "timestamp"})
        if timestamp_html:
            article["timestamp"] = timestamp_html.get_text()

        image_html = frontpage.find("img")
        if image_html:
            article["imageurl"] = image_html["src"]

        # checks if all variables are there
        if all(v in article for v in ["title", "subtitle", "timestamp", "imageurl", "link"]):
            return article
        else:
            return None

    def get(self, request):
        article = self.get_article()
        if article:
            return Response({"article": article})
        else:
            return Response({"error": "Site could not be reached or could not be parsed."})


class Calendar(APIView):
    """
    GET: Returns upcoming university events (within 2 weeks away)
    """

    def get_events(self):
        base_url = "https://www.stanza.co/api/schedules/almanacacademiccalendar/"
        events = []
        for term in ["fall", "summer", "spring"]:
            # aggregates events based on term and year
            url = "{}{}{}term.ics".format(base_url, timezone.localtime().year, term)
            response = requests.get(url)
            response.raise_for_status()
            lines = response.text.split("\n")
            event = {}

            # adds individual events if and only if it's within 2 weeks from current day
            for line in lines:
                if line == "BEGIN:VEVENT":
                    event = {}
                elif line.startswith("DTSTART"):
                    raw_date = line.split(":")[1][0:8]
                    start_date = datetime.datetime.strptime(raw_date, "%Y%m%d").date()
                    event["start"] = start_date.strftime("%Y-%m-%d")
                elif line.startswith("DTEND"):
                    raw_date = line.split(":")[1][0:8]
                    end_date = datetime.datetime.strptime(raw_date, "%Y%m%d").date()
                    event["end"] = end_date.strftime("%Y-%m-%d")
                elif line.startswith("SUMMARY"):
                    name = line.split(":")[1]
                    event["name"] = str(name).strip()
                elif line == "END:VEVENT":
                    time_diff = (end_date - timezone.localtime().date()).total_seconds()

                    # checks for within 2 weeks
                    if time_diff > 0 and time_diff <= 1209600:
                        # simplifies text
                        event["name"] = re.split(
                            "Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday",
                            event["name"],
                        )[0].strip()
                        event["name"] = re.split(r"\($", event["name"])[0].strip()
                        event["name"] = event["name"].replace("\\", "")
                        if "Advance Registration" in event["name"]:
                            event["name"] = "Advance Registration"
                        events.append(event)

        events.sort(key=lambda d: d["start"])
        return events

    def get(self, request):
        return Response({"calendar": self.get_events()})


class Events(generics.ListAPIView):
    """
    list:
    Return a list of events belonging to the type
    """

    permission_classes = [AllowAny]
    serializer_class = EventSerializer

    def get_queryset(self):
        return Event.objects.filter(event_type=self.kwargs.get("type", ""))


class HomePage(APIView):
    """
    GET: provides homepage Cells for mobile
    """

    permission_classes = [IsAuthenticated]

    class Cell:
        def __init__(self, myType, myInfo=None, myWeight=0):
            self.type = myType
            self.info = myInfo
            self.weight = myWeight

        def getCell(self):
            return {"type": self.type, "info": self.info}

    def get(self, request):

        # NOTE: accept arguments: ?version=

        profile = request.user.profile

        # TODO: add user's GSR reservations to Response
        # TODO: add user's courses to Response
        # TODO: add GSR locations to Response
        # TODO: add features (new Penn Mobile features) to Response
        # TODO: add portal posts to Response
        # TODO: add groups_enabled for studyspaces to Response

        cells = []

        # adds laundry preference to home, defaults to Bishop if no preference
        laundry_preference = profile.laundry_preferences.first()
        if laundry_preference:
            cells.append(self.Cell("laundry", {"room_id": laundry_preference.hall_id}, 5))
        else:
            cells.append(self.Cell("laundry", {"room_id": 0}, 5))

        # adds dining preference to home with high priority, defaults to 1920's, Hill, NCH
        dining_preferences = [
            x for x in profile.dining_preferences.values_list("venue_id", flat=True)
        ]

        default_ids = [593, 1442, 636]
        if dining_preferences:
            dining_preferences.extend(default_ids)
            cells.append(self.Cell("dining", {"venues": dining_preferences[:3]}, 100))
        else:
            cells.append(self.Cell("dining", {"venues": default_ids}, 100))

        # gives an update banner if Penn Mobile needs an update
        current_version = request.GET.get("version")
        actual_version = requests.get(
            url="http://itunes.apple.com/lookup?bundleId=org.pennlabs.PennMobile"
        ).json()["results"][0]["version"]
        if current_version and current_version < actual_version:
            cells.append(self.Cell("new-version-released", None, 10000))

        # adds events up to 2 weeks
        cells.append(self.Cell("calendar", {"calendar": Calendar.get_events(self)}, 40))

        # adds front page article of DP
        cells.append(self.Cell("news", {"article": News.get_article(self)}, 50))

        # sorts by cell weight
        cells.sort(key=lambda x: x.weight, reverse=True)

        return Response({"cells": [x.getCell() for x in cells]})
