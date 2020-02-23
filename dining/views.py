from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse, HttpResponseForbidden
from datetime import timedelta, datetime

from legacy.models import Account, DiningBalance, DiningTransaction, Course
from options.models import get_value, get_option
from studentlife.utils import get_new_start_end

# Create your views here.


class Dashboard(APIView):
    def get(self, request, format=None):
        if not self.request.user.is_authenticated:
            return HttpResponseForbidden()

        self.pennid = "76627463"  # request.user.username
        self.uid = Account.objects.filter(pennid=self.pennid)[0].id
        json = self.balance()

        start, end = self.get_semester_start_end()
        json["start-of-semester"] = start
        json["end-of-semester"] = end

        json["cards"] = {"recent-transactions": self.recent_transactions_card()}

        return JsonResponse(json)

    def balance(self):
        balance = DiningBalance.objects.filter(account=self.uid).order_by("-created_at")
        latest = balance[0]
        return {
            "swipes": latest.swipes,
            "dining-dollars": latest.dining_dollars,
            "guest-swipes": latest.guest_swipes,
        }

    def recent_transactions_card(self):

        card = {
            "type": "recent-transactions",
            "header-title": "Transactions",
            "header-body": "Your recent dining dollar transactions",
            "data": [],
        }

        transactions = DiningTransaction.objects.filter(account=self.uid).order_by("-date")

        transactions = transactions[0:5]

        for transaction in transactions:
            card["data"].append(
                {
                    "location": transaction.description,
                    "date": transaction.date.strftime("%Y-%m-%dT%H:%M:%S"),
                    "balance": transaction.balance,
                    "amount": transaction.amount,
                }
            )

        return card

    def get_semester_start_end(self):

        current_start = get_value("semester_start")
        current_start = datetime.strptime(current_start, "%Y-%m-%d")

        current_end = get_value("semester_end")
        current_end = datetime.strptime(current_end, "%Y-%m-%d")

        if current_end > datetime.now():
            return current_start, current_end
        else:
            new_end_option = get_option("semester_end")
            new_start_option = get_option("semester_start")

            new_start, new_end = get_new_start_end()

            new_start_option.value = new_start.strftime("%Y-%m-%d")
            new_start_option.save()

            new_end_option.value = new_end.strftime("%Y-%m-%d")
            new_end_option.save()

            return (
                get_value("semester_start"),
                get_value("semester_end"),
            )
