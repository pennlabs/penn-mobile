import requests
import datetime
import math
import random

MAX_SLOT_HRS = 2.0  # the longest booking allowed per person
MIN_SLOT_HRS = 0.5  # the minimum booking allowed per person


def book_room_for_group(group, is_wharton, room, lid, start, end, requester_pennkey):
    """ makes a request to labs api server to book rooms for group """
    members = group.get_pennkey_active_members()
    error = None

    if len(members) < 1:
        return {
            "complete_success": False,
            "partial_success": False,
            "error": "No members in the group have enabled their pennkey to be used for group bookings",
        }

    # randomize order, and put requester first in the order
    random.shuffle(members)
    for (i, member) in enumerate(members):  # puts the requester as the first person
        if member["username"] == requester_pennkey:
            temp = members[0]
            members[0] = member
            members[i] = temp
            break

    if is_wharton:  # huntsman reservation
        return {
            "complete_success": False,
            "partial_success": False,
            "error": "Unable to book huntsman rooms yet",
        }
    else:  # lib reservation
        # Find the first timeslot to book for (next_start, next_end)
        START_DATE = datetime.datetime.fromisoformat(start)
        END_DATE = datetime.datetime.fromisoformat(end)
        next_start = START_DATE
        next_end = min(END_DATE, next_start + datetime.timedelta(hours=MAX_SLOT_HRS))
        # loop through each member, and attempt to book on their behalf
        bookings = dict()
        failed_members = []  # store the members w/ failed bookings in here

        for member in members:
            if next_end - next_start < datetime.timedelta(hours=MIN_SLOT_HRS):
                break
            if member["user__email"] is "":
                continue  # this member cannot be used for libcal booking b/c email required

            # make 'blind-booking' request to labs-api-server first
            try:
                success = book_room_for_user(
                    room, lid, next_start.isoformat(), next_end.isoformat(), member["user__email"]
                )
                if success:
                    key = f"{lid}_{room}"
                    if not key in bookings:
                        bookings[key] = []
                    new_bookings = split_booking(next_start, next_end, member["username"], True)
                    bookings[key].extend(new_bookings)

                    next_start = next_end
                    next_end = min(END_DATE, next_start + datetime.timedelta(hours=MAX_SLOT_HRS))
                else:
                    failed_members.append(member)
            except BookingError as e:
                if is_fatal_error(e):
                    result_json = construct_bookings_json_obj(
                        bookings, lid, room, END_DATE, next_start, next_end, error
                    )
                    return result_json
                error = e

        # if unbooked slots still remain and not all booking requests succeeded, loop through each member again
        # but get reservation credits first to see how much we can book

        for member in failed_members:
            if next_end - next_start < datetime.timedelta(hours=MIN_SLOT_HRS):
                break  # booked everything already
            if member["user__email"] is "":
                continue  # this member cannot be used for libcal booking b/c email required

            # calculate number of credits already used via getReservations
            (success, used_credit_hours) = get_used_booking_credit_for_user(
                lid, member["user__email"]
            )
            remaining_credit_hours = MAX_SLOT_HRS - used_credit_hours
            rounded_remaining_credit_hours = math.floor(2 * remaining_credit_hours) / 2
            if success and remaining_credit_hours >= MIN_SLOT_HRS:
                next_end = min(
                    END_DATE, next_start + datetime.timedelta(hours=rounded_remaining_credit_hours),
                )
                try:
                    success = book_room_for_user(
                        room,
                        lid,
                        next_start.isoformat(),
                        next_end.isoformat(),
                        member["user__email"],
                    )
                    if success:
                        key = f"{lid}_{room}"
                        if not key in bookings:
                            bookings[key] = []
                        new_bookings = split_booking(next_start, next_end, member["username"], True)
                        bookings[key].extend(new_bookings)

                        next_start = next_end
                        next_end = min(
                            END_DATE, next_start + datetime.timedelta(hours=MAX_SLOT_HRS)
                        )
                except BookingError as e:
                    if is_fatal_error(e):
                        result_json = construct_bookings_json_obj(
                            bookings, lid, room, END_DATE, next_start, next_end, error
                        )
                        return result_json
                    error = e
        result_json = construct_bookings_json_obj(
            bookings, lid, room, END_DATE, next_start, next_end, error
        )
        return result_json


def is_fatal_error(error):
    # consider all errors fatal unless its a daily limit error
    if error is not None:
        if "daily limit".lower() not in (str(error)).lower():
            return False
        return True
    return False


def construct_bookings_json_obj(succesful_bookings, lid, room, end, next_start, next_end, error):
    """ 
    Takes in a set of bookings and constructs a JSON object from them (after pre-processing). For example,
    {
        "complete_success": true,
        "partial_success": true,
        "rooms": [
            {
                "lid": "2587",
                "room": "16993",
                "bookings": [
                    {
                        "start": "2020-03-06T18:00:00-05:00",
                        "end": "2020-03-06T18:30:00-05:00",
                        "pennkey": rehaan,
                        "booked": true
                    }
                ]
            }
        ]
    }
    """
    bookings = succesful_bookings
    complete_success = (next_end - next_start < datetime.timedelta(hours=MIN_SLOT_HRS)) and (
        error is None
    )
    partial_success = len(bookings) > 0
    result_json = {
        "complete_success": complete_success,
        "partial_success": partial_success,
        "rooms": [],
    }

    # add failed bookings to bookings
    failed_bookings = split_booking(next_start, end, None, False)
    failed_key = f"{lid}_{room}"
    if not failed_key in bookings:
        bookings[failed_key] = []
    failed_split_bookings = split_booking(next_start, next_end, None, False)
    bookings[failed_key].extend(failed_split_bookings)

    # add successful bookings to result_json
    for (key, bookings_array) in bookings.items():
        key_split = key.split("_")
        lid = key_split[0]
        room = key_split[1]
        result_json["rooms"].append({"lid": lid, "room": room, "bookings": bookings_array})

    # handle potential error
    if error is not None:
        if "not a valid".lower() in str(error).lower():
            result_json["error"] = "Attempted to book for an invalid time slot"
        elif "daily limit".lower() in str(error).lower():
            result_json["error"] = "Group does not have sufficient booking credits"
        else:
            result_json["error"] = str(error)
    elif complete_success is False:
        result_json["error"] = "Group does not have sufficient booking credits"
    return result_json


def get_used_booking_credit_for_user(lid, email):
    """ returns a user's used booking credit (in hours) for a specific building (lid) """
    RESERVATIONS_URL = "https://api.pennlabs.org/studyspaces/reservations"
    if lid == "1":
        return (False, 0)  # doesn't support huntsman yet
    try:
        r = requests.get(RESERVATIONS_URL + "?email=" + email)
        if r.status_code == 200:
            resp_data = r.json()
            reservations = resp_data["reservations"]
            used_credit_hours = 0
            for reservation in reservations:
                from_date = datetime.datetime.fromisoformat(reservation["fromDate"])
                to_date = datetime.datetime.fromisoformat(reservation["toDate"])
                reservation_hours = (to_date - from_date).total_seconds() / 3600
                if str(reservation["lid"]) == lid and reservation_hours >= MIN_SLOT_HRS:
                    used_credit_hours += reservation_hours
            return (True, used_credit_hours)
    except requests.exceptions.RequestException as e:
        print(e)
    return (False, 0)


def split_booking(start, end, pennkey, booked):
    """
    splits a booking into smaller bookings (of min_slot_hrs) for displaying to user
    """
    bookings = []
    temp_start = start
    temp_end = temp_start + datetime.timedelta(hours=MIN_SLOT_HRS)
    while end - temp_start >= datetime.timedelta(hours=MIN_SLOT_HRS):
        booking_obj = {
            "start": temp_start.isoformat(),
            "end": temp_end.isoformat(),
            "booked": booked,
        }
        if pennkey is not None:
            booking_obj["pennkey"] = pennkey
        bookings.append(booking_obj)
        temp_start = temp_end
        temp_end += datetime.timedelta(hours=MIN_SLOT_HRS)
    return bookings


def book_room_for_user(room, lid, start, end, email):
    """ 
    Tries to make a booking for an individual user, and returns success or not (and the error) in a tuple
    """
    if lid is "1":
        return False  # does not support huntsman booking yet
    BOOKING_URL = "https://api.pennlabs.org/studyspaces/book"
    form_data = {
        "firstname": "Group GSR User",
        "lastname": "Group GSR User",
        "groupname": "Group GSR",
        "size": "2-3",
        "phone": "2158986533",
        "room": room,
        "lid": lid,
        "start": start,
        "end": end,
        "email": email,
    }

    try:
        r = requests.post(BOOKING_URL, data=form_data)
        if r.status_code == 200:
            resp_data = r.json()
            if "error" in resp_data and resp_data["error"] is not None:
                raise BookingError(resp_data["error"])
            return resp_data["results"]
    except requests.exceptions.RequestException as e:
        print("error: " + str(e))
    return False


class BookingError(Exception):
    def __init__(self, error_str):
        self.error_str = error_str

    def __str__(self):
        return self.error_str
