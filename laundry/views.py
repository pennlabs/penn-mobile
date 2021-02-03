from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response

from requests.exceptions import HTTPError

import datetime, calendar
from pytz import timezone

from laundry.api_wrapper import Laundry
from laundry.serializers import LaundryUsageSerializer

laundry = Laundry()


# should i just use the regular API view with a GET header?
class Halls(generics.ListAPIView):

    def list(self, request):
        try:
            return Response(laundry.all_status())
        except HTTPError:
            return Response({"error": "The laundry api is currently unavailable."})


class HallInfo(generics.ListAPIView):

    def list(self, request, hall_id):
        try:
            return Response(laundry.hall_status(int(hall_id)))
        except ValueError:
            return Response({"error": "Invalid hall id passed to server."})
        except HTTPError:
            return Response({"error": "The laundry api is currently unavailable."})


class HallUsage(generics.ListAPIView):

    serializer_class = LaundryUsageSerializer


    def list(self, request, hall_id):
        return Response()
#     serializer

# class HallUsage(generics.ListAPIView):

#     def get_queryset(self):
#         pass

#     def list(self, request, hall_id):
#         try:
#             return Response(laundry.machine_usage(int(hall_id)))
#         except ValueError:
#             return Response({"error": "Invalid hall id passed to server."})
#         except HTTPError:
#             return Response({"error": "The laundry api is currently unavailable."})


