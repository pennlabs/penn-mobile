import zoneinfo

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware

from penndata.models import FitnessRoom, FitnessSnapshot


def cap_string(s):
    return " ".join([word[0].upper() + word[1:] for word in s.split()])


def get_usages():
    try:
        resp = requests.get(
            "https://goboardapi.azurewebsites.net/api/FacilityCount/GetCountsByAccount",
            params={"AccountAPIKey": settings.FITNESS_TOKEN},
        )
        data = resp.json()
    except ConnectionError:
        return None
    except requests.exceptions.JSONDecodeError:
        return None

    def location_aware_datetime(time_str):
        date = parse_datetime(time_str)
        timezone = zoneinfo.ZoneInfo("America/New_York")
        return make_aware(date, timezone=timezone)

    usages = {
        location["LocationName"]: {
            "count": location["LastCount"],
            "capacity": location["TotalCapacity"],
            "last_updated": location_aware_datetime(location["LastUpdatedDateAndTime"]),
        }
        for location in data
    }
    return usages


class Command(BaseCommand):
    help = "Captures a new Fitness Snapshot for every Fitness room."

    def handle(self, *args, **kwargs):
        def exists(record):
            (name, usage) = record
            try:
                room = FitnessRoom.objects.get(name=name)
            except FitnessRoom.DoesNotExist:
                return False
            return not FitnessSnapshot.objects.filter(
                date=usage["last_updated"], room=room
            ).exists()

        # Don't update locations for which we already have a room with a matching last_updated date.
        # This is also O(n^2), idk how we feel about that chat
        usage_by_location = filter(exists, get_usages().items())
        FitnessSnapshot.objects.bulk_create(
            [
                FitnessSnapshot(
                    room=FitnessRoom.objects.get_or_create(name=room_name)[0],
                    date=room_usage["last_updated"],
                    count=room_usage["count"],
                    capacity=room_usage["capacity"],
                )
                for (room_name, room_usage) in usage_by_location
            ]
        )

        self.stdout.write("Captured fitness snapshots!")
