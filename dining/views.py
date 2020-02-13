from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse
from datetime import timedelta

from legacy.models import Account, DiningBalance, DiningTransaction, Course


# Create your views here.

class Dashboard(APIView):

	def get(self, request, format=None):
		return JsonResponse({})