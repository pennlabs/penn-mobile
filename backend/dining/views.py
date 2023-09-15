import datetime

from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.timezone import make_aware
from backend.utils.cache import MONTH_IN_SECONDS_APPROX
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.cache import cache

from dining.api_wrapper import APIError, DiningAPIWrapper
from dining.models import DiningMenu, Venue
from dining.serializers import DiningMenuSerializer


d = DiningAPIWrapper()


class Venues(APIView):
    """
    GET: returns list of venue data provided by Penn API, as well as an image of the venue
    """

    def get(self, request):
        try:
            return Response(d.get_venues())
        except APIError as e:
            return Response({"error": str(e)}, status=400)


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
            date = make_aware(datetime.datetime.strptime(date_param, "%Y-%m-%d"))
            return DiningMenu.objects.filter(date=date)
        else:
            start_date = timezone.now().date()
            end_date = start_date + datetime.timedelta(days=6)
            return DiningMenu.objects.filter(date__gte=start_date, date__lte=end_date)


class Preferences(APIView):
    """
    GET: returns list of a User's diningpreferences
    POST: updates User dining preferences by clearing past preferences
    and resetting them with request data
    """

    permission_classes = [IsAuthenticated]
    key_prefix = "dining_preferences"

    def get(self, request):
        preferences = request.user.profile.dining_preferences
        key = f"{self.key_prefix}:{request.user.id}"
        cached_preferences = cache.get(key)
        if cached_preferences is None:
            cached_preferences = (
                preferences.all().values("venue_id").annotate(count=Count("venue_id"))
            )
            cache.set(key, cached_preferences, MONTH_IN_SECONDS_APPROX)
        return Response({"preferences": cached_preferences})

    def post(self, request):
        profile = request.user.profile
        preferences = profile.dining_preferences

        if "venues" not in request.data:
            return Response(
                {"success": False, "error": "No venues provided"}, status=400
            )

        venues = [
            get_object_or_404(Venue, venue_id=int(venue_id))
            for venue_id in request.data["venues"]
        ]

        # clears all previous preferences associated with the profile
        preferences.clear()
        preferences.add(*venues)

        # clear cache
        cache.delete(f"{self.key_prefix}:{request.user.id}")
        
        return Response({"success": True, "error": None})
