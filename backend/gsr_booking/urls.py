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
    ReservationsView,
    UserViewSet,
)


router = routers.DefaultRouter()

router.register(r"users", UserViewSet)
router.register(r"membership", GroupMembershipViewSet)
router.register(r"groups", GroupViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("locations/", Locations.as_view(), name="locations"),
    path("availability/<lid>", Availability.as_view(), name="availability"),
    path("book/", BookRoom.as_view(), name="book"),
    path("cancel/", CancelRoom.as_view(), name="cancel"),
    path("reservations/", ReservationsView.as_view(), name="reservations"),
    path("gsr/locations/", Locations.as_view(), name="locations"),
    path("gsr/availability/<lid>", Availability.as_view(), name="availability"),
    path("gsr/book/", BookRoom.as_view(), name="book"),
    path("gsr/cancel/", CancelRoom.as_view(), name="cancel"),
    path("gsr/reservations/", ReservationsView.as_view(), name="reservations"),
    path("gsr/wharton/", CheckWharton.as_view(), name="is-wharton"),
]
