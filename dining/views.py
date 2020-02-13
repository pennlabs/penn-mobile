from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse
from datetime import timedelta

from legacy.models import Account, DiningBalance, DiningTransaction, Course


# Create your views here.

class Dashboard(APIView):

	def get(self, request, format=None):
		self.pennkey = request.GET.get("pennid")
		self.uid = Account.objects.filter(pennkey=self.pennkey)[0].id
		json = self.balance()

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