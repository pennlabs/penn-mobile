from django.urls import include, path
from rest_framework import routers

from gsr_booking.views import (
    GroupMembershipViewSet,
    GroupViewSet,
    GSRBookingCredentialsViewSet,
    UserViewSet,
)


router = routers.DefaultRouter()

router.register(r"users", UserViewSet)
router.register(r"membership", GroupMembershipViewSet)
router.register(r"groups", GroupViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("credentials/", GSRBookingCredentialsViewSet.as_view()),
]
