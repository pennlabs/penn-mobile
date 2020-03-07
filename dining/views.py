from datetime import datetime, timedelta

from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from legacy.models import Account, DiningBalance, DiningTransaction
from options.models import get_option, get_value, Option
from pytz import timezone
from rest_framework.views import APIView

from studentlife.utils import date_iso_eastern, get_new_start_end


class Dashboard(APIView):
    def get(self, request, format=None):
        if not self.request.user.is_authenticated:
            return HttpResponseForbidden()

        pennid = "76627463"  # request.user.username

        try:
            uid = Account.objects.get(pennid=pennid).id
        except Account.DoesNotExist:
            return HttpResponseBadRequest()

        json = self.balance(uid)

        start, end = self.get_semester_start_end()
        json["start-of-semester"] = date_iso_eastern(start)
        json["end-of-semester"] = date_iso_eastern(end)

        json["cards"] = {"recent-transactions": self.recent_transactions_card(uid)}

        average_balances = self.get_average_balances(uid, start)

        if average_balances:
            json["cards"].update({"daily-average": average_balances})

        dollar_prediction = self.get_prediction_dollars(uid, start, end)

        if dollar_prediction:
            json["cards"].update({"predictions-graph-dollars": dollar_prediction})

        swipes_prediction = self.get_prediction_swipes(uid, start, end)

        if swipes_prediction:
            json["cards"].update({"predictions-graph-swipes": swipes_prediction})

        return JsonResponse(json)

    def balance(self, uid):
        balance = DiningBalance.objects.filter(account=uid).order_by("-created_at")
        latest = balance[0]
        return {
            "swipes": latest.swipes,
            "dining-dollars": latest.dining_dollars,
            "guest-swipes": latest.guest_swipes,
        }

    def recent_transactions_card(self, uid):

        card = {
            "type": "recent-transactions",
            "header-title": "Transactions",
            "header-body": "Your recent dining dollar transactions",
            "data": [],
        }

        transactions = DiningTransaction.objects.filter(account=uid).order_by("-date")

        transactions = transactions[0:5]

        for transaction in transactions:
            card["data"].append(
                {
                    "location": transaction.description,
                    "date": date_iso_eastern(transaction.date),
                    "balance": transaction.balance,
                    "amount": transaction.amount,
                }
            )

        return card

    def get_semester_start_end(self):

        current_start = get_value("semester_start")
        current_end = get_value("semester_end")

        try:
            current_start = datetime.strptime(current_start, "%Y-%m-%d")
            current_end = datetime.strptime(current_end, "%Y-%m-%d")
        except:
            pass

        if current_start is not None and current_end is not None and current_end > datetime.now():
            return current_start, current_end
        else:
            if current_start is None or current_end is None:
                new_start_option = Option(key="semester_start", value="")
                new_end_option = Option(key="semester_end", value="")
            else:
                new_start_option = get_option("semester_start")
                new_end_option = get_option("semester_end")

            new_start, new_end = get_new_start_end()

            new_start_option.value = new_start.strftime("%Y-%m-%d")
            new_start_option.save()

            new_end_option.value = new_end.strftime("%Y-%m-%d")
            new_end_option.save()

            return (
                datetime.strptime(get_value("semester_start"), "%Y-%m-%d"),
                datetime.strptime(get_value("semester_end"), "%Y-%m-%d")
            )

    def get_average_balances(self, uid, start_of_semester):

        eastern = timezone("US/Eastern")
        two_weeks_ago = datetime.now() - timedelta(days=14)
        two_weeks_ago = two_weeks_ago.replace(
            tzinfo=eastern, hour=0, minute=0, second=0, microsecond=0
        )
        start_of_semester = start_of_semester.replace(
            tzinfo=eastern, hour=0, minute=0, second=0, microsecond=0
        )

        if two_weeks_ago < start_of_semester:
            return None

        transactions = DiningTransaction.objects.filter(
            account=uid, date__gte=two_weeks_ago
        ).order_by("date")

        transaction_dict = {}

        for transaction in transactions:
            date = transaction.date.replace(
                tzinfo=eastern, hour=0, minute=0, second=0, microsecond=0
            )
            if date not in transaction_dict:
                transaction_dict[date] = []

            transaction_dict[date].append(transaction.amount)

        transaction_averages = {}

        for date, amounts in transaction_dict.items():
            amounts = [x for x in amounts if x < 0]
            if len(amounts) > 0:
                transaction_averages[date] = round(sum(amounts) / len(amounts), 2)

        for i in range(14):
            day = two_weeks_ago + timedelta(days=i + 1)

            if day not in transaction_averages.keys():
                transaction_averages[day] = 0

        card = {"type": "daily-average", "data": {"this-week": [], "last-week": []}}

        for i, (date, average) in enumerate(sorted(transaction_averages.items(), reverse=True)):
            if i < 7:
                card["data"]["this-week"].append({"date": date.isoformat(), "average": average})
            elif i < 14:
                card["data"]["last-week"].append({"date": date.isoformat(), "average": average})
            else:
                break

        return card

        eastern = timezone("US/Eastern")
        start = start.replace(
            tzinfo=eastern, hour=0, minute=0, second=0, microsecond=0
        )
        end = end.replace(
            tzinfo=eastern, hour=0, minute=0, second=0, microsecond=0
        )

        transactions = DiningTransaction.objects.filter(
            account=uid, date__gte=start,
        ).order_by("date")

        if len(transactions) < 10:
            return None

        transactions_negative = transactions.filter(amount__lte=0)

        now = datetime.now().replace(tzinfo=eastern, hour=0, minute=0, second=0, microsecond=0)
        days_since_start = (now - start).days
        spend_rate = sum([-1*x for x in transactions_negative.values_list("amount", flat=True)]) / days_since_start

        balance = transactions[0].balance

        days_left = int(balance / spend_rate)

        broke_day =  now + timedelta(days=days_left)

        card = {
                    "type": "predictions-graph-dollars",
                    "start_of_semester": start.isoformat(),
                    "end-of-semester": end.isoformat(),
                    "predicted-zero-date": broke_day.isoformat(),
                    "data": []
                }

        for transaction in transactions:
            card["data"].append({"date": transaction.date.isoformat(), "balance": transaction.balance})

        card["data"] = sorted(card["data"], key=lambda k: k['date'])

        return card
