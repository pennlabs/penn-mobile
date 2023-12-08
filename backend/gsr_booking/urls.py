from django.urls import include, path
from rest_framework import routers
from django.views.decorators.cache import cache_page
from utils.cache import Cache

from gsr_booking.views import (
    Availability,
    BookRoom,
    CancelRoom,
    CheckWharton,
    CreditsView,
    GroupMembershipViewSet,
    GroupViewSet,
    Locations,
    RecentGSRs,
    ReservationsView,
    UserViewSet,
)


router = routers.DefaultRouter()

router.register(r"users", UserViewSet)
router.register(r"membership", GroupMembershipViewSet)
router.register(r"groups", GroupViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("locations/", Locations.as_view(),
         cache_page(Cache.MONTH)(Locations.as_view()), name="locations"),
    path("recent/", RecentGSRs.as_view(), name="recent-gsrs"),
    path("wharton/", CheckWharton.as_view(), name="is-wharton"),
    path("availability/<lid>/<gid>", Availability.as_view(), name="availability"),
    path("book/", BookRoom.as_view(), name="book"),
    path("cancel/", CancelRoom.as_view(), name="cancel"),
    path("reservations/", ReservationsView.as_view(), name="reservations"),
    path("credits/", CreditsView.as_view(), name="credits"),
]
