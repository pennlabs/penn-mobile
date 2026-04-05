from django.urls import path
from django.views.decorators.cache import cache_page

from dining.views import Menus, Preferences, Venues
from utils.cache import Cache


urlpatterns = [
    path("venues/", cache_page(12 * Cache.HOUR)(Venues.as_view()), name="venues"),
    path("menus/", Menus.as_view(), name="menus"),
    path("menus/<date>/", Menus.as_view(), name="menus-with-date"),
    path("preferences/", Preferences.as_view(), name="dining-preferences"),
]
