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
        venues = Venue.objects.all()
        dates = [timezone.now() + datetime.timedelta(days=i) for i in range(7)]
        menus = DiningMenu.objects.filter(date__gt=dates[0], date__lte=dates[-1])

        res = [None] * len(venues)
        for i, venue in enumerate(venues):
            venues_obj = {"id": venue.venue_id, "name": venue.name, "image": venue.image_url}
            days = []
            for date in dates:
                days_obj = dict()
                days_obj["date"] = date.strftime("%Y-%m-%d")
                days_obj["dayparts"] = [
                    {"starttime": menu.start_time, "endtime": menu.end_time, "label": menu.service}
                    for menu in menus.filter(venue=venue, date=date).all()
                ]
                days.append(days_obj)
            venues_obj["days"] = days
            res[i] = venues_obj
        return res

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
        stations = [None] * len(station_response)
        for i, station_data in enumerate(station_response):
            # TODO: This is inefficient for venues such as Houston Market
            station = DiningStation.objects.create(name=station_data["label"])
            item_ids = [int(item) for item in station_data["items"]]

            # Bulk add the items into the station
            items = DiningItem.objects.filter(item_id__in=item_ids)
            station.items.add(*items)
            station.save()
            stations[i] = station
        return stations

    def load_items(self, item_response):
        item_list = [None] * len(item_response)
        for i, key in enumerate(item_response):
            value = item_response[key]
            item_list[i] = DiningItem(
                item_id=key,
                name=value["label"],
                description=value["description"],
                ingredients=value["ingredients"],
            )
        # Ignore conflicts because possibility of duplicate items
        DiningItem.objects.bulk_create(item_list, ignore_conflicts=True)
