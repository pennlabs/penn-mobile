from django.urls import path
from rest_framework import routers

from user.views import NotificationAlertView, NotificationView, UserView


app_name = "user"

router = routers.DefaultRouter()
router.register(r"notifications", NotificationView, basename="notifications")

additional_urls = [
    path("me/", UserView.as_view(), name="user"),
    path("alerts/", NotificationAlertView.as_view(), name="alert"),
]

urlpatterns = router.urls + additional_urls
