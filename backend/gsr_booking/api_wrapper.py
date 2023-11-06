import datetime
from enum import Enum
from abc import ABC, abstractmethod

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.timezone import make_aware
from requests.exceptions import ConnectionError, ConnectTimeout, ReadTimeout
from django.db.models import Q, F, Sum, Prefetch
from django.db.models.functions import Coalesce
from gsr_booking.models import GSR, Group, GroupMembership, GSRBooking, Reservation
from gsr_booking.serializers import GSRBookingSerializer, GSRSerializer
from random import randint
from django.contrib.auth import get_user_model

User = get_user_model()


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

class AbstractBookingWrapper(ABC):
    @abstractmethod
    def book_room(self, rid, start, end, user):
        pass
    
    @abstractmethod
    def cancel_room(self, booking_id, user):
        pass

    @abstractmethod
    def get_availability(self, lid, start, end, user):
        pass

    @abstractmethod
    def get_reservations(self, user):
        pass

    # @abstractmethod
    # def check_credits(self, user):
    #     pass

class WhartonBookingWrapper(AbstractBookingWrapper):
    def request(self, *arg, **kwargs):
        """Make a signed request to the libcal API."""
        # add authorization headers
        kwargs["headers"] = {"Authorization": f"Token {settings.WHARTON_TOKEN}"}
    
        try:
            response = requests.request(*arg, **kwargs)
        except (ConnectTimeout, ReadTimeout, ConnectionError):
            raise APIError("Wharton: Connection timeout")

        # only wharton students can access these routes
        if response.status_code == 403 or response.status_code == 401:
            raise APIError("Wharton: GSR view restricted to Wharton Pennkeys")
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
    
    def get_reservations(self, user):
        url = f"{WHARTON_URL}{user.username}/reservations"
        bookings = self.request("GET", url).json()["bookings"]

        bookings = [booking for booking in bookings if datetime.datetime.strptime(booking["end"], "%Y-%m-%dT%H:%M:%S%z") >= timezone.localtime()]

        return [
            {
                "booking_id": str(booking["booking_id"]),
                "gid": booking["lid"], # their lid is our gid
                "room_id": booking["rid"], 
                "room_name": booking["room"],
                "start": booking["start"],
                "end": booking["end"],
            }
            for booking in bookings
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
            return None

class LibCalBookingWrapper(AbstractBookingWrapper):
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
    
    def request(self, *arg, **kwargs):
        """Make a signed request to the libcal API."""
        self.update_token()

        headers = {"Authorization": f"Bearer {self.token}"}

        # add authorization headers
        if "headers" in kwargs:
            kwargs["headers"].update(headers)
        else:
            kwargs["headers"] = headers
        
        try:
            return requests.request(*arg, **kwargs)
        except (ConnectTimeout, ReadTimeout, ConnectionError):
            raise APIError("LibCal: Connection timeout")
        
    def book_room(self, rid, start, end, user):
        """Books room if pennkey is valid"""
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
            "q2555": "5",
            "q2537": "5",
            "q3699": self.get_affiliation(user.email),
            "q2533": "000-000-0000",
            "q16801": "5",
            "q16802": "5",
            "q16805": "Yes",
            "q16804": "Yes",
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
            res_json["error"] = BeautifulSoup(
                errors.replace("\n", " "), "html.parser"
            ).text.strip()
            del res_json["errors"]
        if "error" in res_json:
            raise APIError("LibCal: " + res_json["error"])
        return res_json

    def get_reservations(self, user):
        pass

    def cancel_room(self, booking_id, user):
        """Cancels room"""
        # gsr_booking = get_object_or_404(GSRBooking, booking_id=booking_id)
        # if gsr_booking:
        #     if user != gsr_booking.user and user != gsr_booking.reservation.creator:
        #         raise APIError("Error: Unauthorized: This reservation was booked by someone else.")
        #     gsr_booking.is_cancelled = True
        #     gsr_booking.save()
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
        items = ",".join([str(x) for x in items])
        response = self.request("GET", f"{API_URL}/1.1/space/item/{items}?{range_str}")

        if response.status_code != 200:
            raise APIError(f"GSR Reserve: Error {response.status_code} when reserving data")
        
        rooms = [{"room_name": room['name'], 'id': room['id'], 'availability': room['availability']} for room in response.json() if room["id"] not in ROOM_BLACKLIST]
        for room in rooms:
            # remove extra fields
            if "formid" in room:
                del room["formid"]
            # enforce date filter
            # API returns dates outside of the range, fix this manually
            room["availability"] = [
                {
                    'start_time': time['from'],
                    'end_time': time['to']
                }
                for time in room["availability"]
                if not start_datetime or datetime.datetime.strptime(time["from"][:-6], "%Y-%m-%dT%H:%M:%S") >= start_datetime
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
    def __init__(self, WBW=None, LBW=None):
        self.WBW = WBW or WhartonBookingWrapper()
        self.LBW = LBW or LibCalBookingWrapper()


    def format_members(self, members):
        return [
            (User(**{ k[6:]: v for k, v in member.items() if k.startswith('user__') }), # temp user object
            member['left'])
            for member in members
        ]

    def get_wharton_members(self, group, gsr_id):
        now = timezone.localtime()
        ninty_min = datetime.timedelta(minutes=90)
        zero_min = datetime.timedelta(minutes=0)
        ret = GroupMembership.objects.filter(group=group, is_wharton=True).values('user').annotate(left=ninty_min-Coalesce(Sum(
            F('user__gsrbooking__end')-F('user__gsrbooking__start'),
            filter=Q(user__gsrbooking__gsr__gid=gsr_id) & Q(user__gsrbooking__is_cancelled=False) & Q(user__gsrbooking__end__gte=now)
        ), zero_min)).filter(Q(left__gt=zero_min)).values('user__id', 'user__username', 'left').order_by('?')[:3]
        return self.format_members(ret)

        # locally i get this:
        # SELECT "auth_user"."username", (5400000000 - COALESCE(SUM(django_timestamp_diff("gsr_booking_gsrbooking"."end", "gsr_booking_gsrbooking"."start")) FILTER (WHERE ("gsr_booking_gsr"."gid" = 1 AND NOT "gsr_booking_gsrbooking"."is_cancelled" AND "gsr_booking_gsrbooking"."end" >= 2023-10-22 20:04:00.804135)), 0)) AS "left" FROM "gsr_booking_groupmembership" LEFT OUTER JOIN "auth_user" ON ("gsr_booking_groupmembership"."user_id" = "auth_user"."id") LEFT OUTER JOIN "gsr_booking_gsrbooking" ON ("auth_user"."id" = "gsr_booking_gsrbooking"."user_id") LEFT OUTER JOIN "gsr_booking_gsr" ON ("gsr_booking_gsrbooking"."gsr_id" = "gsr_booking_gsr"."id") WHERE ("gsr_booking_groupmembership"."group_id" = 3 AND "gsr_booking_groupmembership"."is_wharton") GROUP BY "gsr_booking_groupmembership"."user_id", "auth_user"."username" HAVING (5400000000 - COALESCE(SUM(django_timestamp_diff("gsr_booking_gsrbooking"."end", "gsr_booking_gsrbooking"."start")) FILTER (WHERE ("gsr_booking_gsr"."gid" = 1 AND NOT "gsr_booking_gsrbooking"."is_cancelled" AND "gsr_booking_gsrbooking"."end" >= 2023-10-22 20:04:00.804135)), 0)) > 0 ORDER BY RAND() ASC LIMIT 3

    def get_libcal_members(self, group):
        day_start = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + datetime.timedelta(days=1)
        two_hours = datetime.timedelta(hours=2)
        zero_min = datetime.timedelta(minutes=0)

        ret = GroupMembership.objects.filter(group=group).values('user').annotate(left=two_hours-Coalesce(Sum(
            F('user__gsrbooking__end')-F('user__gsrbooking__start'),
            filter=Q(user__gsrbooking__gsr__kind=GSR.KIND_LIBCAL) & Q(user__gsrbooking__is_cancelled=False) & Q(user__gsrbooking__start__gte=day_start) & Q(user__gsrbooking__end__lte=day_end)
        ), zero_min)).filter(Q(left__gt=zero_min)).values('user__id', 'user__username', 'user__first_name', 'user__last_name', 'user__email', 'left').order_by('?')[:4]
        return self.format_members(ret)
    
        # SELECT "auth_user"."username", (7200000000 - COALESCE(SUM(django_timestamp_diff("gsr_booking_gsrbooking"."end", "gsr_booking_gsrbooking"."start")) FILTER (WHERE ("gsr_booking_gsr"."kind" = LIBCAL AND NOT "gsr_booking_gsrbooking"."is_cancelled" AND "gsr_booking_gsrbooking"."start" >= 2023-10-30 04:00:00 AND "gsr_booking_gsrbooking"."end" <= 2023-10-31 04:00:00)), 0)) AS "left" FROM "gsr_booking_groupmembership" LEFT OUTER JOIN "auth_user" ON ("gsr_booking_groupmembership"."user_id" = "auth_user"."id") LEFT OUTER JOIN "gsr_booking_gsrbooking" ON ("auth_user"."id" = "gsr_booking_gsrbooking"."user_id") LEFT OUTER JOIN "gsr_booking_gsr" ON ("gsr_booking_gsrbooking"."gsr_id" = "gsr_booking_gsr"."id") WHERE "gsr_booking_groupmembership"."group_id" = 3 GROUP BY "gsr_booking_groupmembership"."user_id", "auth_user"."username" HAVING (7200000000 - COALESCE(SUM(django_timestamp_diff("gsr_booking_gsrbooking"."end", "gsr_booking_gsrbooking"."start")) FILTER (WHERE ("gsr_booking_gsr"."kind" = LIBCAL AND NOT "gsr_booking_gsrbooking"."is_cancelled" AND "gsr_booking_gsrbooking"."start" >= 2023-10-30 04:00:00 AND "gsr_booking_gsrbooking"."end" <= 2023-10-31 04:00:00)), 0)) > 0 ORDER BY RAND() ASC LIMIT 4

    def book_room(self, gid, rid, room_name, start, end, user, group=None):
        # NOTE when booking with a group, we are only querying our db for existing bookings, so users in a group who book through wharton may screw up the query
        gsr = get_object_or_404(GSR, gid=gid)
        start=datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%S%z")
        end=datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%S%z")

        book_func = self.WBW.book_room if gsr.kind == GSR.KIND_WHARTON else self.LBW.book_room
        members = [(user, datetime.timedelta(days=99))] if group is None else self.get_wharton_members(group, gsr.id) if gsr.kind == GSR.KIND_WHARTON else self.get_libcal_members(group) 
        
        total_time_available = sum([time_available for _, time_available in members], datetime.timedelta(minutes=0))

        if (end - start) >= total_time_available:
            raise APIError("Error: Not enough credits")
        
        reservation = Reservation.objects.create(
            start=start, end=end, creator=user, group=Group.objects.get_or_create(name="Me", owner=user)[0] if group is None else group
              # we should allow None groups and get rid of Me Groups
        )

        curr_start = start
        try: 
            for curr_user, time_available in members:
                curr_end = curr_start + min(time_available, end-curr_start)
                

                booking_id = book_func(rid, curr_start.strftime("%Y-%m-%dT%H:%M:%S%z"), curr_end.strftime("%Y-%m-%dT%H:%M:%S%z"), curr_user)["booking_id"]
                booking = GSRBooking.objects.create(
                    user_id=curr_user.id,
                    booking_id=str(booking_id),
                    gsr=gsr,
                    room_id=rid,
                    room_name=room_name,
                    start=curr_start,
                    end=curr_end
                )            
                booking.reservation = reservation
                booking.save()

                if (curr_start := curr_end) >= end:
                    break
        except APIError as e:
            raise APIError(f"{str(e)}. Was only able to book {start.strftime('%H:%M')} - {curr_start.strftime('%H:%M')}")

        return reservation
    
    def cancel_room(self, booking_id, user):
        # I think this should prefetch reservation, reservation__gsrbooking_set, and gsr ?
        if gsr_booking := GSRBooking.objects.filter(booking_id=booking_id).prefetch_related(Prefetch('reservation__gsrbooking_set'), Prefetch('gsr')).first():
            if gsr_booking.user != user and gsr_booking.reservation.creator != user:
                raise APIError("Error: Unauthorized: This reservation was booked by someone else.")
            
            (self.WBW.cancel_room if gsr_booking.gsr.kind == GSR.KIND_WHARTON else self.LBW.cancel_room)(booking_id, gsr_booking.user)
            
            gsr_booking.is_cancelled = True
            gsr_booking.save()

            reservation = gsr_booking.reservation
            if all(booking.is_cancelled for booking in reservation.gsrbooking_set.all()):
                reservation.is_cancelled = True
                reservation.save()                
        else:
            try: 
                self.WBW.cancel_room(booking_id, user)
            except APIError:
                try: 
                    self.LBW.cancel_room(booking_id, user)
                except APIError:
                    raise APIError("Error: Unknown booking id")
                
        
    def get_availability(self, lid, gid, start, end, user, group=None):            
        gsr = get_object_or_404(GSR, gid=gid)

        # select a random user from the group if booking wharton gsr
        if gsr.kind == GSR.KIND_WHARTON and group is not None:
            wharton_members = group.memberships.filter(is_wharton=True)
            if (n := wharton_members.count()) == 0:
                raise APIError("Error: Non Wharton cannot book Wharton GSR")
            user = wharton_members[randint(0, n-1)].user
        
        rooms = self.WBW.get_availability(lid, start, end, user) if gsr.kind == GSR.KIND_WHARTON else self.LBW.get_availability(gid, start, end, user)
        return {"name": gsr.name, "gid": gsr.gid, "rooms": rooms}

    
    def get_reservations(self, user, group=None):
        q = Q(user=user) | Q(reservation__creator=user) if group else Q(user=user)
        bookings = GSRBooking.objects.filter(q, is_cancelled=False, end__gte=timezone.localtime()).prefetch_related(Prefetch('reservation'))

        if group:
            ret = []
            for booking in bookings:
                data = GSRBookingSerializer(booking).data
                if booking.reservation.creator == user:
                    data['room_name'] = f"[Me] {data['room_name']}"
                else:
                    data['room_name'] = f"[{group.name}] {data['room_name']}"
                ret.append(data)
        else:
            ret = GSRBookingSerializer(bookings, many=True).data
        
        # deal with bookings made directly through wharton (not us)
        try:
            wharton_bookings = self.WBW.get_reservations(user) # is this bad? 
        except APIError:
            return ret
        
        if len(wharton_bookings) == 0:  
            return ret
    
        booking_ids = set([booking['booking_id'] for booking in ret])
        wharton_bookings = [booking for booking in wharton_bookings if booking['booking_id'] not in booking_ids]
        if len(wharton_bookings) == 0:
            return ret    

        wharton_gsr_datas = {gsr.gid: GSRSerializer(gsr).data for gsr in GSR.objects.filter(kind=GSR.KIND_WHARTON)}        
        for booking in wharton_bookings:
            if booking['booking_id'] in booking_ids:
                continue
            booking['gsr'] = wharton_gsr_datas[booking['gid']]
            del booking['gid']
            ret.append(booking)
        return ret
    
    def check_credits(self, user):
        pass # seems like its unused on the frontend


# initialize singletons
WhartonGSRBooker = WhartonBookingWrapper()
LibCalGSRBooker = LibCalBookingWrapper()
GSRBooker = BookingHandler(WhartonGSRBooker, LibCalGSRBooker)