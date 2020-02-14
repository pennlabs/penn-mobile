from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse
from datetime import timedelta, datetime

from legacy.models import Account, DiningBalance, DiningTransaction, Course
from options.models import get_value, get_option
from studentlife.utils import get_new_end

# Create your views here.

class Dashboard(APIView):

	def get(self, request, format=None):
		self.pennkey = request.GET.get("pennid")
		self.uid = Account.objects.filter(pennkey=self.pennkey)[0].id
		json = self.balance()
		json["end-of-semester"] = self.get_semester_end()
		json["cards"] = []
		json["cards"].append(self.recent_transactions_card())

		return JsonResponse(json)

	def balance(self):
		balance = DiningBalance.objects.filter(account=self.uid).order_by("-created_at")
		latest = balance[0]
		return {
			"swipes": latest.swipes,
			"dining-dollars": latest.dining_dollars,
			"guest-swipes": latest.guest_swipes
		}


	def recent_transactions_card(self):

		card = {
			"type": "recent-transactions",
			"header-title": "Transactions",
			"header-body": "Your recent dining dollar transactions",
			"data": []
		}

		transactions = DiningTransaction.objects.filter(account=self.uid).order_by("-date")

		transactions = transactions[0:5]

		for transaction in transactions:
			card["data"].append({
					"location": transaction.description,
					"date": transaction.date.strftime('%Y-%m-%dT%H:%M:%S'),
					"balance": transaction.balance,
					"amount": transaction.amount
			})

		return card

	def get_semester_end(self):
		current_end = get_value("semester_end")
		current_end = datetime.strptime(current_end, "%Y-%m-%dT%H:%M:%S")

		if current_end > datetime.now():
			return current_end
		else: 
			new_option = get_option("semester_end")
			new_option.value = get_new_end().strftime("%Y-%m-%dT%H:%M:%S")
			new_option.save()
			return get_value("semester_end")
