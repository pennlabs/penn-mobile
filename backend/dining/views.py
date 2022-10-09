import datetime

from django.utils import timezone
from django.utils.timezone import make_aware
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from dining.api_wrapper import DiningAPIWrapper
from dining.models import DiningMenu
from dining.serializers import DiningMenuSerializer


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
            date = make_aware(datetime.datetime.strptime(date_param, "%Y-%m-%d"))
            return DiningMenu.objects.filter(date=date)
        else:
            start_date = timezone.now().date()
            end_date = start_date + datetime.timedelta(days=6)
            return DiningMenu.objects.filter(date__gte=start_date, date__lte=end_date)
