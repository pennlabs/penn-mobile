import csv

from django.conf import settings
from django.core.management.base import BaseCommand

from laundry.api_wrapper import get_validated


def write_file(laundry_rooms):
    with open("laundry/data/laundry_data.csv", "w") as f:
        writer = csv.DictWriter(f, laundry_rooms[0].keys())
        writer.writeheader()
        writer.writerows(laundry_rooms)


class Command(BaseCommand):
    help = "Update laundry rooms csv from server"

    def handle(self, *args, **kwargs):
        # Pull initial request with everything
        all_rooms_request_json = get_validated(
            f"{settings.LAUNDRY_URL}/geoBoundaries/5610?raw=true"
        )
        if all_rooms_request_json is None:
            return
        locations = all_rooms_request_json["geoBoundaries"][0]["geoBoundaries"]

        laundry_rooms = [
            {
                "room_id": int(room["id"]),
                "room_name": room["roomName"],
                "room_description": location["description"],
                "room_location": int(location["id"]),
            }
            for location in locations
            for room in location["rooms"]
        ]

        # for each room, send a request to find number of washers and dryers
        # TODO: This is really inefficient, but may require change in frontend code to update
        for room in laundry_rooms:
            room_request_json = get_validated(
                f"{settings.LAUNDRY_URL}/rooms/{room['room_id']}/machines?raw=true"
            )
            if room_request_json is None:
                return
            # count washers and dryers
            count_washers = 0
            count_dryers = 0
            for machine in room_request_json:
                if machine["isWasher"]:
                    count_washers += 1
                if machine["isDryer"]:
                    count_dryers += 1
            room["count_washers"] = count_washers
            room["count_dryers"] = count_dryers

        write_file(laundry_rooms)
