import csv
from functools import reduce

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from requests.exceptions import HTTPError


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
            [room["id"], room["roomName"], location["description"], location["id"]]
            for location in locations
            for room in location["rooms"]
        ]

        # for each room, send a request to find number of washers and dryers
        # TODO: This is really inefficient, but may require change in frontend code so leaving it for now
        for room in laundry_rooms:
            try:
                room_request = requests.get(
                    f"{settings.LAUNDRY_URL}/rooms/{room[0]}/machines?raw=true",
                    timeout=60,
                    headers=headers,
                )
                room_request.raise_for_status()
            except HTTPError as e:
                self.stdout.write(f"Error: {e}")
                return

            room_request_json = room_request.json()
            # count washers and dryers
            count = (0, 0)
            f = lambda acc, x: (
                (acc[0] + 1, acc[1])
                if x["isWasher"]
                else (acc[0], acc[1] + 1) if x["isDryer"] else acc
            )
            count = reduce(f, room_request_json, count)
            room.extend(count)

        # write to csv
        with open("laundry/data/laundry_data_new.csv", "w") as data:
            writer = csv.writer(data)
            writer.writerows(laundry_rooms)
