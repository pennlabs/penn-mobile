import datetime
import re
from abc import ABC, abstractmethod
from enum import Enum
from random import randint

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import F, Prefetch, Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils import timezone
from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError, ConnectTimeout, ReadTimeout

from gsr_booking.models import GSR, GroupMembership, GSRBooking, Reservation
from gsr_booking.serializers import GSRBookingSerializer, GSRSerializer
from portal.logic import get_user_info
from utils.errors import APIError


User = get_user_model()


BASE_URL = "https://libcal.library.upenn.edu"
API_URL = "https://api2.libcal.com"
WHARTON_URL = "https://apps.wharton.upenn.edu/gsr/api/v1/"
PENNGROUPS_URL = (
    "https://grouperWs.apps.upenn.edu/grouperWs/servicesRest/4.9.3/subjects/"  # noqa: E501
)

# unbookable rooms
LOCATION_BLACKLIST = {3620, 2636, 2611, 3217, 2637, 2634}
ROOM_BLACKLIST = {7176, 16970, 16998, 17625}

WHARTON_CREDIT_LIMIT = 6
LIBCAL_CREDIT_LIMIT = 6


class CreditType(Enum):
    LIBCAL = "Libcal"
    HUNTSMAN = "JMHH"
    ARB = "ARB"


class AbstractBookingWrapper(ABC):
    @abstractmethod
    def book_room(self, rid, start, end, user):
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def cancel_room(self, booking_id, user):
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def get_availability(self, lid, start, end, user):
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def get_reservations(self, user):
        raise NotImplementedError  # pragma: no cover


class WhartonBookingWrapper(AbstractBookingWrapper):
    def request(self, *args, **kwargs):
        """Make a signed request to the Wharton GSR API."""
        # add authorization headers
        kwargs["headers"] = {"Authorization": f"Token {settings.WHARTON_TOKEN}"}

        try:
            response = requests.request(*args, **kwargs)
        except (ConnectTimeout, ReadTimeout, ConnectionError):
            raise APIError("Wharton: Connection timeout")

        if not response.ok:
            raise APIError(f"Wharton: Error {response.status_code} when reserving data")

        return response

    def book_room(self, rid, start, end, user):
        """Books room if pennkey is valid"""
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

    def cancel_room(self, booking_id, user):
        """Cancels reservation given booking id"""
        url = f"{WHARTON_URL}{user.username}/reservations/{booking_id}/cancel"
        response = self.request("DELETE", url).json()
        if "detail" in response:
            raise APIError("Wharton: " + response["detail"])
        return response

    def get_availability(self, lid, start, end, user):
        """Returns a list of rooms and their availabilities"""
        current_time = timezone.localtime()
        search_date = (
            datetime.datetime.strptime(start, "%Y-%m-%d").date()
            if start is not None
            else current_time.date()
        )

        # hits availability route for a given lid and date
        url = f"{WHARTON_URL}{user.username}/availability/{lid}/{str(search_date)}"
        rooms = self.request("GET", url).json()

        if "closed" in rooms and rooms["closed"]:
            return []

        # presets end date as end midnight of next day
        end_date = (
            datetime.datetime.strptime(end, "%Y-%m-%d").date() if end is not None else search_date
        )
        end_date = timezone.make_aware(
            datetime.datetime.combine(
                end_date + datetime.timedelta(days=1), datetime.datetime.min.time()
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

    def get_reservations(self, user):
        url = f"{WHARTON_URL}{user.username}/reservations"
        bookings = self.request("GET", url).json()["bookings"]

        now = timezone.localtime()
        return [
            {
                "booking_id": str(booking["booking_id"]),
                "gid": booking["lid"],  # their lid is our gid
                "room_id": booking["rid"],
                "room_name": booking["room"],
                "start": booking["start"],
                "end": booking["end"],
            }
            for booking in bookings
            if datetime.datetime.strptime(booking["end"], "%Y-%m-%dT%H:%M:%S%z") >= now
        ]

    def is_wharton(self, user):
        url = f"{WHARTON_URL}{user.username}/privileges"
        try:
            response = self.request("GET", url)
            if response.status_code != 200:
                return None
            res_json = response.json()
            return res_json.get("type") == "whartonMBA" or res_json.get("type") == "whartonUGR"
        except APIError:
            raise
        except Exception as e:
            raise APIError(f"Wharton: Error checking privileges: {str(e)}")


class PennGroupsBookingWrapper(AbstractBookingWrapper):
    """
    Handles AGH GSR bookings with SEAS permission checks.
    Uses separate LibCal credentials specific to AGH.
    """

    def __init__(self):
        # Separate LibCal token for AGH
        self.token = None
        self.expiration = timezone.localtime()

    def update_token(self):
        """Get AGH-specific LibCal token"""
        if self.expiration > timezone.localtime():
            return
        body = {
            "client_id": settings.AGH_LIBCAL_ID,  # Different from regular LibCal!
            "client_secret": settings.AGH_LIBCAL_SECRET,
            "grant_type": "client_credentials",
        }

        response = requests.post(f"{API_URL}/1.1/oauth/token", body)

        if response.status_code != 200:
            raise APIError(f"AGH LibCal: HTTP {response.status_code} when getting token")

        response = response.json()

        if "error" in response:
            raise APIError(f"AGH LibCal: {response['error']}, {response.get('error_description')}")

        self.expiration = timezone.localtime() + datetime.timedelta(seconds=response["expires_in"])
        self.token = response["access_token"]

    def request(self, *args, **kwargs):
        """Make a signed request to the libcal API using AGH credentials."""
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
            raise APIError("AGH LibCal: Connection timeout")

    def get_user_pennid(self, user):
        """
        Get user's pennid.
        """
        user_info = get_user_info(user)
        pennid = user_info.get("pennid")
        if not pennid:
            raise APIError("PennGroups: User pennid not found in Platform API response")
        return pennid

    def get_authorized_rooms(self, user):
        """
        Check which AGH rooms the user can access via PennGroups API.
        Returns dict mapping room extensions to their group info, or None if API fails.
        """
        try:
            # Get pennid from Platform API (PennGroups requires numerical pennid, not username)
            try:
                pennid = self.get_user_pennid(user)
            except APIError:
                raise APIError("PennGroups: Failed to get user pennid")

            url = f"{PENNGROUPS_URL}{pennid}/groups"
            response = requests.get(
                url,
                auth=HTTPBasicAuth(settings.PENNGROUPS_USERNAME, settings.PENNGROUPS_PASSWORD),
                timeout=5,
            )

            # Check HTTP status first
            if response.status_code != 200:
                raise APIError(f"PennGroups: HTTP {response.status_code}")

            data = response.json()
            result = data.get("WsGetGroupsLiteResult", {})
            metadata = result.get("resultMetadata", {})

            if metadata.get("resultCode") == "SUBJECT_NOT_FOUND":
                return {}  # Not a SEAS student

            if metadata.get("resultCode") == "SUCCESS":
                groups = result.get("wsGroups", []) or []  # Handle None case
                return {
                    group["extension"]: group
                    for group in groups
                    if "AGH:GSR" in group.get("name", "")
                }

            raise APIError(f"PennGroups: Unexpected resultCode '{metadata.get('resultCode')}'")

        except requests.exceptions.JSONDecodeError:
            raise APIError("PennGroups: Invalid JSON response")
        except (ConnectionError, ConnectTimeout, ReadTimeout):
            raise APIError("PennGroups: Connection timeout")
        except Exception as e:
            raise APIError(f"PennGroups: Error accessing API: {str(e)}")

    def is_seas(self, user):
        """Check if user has SEAS status"""
        try:
            rooms = self.get_authorized_rooms(user)
            return len(rooms) > 0
        except APIError:
            raise

    def extract_room_number(self, libcal_name):
        """Extract room number from LibCal name like 'AGH 334' -> '334' or 'AGH 300A' -> '300A'"""
        match = re.search(r"AGH\s+(\d+[A-Za-z]*)", libcal_name)
        return match.group(1) if match else None

    def is_room_authorized(self, libcal_name, authorized_extensions):
        """Check if LibCal room name corresponds to an authorized PennGroups extension"""
        room_number = self.extract_room_number(libcal_name)
        if not room_number:
            return False

        # Check if there's a matching extension like "GroupStudyRoom_334"
        expected_extension = f"GroupStudyRoom_{room_number}"
        return expected_extension in authorized_extensions

    def book_room(self, rid, start, end, user):
        """
        Check SEAS permissions via PennGroups, then book via LibCal using AGH credentials.

        rid: The LibCal room ID
        start: ISO format datetime string
        end: ISO format datetime string
        user: User object
        """
        # First, verify SEAS membership and room authorization
        try:
            authorized_rooms = self.get_authorized_rooms(user)
        except APIError:
            raise APIError("PennGroups: Unable to verify SEAS membership")

        if not authorized_rooms:
            raise APIError("AGH rooms are only available to SEAS students")

        # Verify that the specific room (rid) matches one of the authorized rooms
        try:
            # Get room details to extract room name for authorization check
            room_response = self.request("GET", f"{API_URL}/1.1/space/item/{rid}")

            # Check status code BEFORE calling .json()
            if room_response.status_code != 200:
                raise APIError(
                    f"AGH LibCal: Room not found or unavailable (HTTP {room_response.status_code})"
                )

            room_data = room_response.json()

            # LibCal space/item endpoint returns a list with one item
            if not room_data or len(room_data) == 0:
                raise APIError("AGH LibCal: Empty room data returned")

            room_name = room_data[0].get("name", "")

            # Check if user is authorized for this specific room
            if not self.is_room_authorized(room_name, authorized_rooms):
                raise APIError(f"AGH LibCal: User not authorized for room {room_name}")

        except APIError:
            raise
        except Exception as e:
            raise APIError(f"AGH LibCal: Unable to verify room authorization: {str(e)}")

        # turns parameters into valid json format, then books room
        payload = {
            "start": start,
            "fname": user.first_name,
            "lname": user.last_name,
            "email": user.email,
            "nickname": f"{user.username} GSR Booking",
            "q43": f"{user.username} GSR Booking",
            "bookings": [{"id": rid, "to": end}],
            "test": False,
            "q2555": "4-5",  # corresponds to radio button
            "q2537": "4-5",  # corresponds to radio button
            "q3699": "SEAS",  # Hardcoded to SEAS because we only have SEAS rooms
            "q2533": "000-000-0000",
            "q16801": "4",  # has to be between 2 and 4
            "q16802": "5",  # has to be between 5 and 10
            "q16805": "Yes",  # has to be "Yes"
            "q16804": "Yes",  # has to be "Yes"
        }

        response = self.request("POST", f"{API_URL}/1.1/space/reserve", json=payload)

        if response.status_code != 200:
            raise APIError(f"GSR Reserve: Error {response.status_code} when reserving data")

        res_json = response.json()
        # corrects keys in response
        if "error" not in res_json and "errors" in res_json:
            errors = res_json["errors"]
            if isinstance(errors, list):
                errors = " ".join(errors)
            res_json["error"] = BeautifulSoup(errors.replace("\n", " "), "html.parser").text.strip()
            del res_json["errors"]
        if "error" in res_json:
            raise APIError("LibCal: " + res_json["error"])
        return res_json

    def cancel_room(self, booking_id, user):
        """Cancels AGH room"""
        # Optional: verify SEAS status before canceling
        # For now, allow anyone to cancel their own booking
        response = self.request("POST", f"{API_URL}/1.1/space/cancel/{booking_id}").json()
        if "error" in response[0]:
            raise APIError("LibCal: " + response[0]["error"])
        return response

    def get_availability(self, gid, start, end, user):
        """
        Returns a list of AGH rooms and their availabilities.
        Filter to only rooms the user is authorized for.
        """
        # First check SEAS membership
        try:
            authorized_rooms = self.get_authorized_rooms(user)
        except APIError:
            return []

        if not authorized_rooms:
            return []

        # Fetch availability from LibCal using AGH credentials
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

        # Get items for AGH category
        response = self.request("GET", f"{API_URL}/1.1/space/category/{gid}").json()
        items = response[0]["items"]
        items = ",".join([str(item) for item in items])

        response = self.request("GET", f"{API_URL}/1.1/space/item/{items}?{range_str}")

        if response.status_code != 200:
            raise APIError(f"AGH Reserve: Error {response.status_code} when fetching availability")

        all_rooms = response.json()

        # Filter to authorized rooms using proper name mapping
        authorized_extensions = set(authorized_rooms.keys())

        filtered_rooms = []
        for room in all_rooms:
            room_name = room.get("name", "")

            # Use proper room name mapping instead of substring matching
            if self.is_room_authorized(room_name, authorized_extensions):
                filtered_rooms.append(
                    {
                        "room_name": room["name"],
                        "id": room["id"],
                        "availability": [
                            {"start_time": time["from"], "end_time": time["to"]}
                            for time in room.get("availability", [])
                            if (
                                not start_datetime
                                or datetime.datetime.strptime(
                                    time["from"][:-6], "%Y-%m-%dT%H:%M:%S"
                                )
                                >= start_datetime
                            )
                        ],
                    }
                )

        return filtered_rooms

    def get_reservations(self, user):
        """
        LibCal doesn't provide per-user reservations.
        This is handled via database queries in BookingHandler.
        """
        pass


class LibCalBookingWrapper(AbstractBookingWrapper):
    def __init__(self):
        self.token = None
        self.expiration = timezone.localtime()

    def update_token(self):
        # does not get new token if the current one is still usable
        if self.expiration > timezone.localtime():
            return
        body = {
            "client_id": settings.GENERAL_LIBCAL_ID,
            "client_secret": settings.GENERAL_LIBCAL_SECRET,
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

    def book_room(self, rid, start, end, user):
        """
        Books room if pennkey is valid

        If this ever breaks for certain rooms but not others, 99% chance the
        questions changed and we are not supplying the right answers
        """

        # turns parameters into valid json format, then books room
        payload = {
            "start": start,
            "fname": user.first_name,
            "lname": user.last_name,
            "email": user.email,
            "nickname": f"{user.username} GSR Booking",
            "q43": f"{user.username} GSR Booking",
            "bookings": [{"id": rid, "to": end}],
            "test": False,
            "q2555": "4-5",  # corresponds to radio button
            "q2537": "4-5",  # corresponds to radio button
            "q3699": self.get_affiliation(user.email),
            "q2533": "000-000-0000",
            "q16801": "4",  # has to be between 2 and 4
            "q16802": "5",  # has to be between 5 and 10
            "q16805": "Yes",  # has to be "Yes"
            "q16804": "Yes",  # has to be "Yes"
        }

        response = self.request("POST", f"{API_URL}/1.1/space/reserve", json=payload)

        if response.status_code != 200:
            raise APIError(f"GSR Reserve: Error {response.status_code} when reserving data")

        res_json = response.json()
        # corrects keys in response
        if "error" not in res_json and "errors" in res_json:
            errors = res_json["errors"]
            if isinstance(errors, list):
                errors = " ".join(errors)
            res_json["error"] = BeautifulSoup(errors.replace("\n", " "), "html.parser").text.strip()
            del res_json["errors"]
        if "error" in res_json:
            raise APIError("LibCal: " + res_json["error"])
        return res_json

    def get_reservations(self, user):
        pass

    def cancel_room(self, booking_id, user):
        """Cancels room"""
        response = self.request("POST", f"{API_URL}/1.1/space/cancel/{booking_id}").json()
        if "error" in response[0]:
            raise APIError("LibCal: " + response[0]["error"])
        return response

    def get_availability(self, gid, start, end, user):
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

        # filters categories and then gets extra information on each room

        response = self.request("GET", f"{API_URL}/1.1/space/category/{gid}").json()
        items = response[0]["items"]
        items = ",".join([str(item) for item in items])
        response = self.request("GET", f"{API_URL}/1.1/space/item/{items}?{range_str}")

        if response.status_code != 200:
            raise APIError(f"GSR Reserve: Error {response.status_code} when reserving data")

        rooms = [
            {"room_name": room["name"], "id": room["id"], "availability": room["availability"]}
            for room in response.json()
            if room["id"] not in ROOM_BLACKLIST
        ]
        for room in rooms:
            # remove extra fields
            if "formid" in room:
                del room["formid"]
            # enforce date filter
            # API returns dates outside of the range, fix this manually
            room["availability"] = [
                {"start_time": time["from"], "end_time": time["to"]}
                for time in room["availability"]
                if not start_datetime
                or datetime.datetime.strptime(time["from"][:-6], "%Y-%m-%dT%H:%M:%S")
                >= start_datetime
            ]
        return rooms

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


class BookingHandler:
    def __init__(self, WBW=None, LBW=None, PBW=None):
        self.WBW = WBW or WhartonBookingWrapper()
        self.LBW = LBW or LibCalBookingWrapper()
        self.PBW = PBW or PennGroupsBookingWrapper()

    def format_members(self, members):
        PREFIX = "user__"
        return [
            (
                User(
                    **{k[len(PREFIX) :]: v for k, v in member.items() if k.startswith(PREFIX)}
                ),  # temp user object
                member["credits"],
            )
            for member in members
        ]

    def get_wharton_members(self, group, gsr_id):
        now = timezone.localtime()
        ninty_min = datetime.timedelta(minutes=90)
        zero_min = datetime.timedelta(minutes=0)

        # Wharton allows 90 minutes at a time
        ret = (
            GroupMembership.objects.filter(group=group, is_wharton=True)
            .values("user")
            .annotate(
                credits=ninty_min
                - Coalesce(
                    Sum(
                        F("user__gsrbooking__end") - F("user__gsrbooking__start"),
                        filter=Q(user__gsrbooking__gsr__gid=gsr_id)
                        & Q(user__gsrbooking__is_cancelled=False)
                        & Q(user__gsrbooking__end__gte=now),
                    ),
                    zero_min,
                )
            )
            .filter(Q(credits__gt=zero_min))
            .values("user__id", "user__username", "credits")
            .order_by("?")[:WHARTON_CREDIT_LIMIT]
        )
        return self.format_members(ret)

    def get_libcal_members(self, group):
        day_start = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + datetime.timedelta(days=1)
        two_hours = datetime.timedelta(hours=2)
        zero_min = datetime.timedelta(minutes=0)

        # LibCal allows 2 hours a day, needs extra user fields for booking purposes
        ret = (
            GroupMembership.objects.filter(group=group)
            .values("user")
            .annotate(
                credits=two_hours
                - Coalesce(
                    Sum(
                        F("user__gsrbooking__end") - F("user__gsrbooking__start"),
                        filter=Q(user__gsrbooking__gsr__kind=GSR.KIND_LIBCAL)
                        & Q(user__gsrbooking__is_cancelled=False)
                        & Q(user__gsrbooking__start__gte=day_start)
                        & Q(user__gsrbooking__end__lte=day_end),
                    ),
                    zero_min,
                )
            )
            .filter(Q(credits__gt=zero_min))
            .values(
                "user__id",
                "user__username",
                "user__first_name",
                "user__last_name",
                "user__email",
                "credits",
            )
            .order_by("?")[:LIBCAL_CREDIT_LIMIT]
        )
        return self.format_members(ret)

    def get_seas_members(self, group):
        """Get SEAS members with LibCal-style credits for AGH bookings"""
        day_start = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + datetime.timedelta(days=1)
        two_hours = datetime.timedelta(hours=2)
        zero_min = datetime.timedelta(minutes=0)

        # AGH/SEAS allows 2 hours a day, same as regular LibCal
        ret = (
            GroupMembership.objects.filter(group=group, is_seas=True)
            .values("user")
            .annotate(
                credits=two_hours
                - Coalesce(
                    Sum(
                        F("user__gsrbooking__end") - F("user__gsrbooking__start"),
                        filter=Q(user__gsrbooking__gsr__kind=GSR.KIND_PENNGROUPS)
                        & Q(user__gsrbooking__is_cancelled=False)
                        & Q(user__gsrbooking__start__gte=day_start)
                        & Q(user__gsrbooking__end__lte=day_end),
                    ),
                    zero_min,
                )
            )
            .filter(Q(credits__gt=zero_min))
            .values(
                "user__id",
                "user__username",
                "user__first_name",
                "user__last_name",
                "user__email",
                "credits",
            )
            .order_by("?")[:LIBCAL_CREDIT_LIMIT]
        )
        return self.format_members(ret)

    def book_room(self, gid, rid, room_name, start, end, user, group=None):
        """Book a room using the appropriate wrapper based on the GSR kind"""
        # NOTE when booking with a group, we are only querying our db for existing bookings,
        # so users in a group who book through wharton may screw up the query
        gsr = get_object_or_404(GSR, gid=gid)
        start = datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%S%z")
        end = datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%S%z")

        # Determine which wrapper and members to use based on GSR kind
        if gsr.kind == GSR.KIND_WHARTON:
            book_func = self.WBW.book_room
            members = (
                [(user, datetime.timedelta(days=99))]
                if group is None
                else self.get_wharton_members(group, gsr.id)
            )
        elif gsr.kind == GSR.KIND_PENNGROUPS:
            book_func = self.PBW.book_room
            members = (
                [(user, datetime.timedelta(days=99))]
                if group is None
                else self.get_seas_members(group)
            )
        else:  # LIBCAL
            book_func = self.LBW.book_room
            members = (
                [(user, datetime.timedelta(days=99))]
                if group is None
                else self.get_libcal_members(group)
            )

        total_time_available = sum(
            [time_available for _, time_available in members], datetime.timedelta(minutes=0)
        )

        if (end - start) >= total_time_available:
            raise APIError("Error: Not enough credits")

        reservation = Reservation.objects.create(start=start, end=end, creator=user, group=group)

        curr_start = start
        try:
            for curr_user, time_available in members:
                curr_end = curr_start + min(time_available, end - curr_start)

                booking_id = book_func(
                    rid,
                    curr_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    curr_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    curr_user,
                )["booking_id"]
                booking = GSRBooking.objects.create(
                    user_id=curr_user.id,
                    booking_id=str(booking_id),
                    gsr=gsr,
                    room_id=rid,
                    room_name=room_name,
                    start=curr_start,
                    end=curr_end,
                )
                booking.reservation = reservation
                booking.save()

                if (curr_start := curr_end) >= end:
                    break
        except APIError as e:
            raise APIError(
                f"{str(e)}. Was only able to book {start.strftime('%H:%M')}"
                f" - {curr_start.strftime('%H:%M')}"
            )

        return reservation

    def cancel_room(self, booking_id, user):
        if (
            gsr_booking := GSRBooking.objects.filter(booking_id=booking_id)
            .prefetch_related(Prefetch("reservation__gsrbooking_set"), Prefetch("gsr"))
            .first()
        ):
            if gsr_booking.user != user and gsr_booking.reservation.creator != user:
                raise APIError("Error: Unauthorized: This reservation was booked by someone else.")

            # Select appropriate wrapper based on GSR kind
            if gsr_booking.gsr.kind == GSR.KIND_WHARTON:
                cancel_func = self.WBW.cancel_room
            elif gsr_booking.gsr.kind == GSR.KIND_PENNGROUPS:
                cancel_func = self.PBW.cancel_room
            else:  # LIBCAL
                cancel_func = self.LBW.cancel_room

            cancel_func(booking_id, gsr_booking.user)

            gsr_booking.is_cancelled = True
            gsr_booking.save()

            reservation = gsr_booking.reservation
            if all(booking.is_cancelled for booking in reservation.gsrbooking_set.all()):
                reservation.is_cancelled = True
                reservation.save()
        else:
            # Try all services if booking not in our database
            for service in [self.WBW, self.LBW, self.PBW]:
                try:
                    service.cancel_room(booking_id, user)
                    return
                except APIError:
                    pass
            raise APIError("Error: Unknown booking id")

    def get_availability(self, lid, gid, start, end, user, group=None):
        gsr = get_object_or_404(GSR, gid=gid)

        # select a random user from the group if booking wharton gsr
        if gsr.kind == GSR.KIND_WHARTON and group is not None:
            wharton_members = group.memberships.filter(is_wharton=True)
            if (n := wharton_members.count()) == 0:
                raise APIError("Error: Non Wharton cannot book Wharton GSR")
            user = wharton_members[randint(0, n - 1)].user

        # Select appropriate wrapper based on GSR kind
        if gsr.kind == GSR.KIND_WHARTON:
            rooms = self.WBW.get_availability(lid, start, end, user)
        elif gsr.kind == GSR.KIND_PENNGROUPS:
            rooms = self.PBW.get_availability(gid, start, end, user)
        else:  # LIBCAL
            rooms = self.LBW.get_availability(gid, start, end, user)

        return {"name": gsr.name, "gid": gsr.gid, "rooms": rooms}

    def get_reservations(self, user, group=None):
        q = Q(user=user) | Q(reservation__creator=user) if group else Q(user=user)
        bookings = GSRBooking.objects.filter(
            q, is_cancelled=False, end__gte=timezone.localtime()
        ).prefetch_related(Prefetch("reservation"))

        if group:
            ret = []
            for booking in bookings:
                data = GSRBookingSerializer(booking).data
                if booking.reservation.creator == user:
                    data["room_name"] = f"[Me] {data['room_name']}"
                else:
                    data["room_name"] = f"[{group.name}] {data['room_name']}"
                ret.append(data)
        else:
            ret = GSRBookingSerializer(bookings, many=True).data

        # deal with bookings made directly through wharton (not us)
        try:
            wharton_bookings = self.WBW.get_reservations(user)
        except APIError:
            return ret

        if len(wharton_bookings) == 0:
            return ret

        booking_ids = set([booking["booking_id"] for booking in ret])
        wharton_bookings = [
            booking for booking in wharton_bookings if booking["booking_id"] not in booking_ids
        ]
        if len(wharton_bookings) == 0:
            return ret

        wharton_gsr_datas = {
            gsr.gid: GSRSerializer(gsr).data for gsr in GSR.objects.filter(kind=GSR.KIND_WHARTON)
        }
        for booking in wharton_bookings:
            booking["gsr"] = wharton_gsr_datas[booking["gid"]]
            del booking["gid"]
            ret.append(booking)
        return ret

    # seems like its unused on the frontend
    # def check_credits(self, user):
    #     pass


# initialize singletons
WhartonGSRBooker = WhartonBookingWrapper()
LibCalGSRBooker = LibCalBookingWrapper()
PennGroupsGSRBooker = PennGroupsBookingWrapper()
GSRBooker = BookingHandler(WhartonGSRBooker, LibCalGSRBooker, PennGroupsGSRBooker)
