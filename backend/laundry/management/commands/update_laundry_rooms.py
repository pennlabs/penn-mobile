import csv

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from requests.exceptions import HTTPError


def write_file(laundry_rooms):
    with open("laundry/data/laundry_data.csv", "w") as f:
        writer = csv.DictWriter(f, laundry_rooms[0].keys())
        writer.writeheader()
        writer.writerows(laundry_rooms)


class Command(BaseCommand):
    help = "Update laundry rooms csv from server"

    def handle(self, *args, **kwargs):
        # Pull initial request with everything
        try:
            headers = {
                "x-api-key": settings.LAUNDRY_X_API_KEY,
                "alliancels-auth-token": settings.LAUNDRY_ALLIANCELS_API_KEY,
            }
            all_rooms_request = requests.get(
                f"{settings.LAUNDRY_URL}/geoBoundaries/5610?raw=true", timeout=60, headers=headers
            )
            all_rooms_request.raise_for_status()

        except HTTPError as e:
            self.stdout.write(f"Error: {e}")
            return

        all_rooms_request_json = all_rooms_request.json()
        locations = all_rooms_request_json["geoBoundaries"][0]["geoBoundaries"]

        laundry_rooms = [
            {
                "room_id": room["id"],
                "room_name": room["roomName"],
                "room_description": location["description"],
                "room_location": location["id"],
            }
            for location in locations
            for room in location["rooms"]
        ]

        # for each room, send a request to find number of washers and dryers
        # TODO: This is really inefficient, but may require change in frontend code to update
        for room in laundry_rooms:
            try:
                room_request = requests.get(
                    f"{settings.LAUNDRY_URL}/rooms/{room['room_id']}/machines?raw=true",
                    timeout=60,
                    headers=headers,
                )
                room_request.raise_for_status()
            except HTTPError as e:
                self.stdout.write(f"Error: {e}")
                return

            room_request_json = room_request.json()
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
