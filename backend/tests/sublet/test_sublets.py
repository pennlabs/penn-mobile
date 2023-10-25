import datetime
import json
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from sublet.models import Amenity, Offer, Sublet, SubletImage

User = get_user_model()
