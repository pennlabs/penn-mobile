from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse

from dining.helpers import (
    balance,
    get_average_balances,
    get_frequent_locations,
    get_prediction_dollars,
    get_prediction_swipes,
    get_semester_start_end,
    recent_transactions_card,
    update_if_not_none,
)
from legacy.models import Account
from studentlife.utils import date_iso_eastern


# from pytz import timezone


"""
START NEW
"""

import csv
import datetime

from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from dining.api_wrapper import dining_request, get_meals, normalize_weekly, APIError


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


class Venues(APIView):
    '''
    GET: returns list of venue data provided by Penn API, as well as an image of the venue
    '''

    def get(self, request):
        try:
            response = dining_request(V2_ENDPOINTS["VENUES"])["result_data"]
        except APIError as e:
            return Response({'error': e.args})

        venues = response["document"]["venue"]

        # adds dining hall image to associated dining hall
        for venue in venues:
            with open("dining/data/dining_images.csv") as data:
                reader = csv.reader(data)
                for i, row in enumerate(reader):
                    uuid, url = row
                    if uuid == str(venue["id"]):
                        venue["imageURL"] = url

        return Response(response)


class Hours(APIView):
    '''
    GET: Returns info on open and closing hours for a particular venue
    '''

    def get(self, request, venue_id):
        try:
            response = dining_request(V2_ENDPOINTS["HOURS"] + venue_id)["result_data"]
        except APIError as e:
            return Response({'error': e.args})

        return Response(response)


class WeeklyMenu(APIView):
    '''
    GET: Returns data on weekly menu for a particular venue
    '''

    def get(self, request, venue_id):
        response = {"result_data": {"Document": {}}}
        days = []
        for i in range(7):
            date = str(timezone.localtime().date() + datetime.timedelta(days=i))
            try:
                v2_response = dining_request(V2_ENDPOINTS["MENUS"] + venue_id + "&date=" + date)
            except APIError as e:
                return Response({'error': e.args})

            if venue_id in VENUE_NAMES:
                response["result_data"]["Document"]["location"] = VENUE_NAMES[venue_id]
            else:
                response["result_data"]["Document"]["location"] = v2_response["result_data"][
                    "days"
                ][0]["cafes"][venue_id]["name"]
            formatted_date = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%-m/%d/%Y")
            days.append(
                {"tblDayPart": get_meals(v2_response, venue_id), "menudate": formatted_date}
            )
        response["result_data"]["Document"]["tblMenu"] = days

        return Response(normalize_weekly(response)["result_data"])


class DailyMenu(APIView):
    '''
    GET: Returns data on daily menu for a particular venue
    '''

    def get(self, request, venue_id):
        date = str(timezone.localtime().date())
        try:
            v2_response = dining_request(V2_ENDPOINTS["MENUS"] + venue_id + "&date=" + date)
        except APIError as e:
            return Response({'error': e.args})

        response = {"result_data": {"Document": {}}}
        response["result_data"]["Document"]["menudate"] = datetime.datetime.strptime(
            date, "%Y-%m-%d"
        ).strftime("%-m/%d/%Y")
        if venue_id in VENUE_NAMES:
            response["result_data"]["Document"]["location"] = VENUE_NAMES[venue_id]
        else:
            response["result_data"]["Document"]["location"] = v2_response["result_data"]["days"][0][
                "cafes"
            ][venue_id]["name"]
        response["result_data"]["Document"]["tblMenu"] = {
            "tblDayPart": get_meals(v2_response, venue_id)
        }
        return Response(response["result_data"])


class DiningItem(APIView):
    '''
    GET: Returns data on a particular item
    '''

    def get(self, request, item_id):
        try:
            response = dining_request(V2_ENDPOINTS["ITEMS"] + item_id)
        except APIError as e:
            return Response({'error': e.args})
        return Response(response["result_data"])

"""
END NEW
"""


class Dashboard(APIView):
    """
    Dining Dashboard containing user's balance and transaction info.

    Methods
    -------
    get(request, format=None)
        returns json for user's dining info using helpers.py methods.
    """

    def get(self, request, format=None):
        if not self.request.user.is_authenticated:
            return HttpResponseForbidden()

        pennkey = request.user.username

        try:
            uid = Account.objects.get(pennkey=pennkey).id
        except Account.DoesNotExist:
            return HttpResponseBadRequest()

        json = {}

        start, end = get_semester_start_end()

        # set all timezones to eastern to be consistent with ISO date format
        # that iOS accepts. Also resets tzinfo that DB might add to allow for
        # consistent comparison.
        eastern = timezone("US/Eastern")
        start = start.replace(tzinfo=eastern, hour=0, minute=0, second=0, microsecond=0)
        end = end.replace(tzinfo=eastern, hour=0, minute=0, second=0, microsecond=0)
        json["start-of-semester"] = date_iso_eastern(start)
        json["end-of-semester"] = date_iso_eastern(end)

        bal = balance(uid)

        # if not on dining plan only return these fields
        if bal is None:
            json["cards"] = {}
            return JsonResponse(json)

        json.update(bal)

        json["cards"] = {"recent-transactions": recent_transactions_card(uid)}
        update_if_not_none(json["cards"], "daily-average", get_average_balances(uid, start))
        update_if_not_none(
            json["cards"], "predictions-graph-dollars", get_prediction_dollars(uid, start, end),
        )
        update_if_not_none(
            json["cards"], "predictions-graph-swipes", get_prediction_swipes(uid, start, end),
        )
        update_if_not_none(
            json["cards"], "frequent-locations", get_frequent_locations(uid, start, end)
        )

        return JsonResponse(json)
