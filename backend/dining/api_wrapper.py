import datetime
from json.decoder import JSONDecodeError

import requests
from django.conf import settings
from django.utils import timezone
from requests.exceptions import ConnectTimeout, ReadTimeout

from dining.models import Venue


V2_BASE_URL = "https://esb.isc-seo.upenn.edu/8091/open_data/dining/v2/?service="

V2_ENDPOINTS = {
    "VENUES": V2_BASE_URL + "venues",
    "HOURS": V2_BASE_URL + "cafes&cafe=",
    "MENUS": V2_BASE_URL + "menus&cafe=",
    "ITEMS": V2_BASE_URL + "items&item=",
}

VENUE_NAMES = {
    "593": "1920 Commons",
    "636": "Hill House",
    "637": "Kings Court English House",
    "638": "Kosher Dining at Falk",
}


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
            raise APIError(f"LibCal: {response['error']}, {response.get('error_description')}")
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
        venues_route = (
            "https://3scale-public-prod-open-data.apps.k8s.upenn.edu/api/v1/dining/venues"
        )
        response = self.request("GET", venues_route)
        if response.status_code != 200:
            raise APIError("Dining: Error connecting to API")
        venues = response.json()["result_data"]["campuses"]["203"]["cafes"]
        for key, value in venues.items():
            # cleaning up json response
            venue = Venue.objects.filter(venue_id=key).first()
            value["image"] = venue.image_url if venue else None
            value["id"] = key
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
                for daypart in day["dayparts"]:
                    [daypart.pop(item) for item in ["id", "hide"]]
            results.append(value)
        return results


def headers():
    """
    Returns headers necessary for Penn Dining API access
    """

    return {
        "Authorization-Bearer": settings.DINING_USERNAME,
        "Authorization-Token": settings.DINING_PASSWORD,
    }


def dining_request(url):
    """
    Makes GET request to Penn Dining API and returns the response
    """

    try:
        response = requests.get(url, params=None, headers=headers(), timeout=30)
    except ReadTimeout:
        raise APIError("Timeout error for request to {}".format(url))

    if response.status_code != 200:
        raise APIError("Request to {} returned {}".format(response.url, response.status_code))

    try:
        response = response.json()
    except JSONDecodeError as e:
        raise APIError("Error in venue ID: " + str(e))

    error_text = response["service_meta"]["error_text"]
    if error_text:
        raise APIError(error_text)

    return response


def normalize_weekly(data):
    """
    Normalization for dining menu data
    """

    if "tblMenu" not in data["result_data"]["Document"]:
        data["result_data"]["Document"]["tblMenu"] = []
    if isinstance(data["result_data"]["Document"]["tblMenu"], dict):
        data["result_data"]["Document"]["tblMenu"] = [data["result_data"]["Document"]["tblMenu"]]
    for day in data["result_data"]["Document"]["tblMenu"]:
        if "tblDayPart" not in day:
            continue
        if isinstance(day["tblDayPart"], dict):
            day["tblDayPart"] = [day["tblDayPart"]]
        for meal in day["tblDayPart"]:
            if isinstance(meal["tblStation"], dict):
                meal["tblStation"] = [meal["tblStation"]]
            for station in meal["tblStation"]:
                if isinstance(station["tblItem"], dict):
                    station["tblItem"] = [station["tblItem"]]
    return data


def get_meals(v2_response, venue_id):
    """
    Extract meals into old format from a DiningV2 JSON response
    """

    result_data = v2_response["result_data"]
    meals = []
    day_parts = result_data["days"][0]["cafes"][venue_id]["dayparts"][0]
    for meal in day_parts:
        stations = []
        for station in meal["stations"]:
            items = []
            for item_id in station["items"]:
                item = result_data["items"][item_id]
                new_item = {}
                new_item["txtTitle"] = item["label"]
                new_item["txtPrice"] = ""
                new_item["txtNutritionInfo"] = ""
                new_item["txtDescription"] = item["description"]
                new_item["tblSide"] = ""
                new_item["tblFarmToFork"] = ""
                attrs = [{"description": item["cor_icon"][attr]} for attr in item["cor_icon"]]
                if len(attrs) == 1:
                    new_item["tblAttributes"] = {"txtAttribute": attrs[0]}
                elif len(attrs) > 1:
                    new_item["tblAttributes"] = {"txtAttribute": attrs}
                else:
                    new_item["tblAttributes"] = ""
                if isinstance(item["options"], list):
                    item["options"] = {}
                if "values" in item["options"]:
                    for side in item["options"]["values"]:
                        new_item["tblSide"] = {"txtSideName": side["label"]}
                items.append(new_item)
            stations.append({"tblItem": items, "txtStationDescription": station["label"]})
        meals.append({"tblStation": stations, "txtDayPartDescription": meal["label"]})
    return meals
