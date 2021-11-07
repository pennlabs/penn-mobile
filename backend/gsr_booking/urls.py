from django.urls import include, path
from rest_framework import routers

from gsr_booking.views import (
    Availability,
    BookRoom,
    CancelRoom,
    CheckWharton,
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
    path("gsr/locations/", Locations.as_view(), name="locations"),
    path("gsr/availability/<lid>/<gid>", Availability.as_view(), name="availability"),
    path("gsr/book/", BookRoom.as_view(), name="book"),
    path("gsr/cancel/", CancelRoom.as_view(), name="cancel"),
    path("gsr/reservations/", ReservationsView.as_view(), name="reservations"),
    path("gsr/wharton/", CheckWharton.as_view(), name="is-wharton"),
    path("gsr/recent/", RecentGSRs.as_view(), name="recent-gsrs"),
]
