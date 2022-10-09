import datetime

import requests
from django.conf import settings
from django.utils import timezone
from django.utils.timezone import make_aware
from requests.exceptions import ConnectTimeout, ReadTimeout

from dining.models import DiningItem, DiningMenu, DiningStation, Venue


OPEN_DATA_URL = "https://3scale-public-prod-open-data.apps.k8s.upenn.edu/api/v1/dining/"
OPEN_DATA_ENDPOINTS = {"VENUES": OPEN_DATA_URL + "venues", "MENUS": OPEN_DATA_URL + "menus"}


class APIError(ValueError):
    pass


class DiningAPIWrapper:
    def __init__(self):
        self.token = None
        self.expiration = timezone.localtime()
        self.openid_endpoint = (
            "https://sso.apps.k8s.upenn.edu/auth/realms/master/protocol/openid-connect/token"
        )

    def update_token(self):
        if self.expiration > timezone.localtime():
            return
        body = {
            "client_id": settings.DINING_ID,
            "client_secret": settings.DINING_SECRET,
            "grant_type": "client_credentials",
        }
        response = requests.post(self.openid_endpoint, data=body).json()
        if "error" in response:
            raise APIError(f"Dining: {response['error']}, {response.get('error_description')}")
        self.expiration = timezone.localtime() + datetime.timedelta(seconds=response["expires_in"])
        self.token = response["access_token"]

    def request(self, *args, **kwargs):
        """Make a signed request to the dining API."""
        self.update_token()

        headers = {"Authorization": f"Bearer {self.token}"}

        # add authorization headers
        if "headers" in kwargs:
            kwargs["headers"].update(headers)
        else:
            kwargs["headers"] = headers

        try:
            return requests.request(*args, **kwargs)
        except (ConnectTimeout, ReadTimeout, ConnectionError):
            raise APIError("Dining: Connection timeout")

    def get_venues(self):
        results = []
        venues_route = OPEN_DATA_ENDPOINTS["VENUES"]
        response = self.request("GET", venues_route)
        if response.status_code != 200:
            raise APIError("Dining: Error connecting to API")
        venues = response.json()["result_data"]["campuses"]["203"]["cafes"]
        for key, value in venues.items():
            # Cleaning up json response
            venue = Venue.objects.filter(venue_id=key).first()
            value["name"] = venue.name
            value["image"] = venue.image_url if venue else None

            value["id"] = int(key)
            remove_items = [
                "cor_icons",
                "city",
                "state",
                "zip",
                "latitude",
                "longitude",
                "description",
                "message",
                "eod",
                "timezone",
                "menu_type",
                "menu_html",
                "location_detail",
                "weekly_schedule",
            ]
            [value.pop(item) for item in remove_items]
            for day in value["days"]:
                day.pop("message")
                removed_dayparts = set()
                for i in range(len(day["dayparts"])):
                    daypart = day["dayparts"][i]
                    [daypart.pop(item) for item in ["id", "hide"]]
                    if not daypart["starttime"]:
                        removed_dayparts.add(i)
                        continue
                    for time in ["starttime", "endtime"]:
                        daypart[time] = datetime.datetime.strptime(
                            day["date"] + "T" + daypart[time], "%Y-%m-%dT%H:%M"
                        )
                # Remove empty dayparts (unavailable meal times)
                day["dayparts"] = [
                    day["dayparts"][i]
                    for i in range(len(day["dayparts"]))
                    if i not in removed_dayparts
                ]
            results.append(value)
        return results

    def load_menu(self, date=timezone.now().date()):
        """
        Loads the weeks menu starting from today
        NOTE: This method should only be used in load_next_menu.py, which is
        run based on a cron job every day
        """

        # Venues without a menu should not be parsed
        skipped_venues = [747, 1163, 1731, 1732, 1733, 1464004, 1464009]

        # TODO: Handle API responses during empty menus (holidays)
        menu_base = OPEN_DATA_ENDPOINTS["MENUS"]
        venues = Venue.objects.all()
        for venue in venues:
            if venue.venue_id in skipped_venues:
                continue

            response = self.request("GET", f"{menu_base}?cafe={venue.venue_id}&date={date}").json()
            # Load new items into database
            # TODO: There is something called a "goitem" for venues like English House.
            # We are currently not loading them in
            self.load_items(response["menus"]["items"])

            menu = response["menus"]["days"][0]
            dayparts = menu["cafes"][str(venue.venue_id)]["dayparts"][0]
            for daypart in dayparts:
                # Parse the dates in data
                for time in ["starttime", "endtime"]:
                    daypart[time] = make_aware(
                        datetime.datetime.strptime(
                            menu["date"] + "T" + daypart[time], "%Y-%m-%dT%H:%M"
                        )
                    )
                dining_menu = DiningMenu.objects.create(
                    venue=venue,
                    date=menu["date"],
                    start_time=daypart["starttime"],
                    end_time=daypart["endtime"],
                    service=daypart["label"],
                )
                # Append stations to dining menu
                stations = self.load_stations(daypart["stations"])
                dining_menu.stations.add(*stations)
                dining_menu.save()

    def load_stations(self, station_response):
        # Store stations into list
        stations = list()
        for station_data in station_response:
            # TODO: This is inefficient for venues such as Houston Market
            station = DiningStation.objects.create(name=station_data["label"])
            item_ids = [int(item) for item in station_data["items"]]
            # Bulk add the items into the station
            items = DiningItem.objects.filter(item_id__in=item_ids)
            station.items.add(*items)
            station.save()
            stations.append(station)
        return stations

    def load_items(self, item_response):
        # NOTE: If there are performance issues, we can initialize
        # the list with the size of item_response
        item_list = list()
        for key, value in item_response.items():
            item_list.append(
                DiningItem(
                    item_id=key,
                    name=value["label"],
                    description=value["description"],
                    ingredients=value["ingredients"],
                )
            )
        # Ignore conflicts because possibility of duplicate items
        DiningItem.objects.bulk_create(item_list, ignore_conflicts=True)
