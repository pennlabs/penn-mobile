from django.urls import include, path
from rest_framework import routers

from gsr_booking.views import (
    Availability,
    BookWhartonRoom,
    CancelWhartonRoom,
    GroupMembershipViewSet,
    GroupViewSet,
    GSRBookingCredentialsViewSet,
    Locations,
    UserViewSet,
    WhartonReservations,
)


router = routers.DefaultRouter()

router.register(r"users", UserViewSet)
router.register(r"membership", GroupMembershipViewSet)
router.register(r"groups", GroupViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("credentials/", GSRBookingCredentialsViewSet.as_view()),
    path("locations/", Locations.as_view()),
    path("availability/<lid>", Availability.as_view()),
    path("book/", BookWhartonRoom.as_view()),
    path("cancel/", CancelWhartonRoom.as_view()),
    path("reservations", WhartonReservations.as_view()),
]
