import calendar
import datetime

from django.utils import timezone
from django.utils.timezone import make_aware
from requests.exceptions import HTTPError
from rest_framework.response import Response
from rest_framework.views import APIView

from laundry.api_wrapper import Laundry
from laundry.models import LaundryRoom, LaundrySnapshot
from laundry.serializers import LaundrySnapshotSerializer
from user.models import Profile


laundry = Laundry()


def refresh_laundry():
    laundry.create_hall_to_link_mapping()


class Halls(APIView):
    def get(self, request):
        try:
            return Response(laundry.all_status())
        except HTTPError:
            return Response({"error": "The laundry api is currently unavailable."}, status=503)


class HallInfo(APIView):
    def get(self, request, hall_id):
        try:
            return Response(laundry.hall_status(int(hall_id)))
        except ValueError:
            return Response({"error": "Invalid hall id passed to server."}, status=404)
        except HTTPError:
            return Response({"error": "The laundry api is currently unavailable."}, status=503)


class HallUsage(APIView):

    serializer_class = LaundrySnapshotSerializer

    def safe_division(self, a, b):
        return round(a / float(b), 3) if b > 0 else 0

    def get_queryset(self, hall_id):
        now = timezone.localtime()

        # start is beginning of day, end is 27 hours after start
        start = make_aware(datetime.datetime(year=now.year, month=now.month, day=now.day))
        end = start + datetime.timedelta(hours=27)

        # filters for LaundrySnapshots within timeframe
        snapshots = LaundrySnapshot.objects.filter(hall_id=hall_id, date__gt=start, date__lte=end)

        # adds all the LaundrySnapshots from the same weekday within the previous 28 days
        for week in range(1, 4):
            # new_start is beginning of day, new_end is 27 hours after start
            new_start = start - datetime.timedelta(weeks=week)
            new_end = new_start + datetime.timedelta(hours=27)

            new_snapshots = LaundrySnapshot.objects.filter(
                hall_id=hall_id, date__gt=new_start, date__lte=new_end
            )
            snapshots = snapshots.union(new_snapshots)

        return snapshots.order_by("-date")

    def get(self, request, hall_id):

        snapshots = self.get_queryset(hall_id)

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

        # collects total washers and dryers
        try:
            total_washers = snapshots.first().total_washers
            total_dryers = snapshots.first().total_dryers
        except AttributeError:
            total_washers = 0
            total_dryers = 0

        return Response(
            {
                "hall_name": laundry.id_to_hall[int(hall_id)],
                "location": laundry.id_to_location[int(hall_id)],
                "day_of_week": calendar.day_name[timezone.localtime().weekday()],
                "start_date": min_date.date(),
                "end_date": max_date.date(),
                "washer_data": {x: self.safe_division(data[x][0], data[x][2]) for x in range(27)},
                "dryer_data": {x: self.safe_division(data[x][1], data[x][2]) for x in range(27)},
                "total_number_of_washers": total_washers,
                "total_number_of_dryers": total_dryers,
            }
        )


class Preferences(APIView):
    def get(self, request):

        # tests if user is logged-in
        if not request.user.is_authenticated:
            return Response({"rooms": []})

        preferences = Profile.objects.get(user=request.user).preferences.all()

        hall_ids = [x.hall_id for x in preferences]

        # returns all hall_ids in a person's preferences
        return Response({"rooms": hall_ids})

    def post(self, request):

        # tests if user is logged-in
        if not request.user.is_authenticated:
            return Response({"rooms": []})

        profile = Profile.objects.get(user=request.user)

        # clears all previous preferences in many-to-many
        profile.preferences.clear()

        hall_ids = request.data["rooms"]

        for hall_id in hall_ids:
            hall = LaundryRoom.objects.get(hall_id=int(hall_id))
            # adds all of the preferences given by the request
            profile.preferences.add(hall)

        profile.save()

        return Response({"detail": "success"})
