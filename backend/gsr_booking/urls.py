from django.urls import include, path
from django.views.decorators.cache import cache_page
from rest_framework import routers

from gsr_booking.views import (
    Availability,
    BookRoom,
    CancelRoom,
    CheckSEAS,
    CheckWharton,
    GroupMembershipViewSet,
    GroupViewSet,
    GSRShareCodeViewSet,
    Locations,
    MyMembershipViewSet,
    RecentGSRs,
    ReservationsView,
)
from utils.cache import Cache


router = routers.DefaultRouter()

router.register(r"mymemberships", MyMembershipViewSet, "mymemberships")
router.register(r"membership", GroupMembershipViewSet)
router.register(r"groups", GroupViewSet)
router.register(r"share", GSRShareCodeViewSet, basename="share")

urlpatterns = [
    path("", include(router.urls)),
    path("locations/", cache_page(Cache.MONTH)(Locations.as_view()), name="locations"),
    path("recent/", RecentGSRs.as_view(), name="recent-gsrs"),
    path("wharton/", CheckWharton.as_view(), name="is-wharton"),
    path("seas/", CheckSEAS.as_view(), name="is-seas"),
    path("availability/<lid>/<gid>", Availability.as_view(), name="availability"),
    path("book/", BookRoom.as_view(), name="book"),
    path("cancel/", CancelRoom.as_view(), name="cancel"),
    path("reservations/", ReservationsView.as_view(), name="reservations"),
]
