from django.urls import include, path
from rest_framework import routers

from gsr_booking.views import (
    Availability,
    GroupMembershipViewSet,
    GroupViewSet,
    GSRBookingCredentialsViewSet,
    UserViewSet,
    Locations,
    Availability,
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

]
