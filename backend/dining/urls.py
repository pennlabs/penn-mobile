from django.urls import path
from django.views.decorators.cache import cache_page
from backend.utils.cache import HOUR_IN_SECONDS, MONTH_IN_SECONDS_APPROX

from dining.views import Menus, Preferences, Venues


urlpatterns = [
    path(
        "venues/",
        cache_page(1 * MONTH_IN_SECONDS_APPROX)(Venues),
        name="venues",
    ),
    path(
        "menus/",
        cache_page(1 * HOUR_IN_SECONDS)(Menus),
        name="menus",
    ),
    path(
        "menus/<date>/",
        cache_page(1 * HOUR_IN_SECONDS)(Menus),
        name="menus-with-date",
    ),
    path(
        "preferences/",
        Preferences.as_view(),
        name="dining-preferences",
    ),
]
