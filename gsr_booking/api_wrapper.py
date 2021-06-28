import datetime

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.utils import timezone


BASE_URL = "https://libcal.library.upenn.edu"
API_URL = "https://api2.libcal.com"

LOCATION_BLACKLIST = set([3620, 2636, 2611, 3217, 2637, 2634])
ROOM_BLACKLIST = set([7176, 16970, 16998, 17625])


class APIError(ValueError):
    pass


class LibCalWrapper:
    def __init__(self):
        self.token = None
        self.expiration = timezone.localtime()

    def get_token(self):
        # does not get new token if the current one is still usable
        if self.expiration > timezone.localtime():
            return
        body = {
            "client_id": settings.LIBCAL_ID,
            "client_secret": settings.LIBCAL_SECRET,
            "grant_type": "client_credentials",
        }
        response = requests.post("{}/1.1/oauth/token".format(API_URL), body).json()

        if "error" in response:
            raise APIError(
                "LibCal Auth Failed: {}, {}".format(
                    response["error"], response.get("error_description")
                )
            )

        self.expiration = timezone.localtime() + datetime.timedelta(seconds=response["expires_in"])
        self.token = response["access_token"]

    def request(self, *args, **kwargs):
        """Make a signed request to the libcal API."""
        if not self.token:
            self.get_token()

        headers = {"Authorization": "Bearer {}".format(self.token)}

        # add authorization headers
        if "headers" in kwargs:
            kwargs["headers"].update(headers)
        else:
            kwargs["headers"] = headers

        response = requests.request(*args, **kwargs)

        return response.json() if response.ok else None

    def get_buildings(self):
        """Returns a list of location IDs and names."""
        response = self.request("GET", "{}/1.1/space/locations".format(API_URL))
        out = []
        for x in response:
            if x["lid"] in LOCATION_BLACKLIST:
                continue
            if x["public"] == 1:
                del x["public"]
                x["service"] = "libcal"
                out.append(x)
        return out

    def get_rooms(self, lid, start=None, end=None):
        """Returns a list of rooms and their availabilities within the data ranges, grouped by category.
        :param lid: The ID of the location to retrieve rooms for.
        :type lid: int
        :param start: The start range for the availabilities to retrieve, in YYYY-MM-DD format.
        :type start: str
        :param end: The end range for the availabilities to retrieve, in YYYY-MM-DD format.
        :type end: str
        """

        range_str = "availability"
        if start:
            start_datetime = datetime.datetime.combine(
                datetime.datetime.strptime(start, "%Y-%m-%d").date(), datetime.datetime.min.time()
            )
            range_str += "=" + start
            if end and not start == end:
                range_str += "," + end
        else:
            start_datetime = None

        resp = self.request("GET", "{}/1.1/space/categories/{}".format(API_URL, lid))
        if "error" in resp:
            raise APIError(resp["error"])
        output = {"id": lid, "categories": []}

        # if there aren't any rooms associated with this location, return
        if len(resp) < 1:
            return output

        if "error" in resp[0]:
            raise APIError(resp[0]["error"])

        if "categories" not in resp[0]:
            return output

        categories = resp[0]["categories"]
        id_to_category = {i["cid"]: i["name"] for i in categories}
        categories = ",".join([str(x["cid"]) for x in categories])
        resp = self.request("GET", "{}/1.1/space/category/{}".format(API_URL, categories))
        for category in resp:
            cat_out = {"cid": category["cid"], "name": id_to_category[category["cid"]], "rooms": []}

            # ignore equipment categories
            if cat_out["name"].endswith("Equipment"):
                continue

            items = category["items"]
            items = ",".join([str(x) for x in items])
            resp = self.request("GET", "{}/1.1/space/item/{}?{}".format(API_URL, items, range_str))

            if resp is not None:
                for room in resp:
                    if room["id"] in ROOM_BLACKLIST:
                        continue
                    # prepend protocol to urls
                    if "image" in room and room["image"]:
                        if not room["image"].startswith("http"):
                            room["image"] = "https:" + room["image"]
                    # convert html descriptions to text
                    if "description" in room:
                        description = room["description"].replace(u"\xa0", u" ")
                        room["description"] = BeautifulSoup(description, "html.parser").text.strip()
                    # remove extra fields
                    if "formid" in room:
                        del room["formid"]
                    # enforce date filter
                    # API returns dates outside of the range, fix this manually
                    if start_datetime:
                        out_times = []
                        for time in room["availability"]:
                            parsed_start = datetime.datetime.strptime(
                                time["from"][:-6], "%Y-%m-%dT%H:%M:%S"
                            )
                            if parsed_start >= start_datetime:
                                out_times.append(time)
                        room["availability"] = out_times
                    cat_out["rooms"].append(room)
                if cat_out["rooms"]:
                    output["categories"].append(cat_out)
        return output

    def book_room(self, rid, start, end, fname, lname, email, nickname, custom={}, test=False):
        """Books a room given the required information.

        :param custom:
            Any other custom fields required to book the room.
        :type custom: dict
        :param test:
            If this is set to true, don't actually book the room. Default is false.
        :type test: bool
        :returns:
            Dictionary containing a success and error field.
        """
        # data = {
        #     "start": "2020-04-30T18:42:45-04:00",
        #     "fname": fname,
        #     "lname": lname,
        #     "email": email,
        #     "nickname": nickname,
        #     "bookings": [
        #         {
        #             "id": rid,
        #             "to": "2020-04-30T18:42:45-04:00"
        #         }
        #     ],
        #     # "test": test
        # }
        data = {
            "start": "2021-06-29T18:42:45-04:00",
            "fname": "John",
            "lname": "Smith",
            "email": "john.smith@gmail.com",
            "nickname": "Law 101 Tutorial Group (John)",
            "q43": "Strawberry",
            "bookings": [{"id": 1090, "to": "2021-06-29T20:42:45-04:00"}],
            "test": test,
        }
        # print(custom)
        # data.update(custom)
        response = self.request(
            "POST", "https://libcal.library.upenn.edu/1.1/space/reserve", json=data
        )
        print(response)
        # if "errors" in response and "error" not in response:
        #     errors = response["errors"]
        #     if isinstance(errors, list):
        #         errors = " ".join(errors)
        #     response["error"] = BeautifulSoup(errors.replace("\n", " "),
        #       "html.parser").text.strip()
        #     del response["errors"]
        # if "results" not in response:
        #     if "error" not in response:
        #         response["error"] = None
        #         response["results"] = True
        #     else:
        #         response["results"] = False
        return response
