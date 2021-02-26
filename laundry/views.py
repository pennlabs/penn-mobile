import calendar
import datetime

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.timezone import make_aware
from requests.exceptions import HTTPError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from laundry.api_wrapper import all_status, check_is_working, hall_status
from laundry.models import LaundryRoom, LaundrySnapshot
from laundry.serializers import LaundryRoomSerializer


class Ids(APIView):
    """
    GET: returns list of all hall_ids
    """

    def get(self, request):
        return Response(LaundryRoomSerializer(LaundryRoom.objects.all(), many=True).data)


class Halls(APIView):
    """
    GET: returns list of all halls, and their respective machines and machine details
    """

    def get(self, request):
        try:
            return Response(all_status())
        except HTTPError:
            return Response({"error": "The laundry api is currently unavailable."}, status=503)


class HallInfo(APIView):
    """
    GET: returns list of a particular hall, its respective machines and machine details
    """

    def get(self, request, hall_id):
        try:
            return Response(hall_status(get_object_or_404(LaundryRoom, hall_id=hall_id)))
        except HTTPError:
            return Response({"error": "The laundry api is currently unavailable."}, status=503)


class TwoHalls(APIView):
    """
    GET: returns list of two particular halls, their respective machines and machine details
    """

    def get(self, request, hall_id1, hall_id2):
        try:
            return Response(
                {
                    "halls": [
                        hall_status(get_object_or_404(LaundryRoom, hall_id=hall_id1)),
                        hall_status(get_object_or_404(LaundryRoom, hall_id=hall_id2)),
                    ]
                }
            )
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
        now = timezone.localtime()

        # start is beginning of day, end is 27 hours after start
        start = make_aware(datetime.datetime(year=now.year, month=now.month, day=now.day))
        end = start + datetime.timedelta(hours=27)

        # filters for LaundrySnapshots within timeframe
        room = get_object_or_404(LaundryRoom, hall_id=hall_id)

        snapshots = LaundrySnapshot.objects.filter(room=room, date__gt=start, date__lte=end)

        # adds all the LaundrySnapshots from the same weekday within the previous 28 days
        for week in range(1, 4):
            # new_start is beginning of day, new_end is 27 hours after start
            new_start = start - datetime.timedelta(weeks=week)
            new_end = new_start + datetime.timedelta(hours=27)

            new_snapshots = LaundrySnapshot.objects.filter(
                room=room, date__gt=new_start, date__lte=new_end
            )
            snapshots = snapshots.union(new_snapshots)

        return (room, snapshots.order_by("-date"))

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

            if date < min_date:
                min_date = date

            if date > max_date:
                max_date = date

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
            "washer_data": {x: HallUsage.safe_division(data[x][0], data[x][2]) for x in range(27)},
            "dryer_data": {x: HallUsage.safe_division(data[x][1], data[x][2]) for x in range(27)},
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

    def get(self, request):

        preferences = request.user.profile.laundry_preferences.all()

        # returns all hall_ids in a person's preferences
        return Response({"rooms": preferences.values_list("hall_id", flat=True)})

    def post(self, request):

        profile = request.user.profile

        # clears all previous preferences in many-to-many
        profile.laundry_preferences.clear()

        hall_ids = request.data["rooms"]

        for hall_id in hall_ids:
            hall = get_object_or_404(LaundryRoom, hall_id=int(hall_id))
            # adds all of the preferences given by the request
            profile.laundry_preferences.add(hall)

        profile.save()

        return Response({"detail": "success"})


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
