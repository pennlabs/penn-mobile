import datetime

import requests
from bs4 import BeautifulSoup
from django.utils import timezone
from requests.exceptions import ConnectionError
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from gsr_booking.models import GSR, GSRBooking
from gsr_booking.serializers import GSRSerializer
from penndata.models import Event
from penndata.serializers import EventSerializer


class News(APIView):
    """
    GET: Get's news article from the DP
    """

    def get_article(self):
        article = {"source": "The Daily Pennsylvanian"}
        try:
            resp = requests.get("https://www.thedp.com/")
        except ConnectionError:
            return None

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
            timestamp = datetime.datetime.strptime(
                timestamp_html.get_text().strip(), "%m/%d/%y %I:%M%p"
            )
            article["timestamp"] = timestamp.isoformat()

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
            return Response(article)
        else:
            return Response({"error": "Site could not be reached or could not be parsed."})


class Calendar(APIView):
    """
    GET: Returns upcoming university events (within 2 weeks away)
    """

    def get_calendar(self):
        # scapes almanac from upenn website
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
        calendar = []
        current_year = timezone.localtime().year
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

                # TODO: add this: and date < timezone.localtime() + datetime.timedelta(days=14)
                if date and date > timezone.localtime():
                    calendar.append({"event": data[0].get_text(), "date": date.isoformat()})
                # only returns the 3 most recent events
                if len(calendar) == 3:
                    break
        return calendar

    def get(self, request):
        return Response({"calendar": self.get_calendar()})


class Events(generics.ListAPIView):
    """
    list:
    Return a list of events belonging to the type
    """

    permission_classes = [AllowAny]
    serializer_class = EventSerializer

    def get_queryset(self):
        return Event.objects.filter(event_type=self.kwargs.get("type", ""))


class GSRView(generics.ListAPIView):
    """Gets list of two most recent rooms booked by User"""

    permission_classes = [IsAuthenticated]
    serializer_class = GSRSerializer

    def get_queryset(self):
        return GSR.objects.filter(
            id__in=list(
                GSRBooking.objects.filter(user=self.request.user, is_cancelled=False)
                .order_by("-end")
                .values_list("gsr", flat=True)
            )[:2]
        )


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
