import datetime
from datetime import timedelta

import requests
from analytics.entries import ViewEntry
from bs4 import BeautifulSoup
from django.shortcuts import get_object_or_404
from django.utils import timezone
from requests.exceptions import ConnectionError
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from laundry.models import LaundryRoom
from penndata.models import (
    AnalyticsEvent,
    CalendarEvent,
    Event,
    FitnessRoom,
    FitnessSnapshot,
    HomePageOrder,
)
from penndata.serializers import (
    AnalyticsEventSerializer,
    CalendarEventSerializer,
    EventSerializer,
    FitnessRoomSerializer,
    HomePageOrderSerializer,
)
from pennmobile.analytics import LabsAnalytics


class News(APIView):
    """
    GET: Get's news article from the DP
    """

    def get_article(self):
        article = {"source": "The Daily Pennsylvanian"}
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
            }
            resp = requests.get("https://www.thedp.com/", headers=headers)
        except ConnectionError:
            return None

        html = resp.content.decode("utf8")

        soup = BeautifulSoup(html, "html5lib")

        if not (
            frontpage := soup.find(
                "div", {"class": "col-lg-6 col-md-5 col-sm-12 frontpage-carousel"}
            )
        ):
            return None

        # adds all variables for news object
        if not (title_html := frontpage.find("a", {"class": "frontpage-link large-link"})):
            return None
        article["link"] = title_html["href"]
        article["title"] = title_html.get_text()

        subtitle_html = frontpage.find("p")
        if subtitle_html:
            article["subtitle"] = subtitle_html.get_text()

        timestamp_html = frontpage.find("div", {"class": "timestamp"})
        if timestamp_html:
            article["timestamp"] = timestamp_html.get_text().strip()

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


class Calendar(generics.ListAPIView):
    """
    list: Returns upcoming university events (within 2 weeks away)
    """

    permission_classes = [AllowAny]
    serializer_class = CalendarEventSerializer

    def get_queryset(self):
        return CalendarEvent.objects.filter(
            date_obj__gte=timezone.localtime(),
            date_obj__lte=timezone.localtime() + timedelta(days=30),
        )


class Events(generics.ListAPIView):
    """
    list:
    Return a list of events belonging to the type
    """

    permission_classes = [AllowAny]
    serializer_class = EventSerializer

    def get_queryset(self):
        queryset = Event.objects.all()

        event_type = self.kwargs.get("type")
        if event_type:
            queryset = queryset.filter(event_type=event_type)

        queryset = queryset.filter(
            end__gte=timezone.localtime(), start__lte=timezone.localtime() + timedelta(days=30)
        )
        return queryset


class Analytics(generics.CreateAPIView):

    permission_classes = [IsAuthenticated]
    serializer_class = AnalyticsEventSerializer


class HomePageOrdering(generics.ListAPIView):
    """
    list:
    Return a list of orderings for homepage
    """

    permission_classes = [AllowAny]
    serializer_class = HomePageOrderSerializer

    def get_queryset(self):
        return HomePageOrder.objects.all()


# Tracks the time user opens up Penn Mobile homepage
@LabsAnalytics.record_apiview(
    ViewEntry(name="homepage_visit_time", get_value=lambda req, res: timezone.localtime())
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

        # adds laundry preference to home, defaults to 0 if no preference
        # TODO: This defaults to the first room, change potentially
        laundry_preference = profile.laundry_preferences.first()
        if laundry_preference:
            cells.append(self.Cell("laundry", {"room_id": laundry_preference.room_id}, 5))
        else:
            cells.append(
                self.Cell("laundry", {"room_id": list(LaundryRoom.objects.all())[0].room_id}, 5)
            )

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
        # cells.append(self.Cell("calendar", {"calendar": Calendar.get_calendar(self)}, 40))

        # adds front page article of DP
        cells.append(self.Cell("news", {"article": News.get_article(self)}, 50))

        # sorts by cell weight
        cells.sort(key=lambda x: x.weight, reverse=True)

        return Response({"cells": [x.getCell() for x in cells]})


class FitnessRoomView(generics.ListAPIView):
    """
    GET: Get Fitness Usage
    """

    queryset = FitnessRoom.objects.all()
    serializer_class = FitnessRoomSerializer

    open_times = {
        0: (6, 23.5),
        1: (6, 23.5),
        2: (6, 23.5),
        3: (6, 23.5),
        4: (6, 22),
        5: (8, 22),
        6: (9, 22),
    }

    def get(self, request):
        response = super().get(self, request)
        # also add last_updated and open/close times to each room in response
        for room in response.data:
            ss = FitnessSnapshot.objects.filter(room__id=room["id"]).order_by("-date").first()
            room["last_updated"] = timezone.localtime(ss.date) if ss else None
            room["count"] = getattr(ss, "count", None)
            room["capacity"] = getattr(ss, "capacity", None)

            room["open"] = [
                datetime.time(hour=int(hours), minute=int((hours % 1) * 60))
                for hours, _ in self.open_times.values()
            ]
            room["close"] = [
                datetime.time(hour=int(hours), minute=int((hours % 1) * 60))
                for _, hours in self.open_times.values()
            ]
        return response


class FitnessUsage(APIView):
    def safe_add(self, a, b):
        return None if a is None and b is None else (a or 0) + (b or 0)

    def linear_interpolate(self, before_val, after_val, before_date, current_date, after_date):
        return (
            before_val
            + (after_val - before_val)
            * (current_date - before_date).total_seconds()
            / (after_date - before_date).total_seconds()
        )

    def get_usage_on_date(self, room, date, field):
        """
        Returns the number of people in the fitness center on a given date per hour
        """

        # Rounded closing times down
        # TODO: get the API for accurate open and close times

        open, close = FitnessRoomView.open_times[date.weekday()]
        open, close = int(open), int(close)

        # get all snapshots for a given room on a given date and the days before and after
        snapshots = FitnessSnapshot.objects.filter(room=room, date__date=date)

        # For usage, None represents no data
        usage = [0] * 24
        for hour in range(open, close + 1):
            # consider the :30 mark of each hour
            hour_date = timezone.make_aware(datetime.datetime.combine(date, datetime.time(hour)))

            # use snapshots before and after the hour_date to interpolate
            before = snapshots.filter(date__lte=hour_date).order_by("-date").first()
            after = snapshots.filter(date__gte=hour_date).order_by("date").first()

            before_date, before_val = getattr(before, "date", None), getattr(before, field, None)
            after_date, after_val = getattr(after, "date", None), getattr(after, field, None)

            # This condition should only activate during morning times
            if before is None:
                before_date, before_val = (
                    timezone.make_aware(datetime.datetime.combine(date, datetime.time(open))),
                    0,
                )

            # This can happen either on the current day or at last entries of other days
            if after is None:
                if date == timezone.localtime().date():
                    # Set value to None if the last retrieved data was
                    # over 2 hours old to avoid extrapolation
                    if hour_date - datetime.timedelta(hours=1) > before_date:
                        for i in range(hour, 24):
                            usage[i] = None
                        break
                    else:
                        after_date, after_val = timezone.localtime(), before_val
                else:
                    after_date, after_val = (
                        timezone.make_aware(datetime.datetime.combine(date, datetime.time(close)))
                        + datetime.timedelta(minutes=30),
                        0,
                    )

            usage[hour] = (
                self.linear_interpolate(before_val, after_val, before_date, hour_date, after_date)
                if before_date != after_date
                else after_val
            )
        if all(amt == 0 for amt in usage):  # location probably closed - don't count in aggregate
            return [None] * 24
        return usage

    def get_usage(self, room, date, num_samples, group_by, field):
        unit = 1 if group_by == "day" else 7  # skip by 1 or 7 days
        usage_aggs = [(None, 0)] * 24  # (sum, count) for each hour
        min_date = timezone.localtime().date()
        max_date = date - datetime.timedelta(days=unit * (num_samples - 1))

        for i in range(num_samples):
            curr = date - datetime.timedelta(days=i * unit)
            usage = self.get_usage_on_date(room, curr, field)  # usage for curr
            # incorporate usage safely considering None (no data) values
            usage_aggs = [
                (self.safe_add(sum, val), count + (1 if val is not None else 0))
                for (sum, count), val in zip(usage_aggs, usage)
            ]
            # update min and max date if any data was logged
            if any(usage):
                min_date = min(min_date, curr)
                max_date = max(max_date, curr)
        ret = [(sum / count) if count else None for (sum, count) in usage_aggs]
        return ret, min_date, max_date

    def get(self, request, room_id):
        """
        GET: returns the usage in terms of count or capacity of a fitness center for a given date
        per hour aggregated by day or week for a given number of days
        """

        room = get_object_or_404(FitnessRoom, pk=room_id)
        try:
            date_param = request.query_params.get("date")
            date = (
                timezone.make_aware(datetime.datetime.strptime(date_param, "%Y-%m-%d")).date()
                if date_param
                else timezone.localtime().date()
            )
        except ValueError:
            return Response({"detail": "date must be in the format YYYY-MM-DD"}, status=400)
        try:
            num_samples = int(request.query_params.get("num_samples", 1))
        except ValueError:
            return Response({"detail": "num_samples must be an integer"}, status=400)

        if (group_by := request.query_params.get("group_by", "day")) not in ("day", "week"):
            return Response({"detail": "group_by must be either 'day' or 'week'"}, status=400)

        if (field := request.query_params.get("field", "count")) not in ("count", "capacity"):
            return Response({"detail": "field must be either 'count' or 'capacity'"}, status=400)

        usage_per_hour, min_date, max_date = self.get_usage(
            room, date, num_samples, group_by, field
        )
        return Response(
            {
                "room_name": room.name,
                "start_date": min_date,
                "end_date": max_date,
                "usage": {i: amt for i, amt in enumerate(usage_per_hour)},
            }
        )


class FitnessPreferences(APIView):
    """
    GET: returns list of a User's fitness preferences

    POST: updates User fitness preferences by clearing past preferences
    and resetting them with request data
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):

        preferences = request.user.profile.fitness_preferences.all()

        # returns all ids in a person's preferences
        return Response({"rooms": preferences.values_list("id", flat=True)})

    def post(self, request):

        if "rooms" not in request.data:
            return Response({"success": False, "error": "No rooms provided"})

        profile = request.user.profile

        ids = request.data["rooms"]

        halls = [get_object_or_404(FitnessRoom, id=int(id)) for id in ids]

        # clears all previous preferences in many-to-many
        profile.fitness_preferences.clear()

        # adds all of the preferences given by the request
        profile.fitness_preferences.add(*halls)

        profile.save()

        return Response({"success": True, "error": None})


class UniqueCounterView(APIView):
    """
    get: determines number of unique visits for a given post or poll
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = dict()
        if "post_id" in request.query_params:
            query["post__id"] = request.query_params["post_id"]
        if "poll_id" in request.query_params:
            query["poll__id"] = request.query_params["poll_id"]
        if len(query) != 1:
            return Response({"detail": "require 1 id out of post_id or poll_id"}, status=400)
        query["is_interaction"] = (
            request.query_params.get("is_interaction", "false").lower() == "true"
        )
        return Response({"count": AnalyticsEvent.objects.filter(**query).count()})
