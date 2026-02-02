import zoneinfo

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware

from penndata.models import FitnessRoom, FitnessSnapshot


def cap_string(s):
    return " ".join([word[0].upper() + word[1:] for word in s.split()])


def get_usages():
    try:

        session = requests.Session()

        url = "https://goboardapi.azurewebsites.net/api/FacilityCount/GetCountsByAccount"

        params = {"AccountAPIKey": settings.FITNESS_TOKEN}

        headers = {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://www.connect2mycloud.com",
            "Host": "goboardapi.azurewebsites.net",
            "Referer": "https://www.connect2mycloud.com/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            + "(KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        }
        session.get(url, params=params, headers=headers)
        resp2 = session.get(url, params=params, headers=headers)
        data = resp2.json()
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
        # Don't update locations for which we already have a room with a matching last_updated date.
        # Fixed the O(n^2) issue by loading everything into memory. Should be fine since there's
        # not many rooms, and 1 snapshot returned per room
        all_rooms = FitnessRoom.objects.all()
        all_room_names = set(room.name for room in all_rooms)
        query = Q()
        for room_name, room_usage in get_usages().items():
            query |= Q(room__name=room_name, date=room_usage["last_updated"])
        existing_snapshots = FitnessSnapshot.objects.filter(query)
        existing_room_date_pairs = set(
            (snapshot.room.name, snapshot.date) for snapshot in existing_snapshots
        )

        def exists(record):
            (name, usage) = record
            if name not in all_room_names:
                return False
            if (name, usage["last_updated"]) in existing_room_date_pairs:
                return False
            return True

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
