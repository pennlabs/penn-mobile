from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from pytz import timezone
from rest_framework.views import APIView

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
            json["cards"], "predictions-graph-dollars", get_prediction_dollars(uid, start, end)
        )
        update_if_not_none(
            json["cards"], "predictions-graph-swipes", get_prediction_swipes(uid, start, end)
        )
        update_if_not_none(
            json["cards"], "frequent-locations", get_frequent_locations(uid, start, end)
        )

        return JsonResponse(json)
