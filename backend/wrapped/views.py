from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.db import transaction
from wrapped.models import Page, IndividualStat, GlobalStat
from django.core.exceptions import ValidationError
