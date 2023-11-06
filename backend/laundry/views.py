import calendar
import datetime

from django.core.cache import cache
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from requests.exceptions import HTTPError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from laundry.api_wrapper import check_is_working, hall_status
from laundry.models import LaundryRoom, LaundrySnapshot
from laundry.serializers import LaundryRoomSerializer
from utils.cache import Cache


class Ids(APIView):
    """
    GET: returns list of all hall_ids
    """

    def get(self, request):
        return Response(LaundryRoomSerializer(LaundryRoom.objects.all(), many=True).data)


class HallInfo(APIView):
    """
    GET: returns list of a particular hall, its respective machines and machine details
    """

    def get(self, request, hall_id):
        try:
            return Response(hall_status(get_object_or_404(LaundryRoom, hall_id=hall_id)))
        except HTTPError:
            return Response({"error": "The laundry api is currently unavailable."}, status=503)


class MultipleHallInfo(APIView):
    """
    GET: returns list of hall information as well as hall usage
    """

    def get(self, request, hall_ids):
        halls = [int(x) for x in hall_ids.split(",")]
        output = {"rooms": []}

        for hall_id in halls:
            hall_data = hall_status(get_object_or_404(LaundryRoom, hall_id=hall_id))
            hall_data["id"] = hall_id
            hall_data["usage_data"] = HallUsage.compute_usage(hall_id)
            output["rooms"].append(hall_data)

        return Response(output)


class HallUsage(APIView):
    """
    GET: returns usage data for dryers and washers of a particular hall
    """

    def safe_division(a, b):
        return round(a / float(b), 3) if b > 0 else 0

    def get_snapshot_info(hall_id):
        # filters for LaundrySnapshots within timeframe
        room = get_object_or_404(LaundryRoom, hall_id=hall_id)

        # get start time, which is now without the times
        start = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)

        # adds all the LaundrySnapshots from the same weekday within the previous 28 days
        filter = Q(room=room)
        for week in range(4):
            new_start = start - datetime.timedelta(weeks=week)
            new_end = new_start + datetime.timedelta(hours=27)
            filter |= Q(date__gt=new_start, date__lt=new_end)

        snapshots = LaundrySnapshot.objects.filter(filter).order_by("-date")
        return (room, snapshots)

    def compute_usage(hall_id):
        try:
            (room, snapshots) = HallUsage.get_snapshot_info(hall_id)
        except ValueError:
            return Response({"error": "Invalid hall id passed to server."}, status=404)

        # [0]: available washers, [1]: available dryers, [2]: total number of LaundrySnapshots
        data = [(0, 0, 0)] * 27

        # used calculate the start and end dates
        min_date = timezone.localtime()
        max_date = timezone.localtime() - datetime.timedelta(days=30)

        for snapshot in snapshots:
            date = snapshot.date.astimezone()
            min_date = min(min_date, date)
            max_date = max(max_date, date)
            hour = date.hour

            # accounts for the 3 hours on the next day
            if (
                calendar.day_name[timezone.localtime().weekday()]
                == calendar.day_name[(date - datetime.timedelta(days=1)).weekday()]
            ):
                hour = date.hour + 24

            # adds total number of available washers and dryers
            data[hour] = (
                data[hour][0] + snapshot.available_washers,
                data[hour][1] + snapshot.available_dryers,
                data[hour][2] + 1,
            )

        content = {
            "hall_name": room.name,
            "location": room.location,
            "day_of_week": calendar.day_name[timezone.localtime().weekday()],
            "start_date": min_date.date(),
            "end_date": max_date.date(),
            "washer_data": {
                x: HallUsage.safe_division(data[x][0], data[x][2]) for x in range(len(data))
            },
            "dryer_data": {
                x: HallUsage.safe_division(data[x][1], data[x][2]) for x in range(len(data))
            },
            "total_number_of_washers": room.total_washers,
            "total_number_of_dryers": room.total_dryers,
        }

        return content

    def get(self, request, hall_id):
        return Response(HallUsage.compute_usage(hall_id))


class Preferences(APIView):
    """
    GET: returns list of a User's laundry preferences

    POST: updates User laundry preferences by clearing past preferences
    and resetting them with request data
    """

    permission_classes = [IsAuthenticated]
    key = "laundry_preferences:{user_id}"

    def get(self, request):
        key = self.key.format(user_id=request.user.id)
        cached_preferences = cache.get(key)
        if cached_preferences is None:
            preferences = request.user.profile.laundry_preferences.all()
            cached_preferences = preferences.values_list("hall_id", flat=True)
            cache.set(key, cached_preferences, Cache.MONTH)

        return Response({"rooms": cached_preferences})

    def post(self, request):
        key = self.key.format(user_id=request.user.id)
        profile = request.user.profile
        preferences = profile.laundry_preferences

        if "rooms" not in request.data:
            return Response({"success": False, "error": "No rooms provided"}, status=400)

        halls = [
            get_object_or_404(LaundryRoom, hall_id=int(hall_id))
            for hall_id in request.data["rooms"]
        ]

        # clears all previous preferences in many-to-many
        preferences.clear()
        preferences.add(*halls)

        # clear cache
        cache.delete(key)

        return Response({"success": True, "error": None})


class Status(APIView):
    """
    GET: returns Response according to whether or not Penn Laundry API is working or not
    """

    def get(self, request):
        if check_is_working():
            return Response({"is_working": True, "error_msg": None})
        else:
            error_msg = (
                "Penn's laundry server is currently not updating. "
                + "We hope this will be fixed shortly."
            )
            return Response({"is_working": False, "error_msg": error_msg})
