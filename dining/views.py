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

import pytz
from bs4 import BeautifulSoup
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from dining.api_wrapper import APIError, dining_request, get_meals, normalize_weekly
from dining.models import DiningBalance, DiningPreference, DiningTransaction, Venue
from dining.serializers import DiningBalanceSerializer, DiningTransactionSerializer


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
    """
    GET: returns list of venue data provided by Penn API, as well as an image of the venue
    """

    def get(self, request):
        try:
            response = dining_request(V2_ENDPOINTS["VENUES"])["result_data"]
        except APIError as e:
            return Response({"error": e.args}, status=400)

        venues = response["document"]["venue"]

        # adds dining hall image to associated dining hall
        for venue in venues:
            image_url = Venue.objects.get(venue_id=str(venue["id"])).image_url
            venue["imageURL"] = image_url

        return Response(response)


class Hours(APIView):
    """
    GET: Returns info on open and closing hours for a particular venue
    """

    def get(self, request, venue_id):
        try:
            response = dining_request(V2_ENDPOINTS["HOURS"] + venue_id)["result_data"]
            return Response(response)
        except APIError as e:
            return Response({"error": e.args}, status=400)


class WeeklyMenu(APIView):
    """
    GET: Returns data on weekly menu for a particular venue
    """

    def get(self, request, venue_id):
        response = {"result_data": {"Document": {}}}
        days = []
        for i in range(7):
            date = str(timezone.localtime().date() + datetime.timedelta(days=i))
            try:
                v2_response = dining_request(V2_ENDPOINTS["MENUS"] + venue_id + "&date=" + date)
            except APIError as e:
                return Response({"error": e.args}, status=400)

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
    """
    GET: Returns data on daily menu for a particular venue
    """

    def get(self, request, venue_id):
        date = str(timezone.localtime().date())
        try:
            v2_response = dining_request(V2_ENDPOINTS["MENUS"] + venue_id + "&date=" + date)
        except APIError as e:
            return Response({"error": e.args}, status=400)

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
    """
    GET: Returns data on a particular item
    """

    def get(self, request, item_id):
        try:
            response = dining_request(V2_ENDPOINTS["ITEMS"] + item_id)
        except APIError as e:
            return Response({"error": e.args}, status=400)
        return Response(response["result_data"])


class Preferences(APIView):
    """
    GET: returns list of a User's diningpreferences

    POST: updates User dining preferences by clearing past preferences
    and resetting them with request data
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):

        preferences = DiningPreference.objects.filter(profile=request.user.profile)

        # aggregated venues and puts it in form {"venue_id": x, "count": x}
        aggregated_preferences = preferences.values("venue_id").annotate(count=Count("venue_id"))
        return Response({"preferences": aggregated_preferences})

    def post(self, request):

        profile = request.user.profile

        # clears all previous preferences associated with the profile
        preferences = DiningPreference.objects.filter(profile=request.user.profile)
        for preference in preferences:
            preference.delete()

        venue_ids = request.data["venues"]

        for venue_id in venue_ids:
            get_object_or_404(Venue, venue_id=int(venue_id))
            # adds all of the preferences given by the request
            DiningPreference.objects.create(profile=profile, venue_id=venue_id)

        return Response({"success": True, "error": None})


# NOTE: has NOT been fully tested yet,
# how am i able to login to LAS so that I could see it's return values?
class Transactions(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.profile

        transactions = DiningTransaction.objects.filter(profile=profile)
        serialized_data = DiningTransactionSerializer(transactions, many=True).data

        # this serializer outputs the -5:00 after the datetime
        # is this alright? i don't think LAS has this
        return Response(serialized_data)

    def post(self, request):

        profile = request.user.profile

        transaction = request.data["transactions"]

        # create list of rows, remove headers, and reverse so in order of date
        cr = csv.reader(transaction.splitlines(), delimiter=",")
        row_list = list(cr)
        row_list.pop(0)
        row_list.reverse()

        last_transaction = DiningTransaction.objects.order_by("-date").first()

        for row in row_list:
            if len(row) == 4:
                if row[0] == "No transaction history found for this date range.":
                    continue
                else:
                    date = datetime.datetime.strptime(row[0], "%m/%d/%Y %I:%M%p")
                    if last_transaction is None or date > last_transaction.date:
                        DiningTransaction.objects.create(
                            profile=profile, date=date, description=row[1], amount=float(row[2])
                        )
                        profile.dining_balance = float(row[3])
                        profile.save()

        return Response({"success": True, "error": None})


# NOTE: has NOT been fully tested yet,
# how am i able to login to LAS so that I could see it's return values?
# TODO: look into where i can get the HTML POST data
class Balance(APIView):
    def get_dst_gmt_timezone(self):
        now = datetime.datetime.now(tz=pytz.timezone("US/Eastern"))
        if now.timetuple().tm_isdst:
            return "04:00"
        else:
            return "05:00"

    def get(self, request):

        profile = request.user.profile
        balance = DiningBalance.objects.filter(profile=profile).order_by("-date").first()

        if balance is not None:
            timestamp = balance.date.strftime("%Y-%m-%dT%H:%M:%S") + "-{}".format(
                self.get_dst_gmt_timezone()
            )
            data = DiningBalanceSerializer(balance, many=False).data
            dollars = data.pop("dollars")
            data["dining_dollars"] = dollars
            data["timestamp"] = timestamp
            return Response({"balance": data})

        else:
            return Response({"balance": None})

    def post(self, request):

        profile = request.user.profile

        html = request.data["html"]
        if "You are not currently signed up" in html:
            return Response({"hasPlan": False, "balance": None, "error": None})

        soup = BeautifulSoup(html, "html.parser")
        divs = soup.findAll("div", {"class": "info-column"})
        dollars = None
        swipes = None
        guest_swipes = None
        added_swipes = None
        if len(divs) >= 4:
            for div in divs[:4]:
                if "Dining Dollars" in div.text:
                    dollars = float(div.span.text[1:])
                elif "Regular Visits" in div.text:
                    swipes = int(div.span.text)
                elif "Guest Visits" in div.text:
                    guest_swipes = int(div.span.text)
                elif "Add-on Visits" in div.text:
                    added_swipes = int(div.span.text)
        else:
            return Response(
                {"success": False, "error": "Something went wrong parsing HTML."}, status=400
            )

        total_swipes = swipes + added_swipes

        balance = DiningBalance.objects.create(
            profile=profile, dollars=dollars, swipes=total_swipes, guest_swipes=guest_swipes
        )

        return Response(
            {
                "hasPlan": True,
                "balance": DiningBalanceSerializer(balance, many=False),
                "error": None,
            }
        )


class AverageBalance(APIView):
    def get(self, request):
        pass


class Projection(APIView):
    def get(self, request):
        pass


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
