from dining.helpers import (
    balance,
    get_average_balances,
    get_frequent_locations,
    get_prediction_dollars,
    get_prediction_swipes,
    get_semester_start_end,
    recent_transactions_card,
)
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from legacy.models import Account
from pytz import timezone
from rest_framework.views import APIView

from studentlife.utils import date_iso_eastern


class Dashboard(APIView):
    def get(self, request, format=None):
        if not self.request.user.is_authenticated:
            return HttpResponseForbidden()

        pennid = request.user.username

        try:
            uid = Account.objects.get(pennid=pennid).id
        except Account.DoesNotExist:
            return HttpResponseBadRequest()

        json = balance(uid)

        start, end = get_semester_start_end()

        eastern = timezone("US/Eastern")
        start = start.replace(tzinfo=eastern, hour=0, minute=0, second=0, microsecond=0)
        end = end.replace(tzinfo=eastern, hour=0, minute=0, second=0, microsecond=0)
        json["start-of-semester"] = date_iso_eastern(start)
        json["end-of-semester"] = date_iso_eastern(end)

        json["cards"] = {"recent-transactions": recent_transactions_card(uid)}

        average_balances = get_average_balances(uid, start)

        if average_balances:
            json["cards"].update({"daily-average": average_balances})

        dollar_prediction = get_prediction_dollars(uid, start, end)

        if dollar_prediction:
            json["cards"].update({"predictions-graph-dollars": dollar_prediction})

        swipes_prediction = get_prediction_swipes(uid, start, end)

        if swipes_prediction:
            json["cards"].update({"predictions-graph-swipes": swipes_prediction})

        frequent_locations = get_frequent_locations(uid, start, end)

        if frequent_locations:
            json["cards"].update({"frequent-locations": frequent_locations})

        return JsonResponse(json)
