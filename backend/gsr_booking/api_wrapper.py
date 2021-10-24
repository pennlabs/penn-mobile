import datetime

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.utils import timezone
from requests.exceptions import ConnectTimeout, ReadTimeout
from gsr_booking.models import (
    GSR,
    Group,
    GroupMembership,
    GSRBooking,
    GSRBookingCredentials,
    UserSearchIndex,
)


BASE_URL = "https://libcal.library.upenn.edu"
API_URL = "https://api2.libcal.com"
WHARTON_URL = "https://apps.wharton.upenn.edu/gsr/api/v1/"

# unbookable rooms
LOCATION_BLACKLIST = {3620, 2636, 2611, 3217, 2637, 2634}
ROOM_BLACKLIST = {7176, 16970, 16998, 17625}


class APIError(ValueError):
    pass

class BookingWrapper:
    def __init__(self):
        self.WLW = WhartonLibWrapper()
        self.LCW = LibCalWrapper()

    def book_room(self, gid, rid, start, end, user):
        gsr = GSR.objects.filter(gid=gid)
        if not gsr.exists():
            raise APIError(f"Unknown GSR GID {gid}")

        # error catching on view side
        if gsr.kind == GSR.KIND_WHARTON:
            return self.WLW.book_room(rid, start, end, user.username).get("booking_id")
        else:
            return self.LCW.book_room(rid, start, end, user).get("booking_id")

    def get_availability(self, lid, gid, start, end, user):
        # checks which GSR class to use
        gsr = GSR.objects.filter(lid=lid)
        if not gsr.exists():
            raise APIError(f"Unknown GSR LID {lid}")
        
        if gsr.kind == GSR.KIND_WHARTON:
            rooms = self.WLW.get_availability(lid, start, end, user.username)
        else:
            rooms = self.LCW.get_availability(lid, start, end)
        
        # cleans data to match Wharton wrapper
        try:
            gsr = [x for x in rooms["categories"] if x["cid"] == int(gid)][0]
        except IndexError:
            raise APIError("Unknown GSR")

        for room in gsr["rooms"]:
            for availability in room["availability"]:
                availability["start_time"] = availability["from"]
                availability["end_time"] = availability["to"]
                del availability["from"]
                del availability["to"]
        context = {}
        context["name"] = gsr["name"]
        context["gid"] = gsr["cid"]
        context["rooms"] = [
            {"room_name": x["name"], "id": x["id"], "availability": x["availability"]}
            for x in gsr["rooms"]
        ]
        return context
        

    def cancel_room():
        # TODO
        pass


    # Check credits function here
    # Implement two hour limit
    def check_credits(self, lid, gid, user):
        gsr = GSR.objects.filter(lid=lid, gid=gid)
        if not gsr.exists():
            raise APIError(f"Unknown GSR LID {lid}")
        total_minutes = 0
        if gsr.first().kind == GSR.KIND_WHARTON:
            wharton_reservations = self.WLW.get_reservations(user)['bookings']
            for reservation in wharton_reservations:
                if reservation["lid"] == 1:
                    reservation["lid"] = "JMHH"
                if reservation["lid"] == 6:
                    reservation["lid"] = "ARB"
                if reservation['lid'] == lid:
                    start = datetime.datetime.strptime(reservation["start"], "%Y-%m-%dT%H:%M:%S%z")
                    end = datetime.datetime.strptime(reservation["end"], "%Y-%m-%dT%H:%M:%S%z")
                    total_minutes += int((end.timestamp() - start.timestamp()) / 60)
            return 90 - total_minutes

        else:
            
            start = timezone.now().date()
            dt = datetime.datetime.combine(start, datetime.datetime.min.time())
            print(start)
            # end = timezone.now().date() + 1
            
            libcal_reservations = GSRBooking.objects.filter(gsr__in=GSR.objects.filter(kind=GSR.KIND_LIBCAL), is_cancelled=False)

       

class WhartonLibWrapper:
    def request(self, *args, **kwargs):
        """Make a signed request to the libcal API."""

        headers = {"Authorization": f"Token {settings.WHARTON_TOKEN}"}

        # add authorization headers
        kwargs["headers"] = headers

        try:
            response = requests.request(*args, **kwargs)
        except (ConnectTimeout, ReadTimeout):
            raise APIError("Wharton: Connection timeout")

        # only wharton students can access these routes
        if response.status_code == 403 or response.status_code == 401:
            raise APIError("Wharton: GSR view restricted to Wharton Pennkeys")
        return response

    def is_wharton(self, username):
        url = f"{WHARTON_URL}{username}/privileges"
        try:
            response = self.request("GET", url).json()
            return response["type"] != "None"
        except APIError:
            return False

    def get_availability(self, lid, start, end, username):
        """Returns a list of rooms and their availabilities"""
        current_time = timezone.localtime()
        search_date = (
            datetime.datetime.strptime(start, "%Y-%m-%d").date()
            if start is not None
            else current_time.date()
        )

        # hits availability route for a given lid and date
        url = WHARTON_URL + username + "/availability/" + lid + "/" + str(search_date)
        rooms = self.request("GET", url).json()

        # presets end date as end midnight of next day
        end_date = (
            datetime.datetime.strptime(end + "T00:00:00-04:00", "%Y-%m-%dT%H:%M:%S%z")
            if end is not None
            else datetime.datetime.strptime(
                str(search_date + datetime.timedelta(days=1)) + "T00:00:00-04:00",
                "%Y-%m-%dT%H:%M:%S%z",
            )
        )
        for room in rooms:
            valid_slots = []
            for slot in room["availability"]:
                # checks if the available slots are within the current time and midnight of next day
                start_time = datetime.datetime.strptime(slot["start_time"], "%Y-%m-%dT%H:%M:%S%z")
                end_time = datetime.datetime.strptime(slot["end_time"], "%Y-%m-%dT%H:%M:%S%z")
                if start_time >= current_time and end_time <= end_date and not slot["reserved"]:
                    del slot["reserved"]
                    valid_slots.append(slot)
                room["availability"] = valid_slots
        return rooms

    def book_room(self, rid, start, end, username):
        """Books room if pennkey is valid"""
        payload = {
            "start": start,
            "end": end,
            "pennkey": username,
            "room": rid,
        }
        url = WHARTON_URL + username + "/student_reserve"
        response = self.request("POST", url, json=payload).json()
        if "error" in response:
            raise APIError("Wharton: " + response["error"])
        return response

    def get_reservations(self, user):
        url = WHARTON_URL + user.username + "/reservations"
        return self.request("GET", url).json()

    def cancel_room(self, user, booking_id):
        """Cancels reservation given booking id"""
        url = WHARTON_URL + user.username + "/reservations/" + booking_id + "/cancel"
        response = self.request("DELETE", url).json()
        if "detail" in response:
            raise APIError("Wharton: " + response["detail"])
        return response


class LibCalWrapper:
    def __init__(self):
        self.token = None
        self.expiration = timezone.localtime()

    def update_token(self):
        # does not get new token if the current one is still usable
        if self.expiration > timezone.localtime():
            return
        body = {
            "client_id": settings.LIBCAL_ID,
            "client_secret": settings.LIBCAL_SECRET,
            "grant_type": "client_credentials",
        }
        response = requests.post(f"{API_URL}/1.1/oauth/token", body).json()

        if "error" in response:
            raise APIError(f"LibCal: {response['error']}, {response.get('error_description')}")
        self.expiration = timezone.localtime() + datetime.timedelta(seconds=response["expires_in"])
        self.token = response["access_token"]

    def request(self, *args, **kwargs):
        """Make a signed request to the libcal API."""
        self.update_token()

        headers = {"Authorization": f"Bearer {self.token}"}

        # add authorization headers
        if "headers" in kwargs:
            kwargs["headers"].update(headers)
        else:
            kwargs["headers"] = headers

        try:
            return requests.request(*args, **kwargs)
        except (ConnectTimeout, ReadTimeout):
            raise APIError("LibCal: Connection timeout")

    def get_availability(self, lid, start=None, end=None):
        """Returns a list of rooms and their availabilities"""

        # adjusts url based on start and end times
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

        response = self.request("GET", f"{API_URL}/1.1/space/categories/{lid}").json()
        if "error" in response:
            raise APIError("LibCal: " + response["error"])
        output = {"id": lid, "categories": []}

        # if there aren't any rooms associated with this location, return
        if len(response) < 1:
            return output

        if "error" in response[0]:
            raise APIError("LibCal: " + response[0]["error"])

        if "categories" not in response[0]:
            return output

        # filters categories and then gets extra information on each room
        categories = response[0]["categories"]
        id_to_category = {i["cid"]: i["name"] for i in categories}
        categories = ",".join([str(x["cid"]) for x in categories])
        response = self.request("GET", f"{API_URL}/1.1/space/category/{categories}").json()
        for category in response:
            cat_out = {"cid": category["cid"], "name": id_to_category[category["cid"]], "rooms": []}

            # ignore equipment categories
            if cat_out["name"].endswith("Equipment"):
                continue

            items = category["items"]
            items = ",".join([str(x) for x in items])
            # hits this route for extra information
            response = self.request("GET", f"{API_URL}/1.1/space/item/{items}?{range_str}")

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
                        description = room["description"].replace("\xa0", " ")
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
            "nickname": f"{user.username} GSR Booking",
            "q43": f"{user.username} GSR Booking",
            "bookings": [{"id": rid, "to": end}],
            "test": test,
            "q2555": "5",
            "q2537": "5",
            "q3699": self.get_affiliation(user.email),
            "q2533": "000-000-0000",
            "q16801": "5",
            "q16802": "5",
            "q16805": "Yes",
            "q16804": "Yes",
        }

        response = self.request("POST", f"{API_URL}/1.1/space/reserve", json=data).json()

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
            raise APIError("LibCal: " + response["error"])
        return response

    def get_affiliation(self, email):
        """Gets school from email"""
        if "wharton" in email:
            return "Wharton"
        elif "seas" in email:
            return "SEAS"
        elif "sas" in email:
            return "SAS"
        else:
            return "Other"

    def cancel_room(self, booking_id):
        """Cancels room"""
        response = self.request("POST", f"{API_URL}/1.1/space/cancel/{booking_id}").json()
        if "error" in response[0]:
            raise APIError("LibCal: " + response[0]["error"])
        return response
