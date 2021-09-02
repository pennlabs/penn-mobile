import datetime

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.utils import timezone


BASE_URL = "https://libcal.library.upenn.edu"
API_URL = "https://api2.libcal.com"
WHARTON_URL = "https://apps.wharton.upenn.edu/gsr/api/v1/"

# unbookable rooms
LOCATION_BLACKLIST = set([3620, 2636, 2611, 3217, 2637, 2634])
ROOM_BLACKLIST = set([7176, 16970, 16998, 17625])


class APIError(ValueError):
    pass


class WhartonLibWrapper:
    def request(self, *args, **kwargs):
        """Make a signed request to the libcal API."""

        headers = {"Authorization": "Token {}".format(settings.WHARTON_TOKEN)}

        # add authorization headers
        kwargs["headers"] = headers

        response = requests.request(*args, **kwargs)
        if response.status_code == 403:
            raise APIError("Disallowed")
        return response

    def get_availability(self, lid, start, end, username):
        current_time = timezone.localtime()
        search_date = (
            datetime.datetime.strptime(start, "%Y-%m-%d").date()
            if start is not None
            else current_time.date()
        )
        url = WHARTON_URL + username + "/availability/" + lid + "/" + str(search_date)
        rooms = self.request("GET", url).json()

        end_date = (
            datetime.datetime.strptime(end + "T00:00:00-04:00", "%Y-%m-%dT%H:%M:%S%z")
            if end is not None
            else datetime.datetime.strptime(
                str(current_time.date() + datetime.timedelta(days=1)) + "T00:00:00-04:00",
                "%Y-%m-%dT%H:%M:%S%z",
            )
        )
        for room in rooms:
            valid_slots = []
            for slot in room["availability"]:
                start_time = datetime.datetime.strptime(slot["start_time"], "%Y-%m-%dT%H:%M:%S%z")
                end_time = datetime.datetime.strptime(slot["end_time"], "%Y-%m-%dT%H:%M:%S%z")
                if start_time >= current_time and end_time <= end_date and not slot["reserved"]:
                    del slot["reserved"]
                    valid_slots.append(slot)
                room["availability"] = valid_slots
        return rooms

    def book_room(self, rid, start, end, username):
        payload = {
            "start": start,
            "end": end,
            "pennkey": username,
            "room": rid,
        }
        url = WHARTON_URL + username + "/student_reserve"
        response = self.request("POST", url, json=payload).json()
        if "error" in response:
            raise APIError(response["error"])
        return response

    def get_reservations(self, user):
        url = WHARTON_URL + user.username + "/reservations"
        return self.request("GET", url).json()

    def cancel_room(self, user, booking_id):
        url = WHARTON_URL + user.username + "/reservations/" + booking_id + "/cancel"
        return self.request("DELETE", url).json()


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

        return requests.request(*args, **kwargs)

    def get_buildings(self):
        """Returns a list of location IDs and names."""
        response = self.request("GET", "{}/1.1/space/locations".format(API_URL))
        out = []
        for x in response.json():
            if x["lid"] in LOCATION_BLACKLIST:
                continue
            if x["public"] == 1:
                del x["public"]
                if "formid" in x:
                    del x["formid"]
                out.append(x)
        return out

    def get_availability(self, lid, start=None, end=None):
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

        response = self.request("GET", "{}/1.1/space/categories/{}".format(API_URL, lid)).json()
        if "error" in response:
            raise APIError(response["error"])
        output = {"id": lid, "categories": []}

        # if there aren't any rooms associated with this location, return
        if len(response) < 1:
            return output

        if "error" in response[0]:
            raise APIError(response[0]["error"])

        if "categories" not in response[0]:
            return output

        categories = response[0]["categories"]
        id_to_category = {i["cid"]: i["name"] for i in categories}
        categories = ",".join([str(x["cid"]) for x in categories])
        response = self.request(
            "GET", "{}/1.1/space/category/{}".format(API_URL, categories)
        ).json()
        for category in response:
            cat_out = {"cid": category["cid"], "name": id_to_category[category["cid"]], "rooms": []}

            # ignore equipment categories
            if cat_out["name"].endswith("Equipment"):
                continue

            items = category["items"]
            items = ",".join([str(x) for x in items])
            response = self.request(
                "GET", "{}/1.1/space/item/{}?{}".format(API_URL, items, range_str)
            )

            if response.ok:
                for room in response.json():
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

    def book_room(self, rid, start, end, user, test=False):
        """Books a room given the required information."""

        # turns parameters into valid json format, then books room
        data = {
            "start": start,
            "fname": user.first_name,
            "lname": user.last_name,
            "email": user.email,
            "nickname": "hi",
            "bookings": [{"id": rid, "to": end}],
            "test": test,
            "q2555": "1",
            "q3699": self.get_affiliation(user.email),
        }

        response = self.request("POST", "{}/1.1/space/reserve".format(API_URL), json=data).json()

        # corrects keys in response
        if "error" not in response:
            if "errors" in response:
                errors = response["errors"]
                if isinstance(errors, list):
                    errors = " ".join(errors)
                response["error"] = BeautifulSoup(
                    errors.replace("\n", " "), "html.parser"
                ).text.strip()
                del response["errors"]
        if "error" in response:
            raise APIError(response["error"])
        return response

    def get_affiliation(self, email):
        if "wharton" in email:
            return "Wharton"
        elif "seas" in email:
            return "SEAS"
        elif "sas" in email:
            return "SAS"
        else:
            return "Other"

    def cancel_room(self, booking_id):
        return self.request("POST", "{}/1.1/space/cancel/{}".format(API_URL, booking_id)).json()

    def get_reservations(self, booking_ids):
        try:
            reservations = self.request(
                "GET", "{}/1.1/space/booking/{}".format(API_URL, booking_ids)
            )

            if reservations.status_code == 404:
                return []

            # cleans response values
            for reservation in reservations.json():
                reservation["service"] = "libcal"
                reservation["booking_id"] = reservation["bookId"]
                reservation["room_id"] = reservation["eid"]
                reservation["gid"] = reservation["cid"]
                del reservation["bookId"]
                del reservation["eid"]
                del reservation["cid"]
                del reservation["status"]
                del reservation["email"]
                del reservation["firstName"]
                del reservation["lastName"]

            room_ids = ",".join(
                list(set([str(reservation["room_id"]) for reservation in reservations]))
            )
            # cleans response values and adds room info to reservations
            if room_ids:
                rooms = self.get_room_info(room_ids)
                for room in rooms:
                    room["thumbnail"] = room["image"]
                    del room["image"]
                    del room["formid"]

                for res in reservations:
                    room = [x for x in rooms if x["id"] == res["room_id"]][0]
                    res["name"] = room["name"]
                    res["info"] = room
                    del res["room_id"]

            return reservations

        except (requests.exceptions.HTTPError) as error:
            raise APIError("Server Error: {}".format(error))

    def get_room_info(self, room_ids):
        """Gets room information for a given list of ids."""
        try:
            response = self.request("GET", "{}/1.1/space/item/{}".format(API_URL, room_ids))
            rooms = response.json()
            for room in rooms:
                if not room["image"].startswith("http"):
                    room["image"] = "https:" + room["image"]
                if "description" in room:
                    description = room["description"].replace(u"\xa0", u" ")
                    room["description"] = BeautifulSoup(description, "html.parser").text.strip()
        except requests.exceptions.HTTPError as error:
            raise APIError("Server Error: {}".format(error))
        return rooms
