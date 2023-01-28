import datetime

from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from dining.api_wrapper import DiningAPIWrapper
from dining.models import DiningMenu, Venue
from dining.serializers import DiningMenuSerializer
from pennmobile.utils.time_formatter import parse_time


d = DiningAPIWrapper()


class Venues(APIView):
    """
    GET: returns list of venue data provided by Penn API, as well as an image of the venue
    """

    def get(self, request):
        return Response(d.get_venues())


class Menus(generics.ListAPIView):
    """
    GET: returns list of menus, defaulted to all objects within the week,
    and can specify the filter for a particular day
    """

    serializer_class = DiningMenuSerializer

    def get_queryset(self):
        # TODO: We only have data for the next week, so we should 404
        # if date_param is out of bounds
        if date_param := self.kwargs.get("date"):
            date = parse_time(date_param)
            return DiningMenu.objects.filter(date=date)
        else:
            start_date = timezone.now().date()
            end_date = start_date + datetime.timedelta(days=6)
            return DiningMenu.objects.filter(date__gte=start_date, date__lte=end_date)


class Preferences(APIView):
    """
    GET: returns list of a User's dining preferences
    POST: updates User dining preferences with request data
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        preferences = request.user.profile.dining_preferences

        # aggregates venues and puts it in form {"venue_id": x, "count": x}
        return Response(
            {"preferences": preferences.values("venue_id").annotate(count=Count("venue_id"))}
        )

    def post(self, request):
        profile = request.user.profile
        preferences = profile.dining_preferences
        venue_ids = request.data["venues"]

        # first check that all are valid objects
        venues = [get_object_or_404(Venue, venue_id=int(id)) for id in venue_ids]

        # clears all previous preferences associated with the profile
        preferences.clear()

        # adds all of the preferences given by the request
        preferences.add(*venues)

        return Response({"success": True, "error": None})
