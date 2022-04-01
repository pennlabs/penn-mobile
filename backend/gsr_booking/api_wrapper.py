import datetime
from enum import Enum

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.timezone import make_aware
from requests.exceptions import ConnectionError, ConnectTimeout, ReadTimeout

from gsr_booking.models import GSR, Group, GroupMembership, GSRBooking, Reservation
from gsr_booking.serializers import GSRBookingSerializer, GSRSerializer


BASE_URL = "https://libcal.library.upenn.edu"
API_URL = "https://api2.libcal.com"
WHARTON_URL = "https://apps.wharton.upenn.edu/gsr/api/v1/"

# unbookable rooms
LOCATION_BLACKLIST = {3620, 2636, 2611, 3217, 2637, 2634}
ROOM_BLACKLIST = {7176, 16970, 16998, 17625}


class CreditType(Enum):
    LIBCAL = "Libcal"
    HUNTSMAN = "JMHH"
    ARB = "ARB"


class APIError(ValueError):
    pass


class BookingWrapper:
    def __init__(self):
        self.WLW = WhartonLibWrapper()
        self.LCW = LibCalWrapper()

    def is_wharton(self, user):
        penn_labs = Group.objects.get(name="Penn Labs")
        me_group = Group.objects.get(name="Me", owner=user)
        membership = GroupMembership.objects.filter(group=me_group).first()
        return membership.is_wharton or user in penn_labs.members.all()

    def book_room(self, gid, rid, room_name, start, end, user, group_book=None):

        gsr = GSR.objects.filter(gid=gid).first()
        if not gsr:
            raise APIError(f"Unknown GSR GID {gid}")

        # error catching on view side
        if gsr.kind == GSR.KIND_WHARTON:
            booking_id = self.WLW.book_room(rid, start, end, user, gsr.lid).get("booking_id")
        else:
            booking_id = self.LCW.book_room(rid, start, end, user).get("booking_id")

        # creates booking on database
        # TODO: break start / end time into smaller chunks and pool credit for group booking
        booking = GSRBooking.objects.create(
            user=user,
            booking_id=str(booking_id),
            gsr=gsr,
            room_id=rid,
            room_name=room_name,
            start=datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%S%z"),
            end=datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%S%z"),
        )

        # create reservation with single-person-group containing user
        # TODO: create reservation with group that frontend passes in
        if not group_book:
            single_person_group = Group.objects.filter(owner=user).first()
            if not single_person_group:
                raise APIError("Unknown User")
            reservation = Reservation.objects.create(
                start=start, end=end, creator=user, group=single_person_group
            )
            booking.reservation = reservation
            booking.save()

        return booking

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
        bookings = self.LCW.get_reservations(user) + self.WLW.get_reservations(user)

        # TODO: toggle this for everyone
        group = Group.objects.get(name="Penn Labs")
        if user in group.members.all():
            for booking in bookings:
                gsr_booking = GSRBooking.objects.filter(booking_id=booking["booking_id"]).first()
                if not gsr_booking:
                    booking["room_name"] = "[Me] " + booking["room_name"]
                else:
                    # TODO: change this once we release the "Me" group
                    if gsr_booking.user == gsr_booking.reservation.creator:
                        booking["room_name"] = "[Me] " + booking["room_name"]
                    else:
                        booking["room_name"] = (
                            f"[{gsr_booking.reservation.group.name}] " + booking["room_name"]
                        )
        return bookings

    def check_credits(self, user):
        wharton_booking_credits = self.WLW.check_credits(user)
        libcal_booking_credits = self.LCW.check_credits(user)
        credits_merged = libcal_booking_credits.copy()
        credits_merged.update(wharton_booking_credits)
        return credits_merged


class WhartonLibWrapper:
    def request(self, *args, **kwargs):
        """Make a signed request to the libcal API."""

        headers = {"Authorization": f"Token {settings.WHARTON_TOKEN}"}

        # add authorization headers
        kwargs["headers"] = headers

        try:
            response = requests.request(*args, **kwargs)
        except (ConnectTimeout, ReadTimeout, ConnectionError):
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

    def book_room(self, rid, start, end, user, lid):
        """Books room if pennkey is valid"""

        start_date = datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%S%z")
        end_date = datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%S%z")
        duration = int((end_date.timestamp() - start_date.timestamp()) / 60)

        if self.check_credits(user)[lid] < duration:
            raise APIError("Not Enough Credits to Book")

        payload = {
            "start": start,
            "end": end,
            "pennkey": user.username,
            "room": rid,
        }
        url = f"{WHARTON_URL}{user.username}/student_reserve"
        response = self.request("POST", url, json=payload).json()
        if "error" in response:
            raise APIError("Wharton: " + response["error"])
        return response

    def get_reservations(self, user):
        booking_ids = set()

        reservations = Reservation.objects.filter(
            creator=user, end__gte=timezone.localtime(), is_cancelled=False
        )
        group_gsrs = GSRBooking.objects.filter(
            reservation__in=reservations, gsr__in=GSR.objects.filter(kind=GSR.KIND_WHARTON)
        )

        wharton_bookings = GSRBookingSerializer(
            GSRBooking.objects.filter(
                user=user,
                gsr__in=GSR.objects.filter(kind=GSR.KIND_WHARTON),
                end__gte=timezone.localtime(),
                is_cancelled=False,
            ).union(group_gsrs),
            many=True,
        ).data

        for wharton_booking in wharton_bookings:
            booking_ids.add(wharton_booking["booking_id"])

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
                    if str(booking["booking_id"]) not in booking_ids:
                        context = {
                            "booking_id": str(booking["booking_id"]),
                            "gsr": GSRSerializer(GSR.objects.get(lid=booking["lid"])).data,
                            "room_id": booking["rid"],
                            "room_name": booking["room"],
                            "start": booking["start"],
                            "end": booking["end"],
                        }
                        wharton_bookings.append(context)
                        booking_ids.add(str(booking["booking_id"]))
        except APIError:
            pass

        return wharton_bookings

    def cancel_room(self, user, booking_id):
        """Cancels reservation given booking id"""
        wharton_booking = GSRBooking.objects.filter(booking_id=booking_id)
        username = user.username
        if wharton_booking.exists():
            gsr_booking = wharton_booking.first()
            gsr_booking.is_cancelled = True
            gsr_booking.save()
            # changing username if booking is in database
            username = gsr_booking.user.username
        url = f"{WHARTON_URL}{username}/reservations/{booking_id}/cancel"
        response = self.request("DELETE", url).json()
        if "detail" in response:
            raise APIError("Wharton: " + response["detail"])
        return response

    def check_credits(self, user):
        # gets all current reservations from wharton availability route
        wharton_lids = GSR.objects.filter(kind=GSR.KIND_WHARTON).values_list("lid", flat=True)
        # wharton get 90 minutes of credit at any moment
        wharton_credits = {lid: 90 for lid in wharton_lids}
        reservations = self.get_reservations(user)
        for reservation in reservations:
            # determines if ARB or Huntsman
            room_type = reservation["gsr"]["lid"]
            if room_type in wharton_credits:
                # accumulates total minutes
                start = datetime.datetime.strptime(reservation["start"], "%Y-%m-%dT%H:%M:%S%z")
                end = datetime.datetime.strptime(reservation["end"], "%Y-%m-%dT%H:%M:%S%z")
                wharton_credits[room_type] -= int((end.timestamp() - start.timestamp()) / 60)

        # 90 minutes at any given time
        return wharton_credits


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
        except (ConnectTimeout, ReadTimeout, ConnectionError):
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

        start_date = datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%S%z")
        end_date = datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%S%z")
        duration = int((end_date.timestamp() - start_date.timestamp()) / 60)

        if self.check_credits(user, start_date)[CreditType.LIBCAL.value] < duration:
            raise APIError("Not Enough Credits to Book")

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

        reservations = Reservation.objects.filter(
            creator=user, end__gte=timezone.localtime(), is_cancelled=False
        )
        group_gsrs = GSRBooking.objects.filter(
            reservation__in=reservations, gsr__in=GSR.objects.filter(kind=GSR.KIND_LIBCAL)
        )

        return GSRBookingSerializer(
            GSRBooking.objects.filter(
                user=user,
                gsr__in=GSR.objects.filter(kind=GSR.KIND_LIBCAL),
                end__gte=timezone.localtime(),
                is_cancelled=False,
            ).union(group_gsrs),
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
            if user != gsr_booking.user and user != gsr_booking.reservation.creator:
                raise APIError("Error: Unauthorized: This reservation was booked by someone else.")
            gsr_booking.is_cancelled = True
            gsr_booking.save()
        response = self.request("POST", f"{API_URL}/1.1/space/cancel/{booking_id}").json()
        if "error" in response[0]:
            raise APIError("LibCal: " + response[0]["error"])
        return response

    def check_credits(self, user, lc_start=None):
        # default to beginning of day
        if lc_start is None:
            lc_start = make_aware(datetime.datetime.now())
            lc_start = lc_start.replace(second=0, microsecond=0, minute=0, hour=0)

        lc_end = lc_start + datetime.timedelta(days=1)

        # filters for all reservations for the given date
        reservations = GSRBooking.objects.filter(
            gsr__in=GSR.objects.filter(kind=GSR.KIND_LIBCAL),
            start__gte=lc_start,
            end__lte=lc_end,
            is_cancelled=False,
            user=user,
        )
        total_minutes = 0
        for reservation in reservations:
            # accumulates total minutes over all reservations
            total_minutes += int((reservation.end.timestamp() - reservation.start.timestamp()) / 60)
        # 120 minutes per day
        return {CreditType.LIBCAL.value: 120 - total_minutes}
