from dining.helpers import (
    balance,
    get_average_balances,
    get_frequent_locations,
    get_prediction_dollars,
    get_prediction_swipes,
    get_semester_start_end,
    recent_transactions_card,
    update_if_not_none
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

        update_if_not_none(json["cards"], "daily-average", get_average_balances(uid, start))
        update_if_not_none(json["cards"], "predictions-graph-dollars", get_prediction_dollars(uid, start, end))
        update_if_not_none(json["cards"], "predictions-graph-swipes", get_prediction_swipes(uid, start, end))
        update_if_not_none(json["cards"], "frequent-locations", get_prediction_swipes(uid, start, end))

        return JsonResponse(json)
