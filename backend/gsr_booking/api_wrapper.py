import datetime

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.timezone import make_aware
from requests.exceptions import ConnectTimeout, ReadTimeout

from gsr_booking.models import GSR, Group, GSRBooking, Reservation
from gsr_booking.serializers import GSRBookingSerializer, GSRSerializer


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

    def is_wharton(self, username):
        return self.WLW.is_wharton(username)

    def book_room(self, gid, rid, room_name, start, end, user):

        gsr = GSR.objects.filter(gid=gid).first()
        if not gsr:
            raise APIError(f"Unknown GSR GID {gid}")

        if not self.check_credits(gsr.lid, gid, user, start, end):
            raise APIError("Not Enough Credits to Book")

        # error catching on view side
        if gsr.kind == GSR.KIND_WHARTON:
            booking_id = self.WLW.book_room(rid, start, end, user.username).get("booking_id")
        else:
            booking_id = self.LCW.book_room(rid, start, end, user).get("booking_id")

        # create reservation with single-person-group containing user
        # TODO: create reservation with group that frontend passes in
        single_person_group = Group.objects.filter(owner=user).first()
        if not single_person_group:
            raise APIError("Unknown User")
        reservation = Reservation.objects.create(
            start=start, end=end, creator=user, group=single_person_group
        )
        # creates booking on database
        # TODO: break start / end time into smaller chunks and pool credit for group booking
        GSRBooking.objects.create(
            reservation=reservation,
            user=user,
            booking_id=str(booking_id),
            gsr=gsr,
            room_id=rid,
            room_name=room_name,
            start=datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%S%z"),
            end=datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%S%z"),
        )

    def get_availability(self, lid, gid, start, end, user):
        # checks which GSR class to use
        gsr = GSR.objects.filter(lid=lid).first()
        if not gsr:
            raise APIError(f"Unknown GSR LID {lid}")
        if gsr.kind == GSR.KIND_WHARTON:
            rooms = self.WLW.get_availability(lid, start, end, user.username)
            return {"name": gsr.name, "gid": gsr.gid, "rooms": rooms}
        else:
            rooms = self.LCW.get_availability(lid, start, end)
            # cleans data to match Wharton wrapper
            try:
                lc_gsr = [x for x in rooms["categories"] if x["cid"] == int(gid)][0]
            except IndexError:
                raise APIError("Unknown GSR")

            for room in lc_gsr["rooms"]:
                for availability in room["availability"]:
                    availability["start_time"] = availability["from"]
                    availability["end_time"] = availability["to"]
                    del availability["from"]
                    del availability["to"]

            context = {"name": lc_gsr["name"], "gid": lc_gsr["cid"]}
            context["rooms"] = [
                {"room_name": x["name"], "id": x["id"], "availability": x["availability"]}
                for x in lc_gsr["rooms"]
            ]
            return context

    def cancel_room(self, booking_id, user):
        try:
            # gets reservations from wharton for a user
            wharton_bookings = self.WLW.get_reservations(user)
        except APIError as e:
            # don't throw error if the student is non-wharton
            if str(e) == "Wharton: GSR view restricted to Wharton Pennkeys":
                wharton_bookings = []
            else:
                raise APIError(f"Error: {str(e)}")
        wharton_booking_ids = [str(x["booking_id"]) for x in wharton_bookings]
        try:
            gsr_booking = GSRBooking.objects.filter(booking_id=booking_id).first()
            # checks if the booking_id is a wharton booking_id
            if booking_id in wharton_booking_ids:
                self.WLW.cancel_room(user, booking_id)
            else:
                # defaults to wharton because it is in wharton_booking_ids
                self.LCW.cancel_room(user, booking_id)
        except APIError as e:
            raise APIError(f"Error: {str(e)}")

        if gsr_booking:
            # updates GSR booking after done
            gsr_booking.is_cancelled = True
            gsr_booking.save()

            reservation = gsr_booking.reservation
            all_cancelled = True
            # loops through all reservation bookings and checks if all
            # corresponding bookings are cancelled
            for booking in GSRBooking.objects.filter(reservation=reservation):
                if not booking.is_cancelled:
                    all_cancelled = False
                    break
            if all_cancelled:
                reservation.is_cancelled = True
                reservation.save()

    def get_reservations(self, user):
        libcal_bookings = self.LCW.get_reservations(user)
        wharton_bookings = self.WLW.get_reservations(user)
        # add all libcal_bookings and wharton bookings not in table
        # use list comprehension instead of set to preserve ordering
        return libcal_bookings + wharton_bookings

    def check_credits(self, lid, gid, user, start, end):
        """
        Checks credits for a particular room at a particular date
        from gsr_booking.api_wrapper import BookingWrapper
        b = BookingWrapper()
        b.check_credits(lid, gid, request.user, "2021-10-27")
        """

        start = datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%S%z")
        end = datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%S%z")
        duration = int((end.timestamp() - start.timestamp()) / 60)

        gsr = GSR.objects.filter(lid=lid, gid=gid).first()
        # checks if valid gsr
        if not gsr:
            raise APIError(f"Unknown GSR LID {lid}")

        total_minutes = 0
        if gsr.kind == GSR.KIND_WHARTON:
            # gets all current reservations from wharton availability route
            reservations = self.WLW.get_reservations(user)
            for reservation in reservations:
                if reservation["gsr"]["lid"] == lid:
                    # accumulates total minutes
                    start = datetime.datetime.strptime(reservation["start"], "%Y-%m-%dT%H:%M:%S%z")
                    end = datetime.datetime.strptime(reservation["end"], "%Y-%m-%dT%H:%M:%S%z")
                    total_minutes += int((end.timestamp() - start.timestamp()) / 60)
            # 90 minutes at any given time
            return 90 - total_minutes >= duration
        else:
            lc_start = make_aware(
                datetime.datetime.combine(start.date(), datetime.datetime.min.time())
            )
            lc_end = lc_start + datetime.timedelta(days=1)
            # filters for all reservations for the given date
            reservations = GSRBooking.objects.filter(
                gsr__in=GSR.objects.filter(kind=GSR.KIND_LIBCAL),
                start__gte=lc_start,
                end__lte=lc_end,
                is_cancelled=False,
            )
            total_minutes = 0
            for reservation in reservations:
                # accumulates total minutes over all reservations
                total_minutes += int(
                    (reservation.end.timestamp() - reservation.start.timestamp()) / 60
                )
            # 120 minutes per day
            return 120 - total_minutes >= duration


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
        url = f"{WHARTON_URL}{username}/availability/{lid}/{str(search_date)}"
        rooms = self.request("GET", url).json()
        if "closed" in rooms and rooms["closed"]:
            return []

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
        url = f"{WHARTON_URL}{username}/student_reserve"
        response = self.request("POST", url, json=payload).json()
        if "error" in response:
            raise APIError("Wharton: " + response["error"])
        return response

    def get_reservations(self, user):
        wharton_bookings = []
        try:
            url = f"{WHARTON_URL}{user.username}/reservations"
            bookings = self.request("GET", url).json()["bookings"]
            # ignore this because this route is used by everyone
            for booking in bookings:
                booking["lid"] = GSR.objects.get(gid=booking["lid"]).lid
                # checks if reservation is within time range
                if (
                    datetime.datetime.strptime(booking["end"], "%Y-%m-%dT%H:%M:%S%z")
                    >= timezone.localtime()
                ):
                    # filtering for lid here works because Wharton buildings have distinct lid's
                    context = {
                        "booking_id": str(booking["booking_id"]),
                        "gsr": GSRSerializer(GSR.objects.get(lid=booking["lid"])).data,
                        "room_id": booking["rid"],
                        "room_name": booking["room"],
                        "start": booking["start"],
                        "end": booking["end"],
                    }
                    wharton_bookings.append(context)
        except APIError:
            pass
        return wharton_bookings

    def cancel_room(self, user, booking_id):
        """Cancels reservation given booking id"""
        wharton_booking = GSRBooking.objects.filter(booking_id=booking_id)
        if wharton_booking.exists():
            gsr_booking = wharton_booking.first()
            gsr_booking.is_cancelled = True
            gsr_booking.save()
        url = f"{WHARTON_URL}{user.username}/reservations/{booking_id}/cancel"
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
        payload = {
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

        response = self.request("POST", f"{API_URL}/1.1/space/reserve", json=payload).json()

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

    def get_reservations(self, user):
        return GSRBookingSerializer(
            GSRBooking.objects.filter(
                user=user,
                gsr__in=GSR.objects.filter(kind=GSR.KIND_LIBCAL),
                end__gte=timezone.localtime(),
                is_cancelled=False,
            ),
            many=True,
        ).data

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

    def cancel_room(self, user, booking_id):
        """Cancels room"""
        gsr_booking = get_object_or_404(GSRBooking, booking_id=booking_id)
        if gsr_booking:
            gsr_booking.is_cancelled = True
            gsr_booking.save()
        if user != gsr_booking.user:
            raise APIError("Error: Unauthorized: This reservation was booked by someone else.")
        response = self.request("POST", f"{API_URL}/1.1/space/cancel/{booking_id}").json()
        if "error" in response[0]:
            raise APIError("LibCal: " + response[0]["error"])
        return response
