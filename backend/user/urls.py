from django.urls import path
from rest_framework import routers

from user.views import (
    NotificationAlertView,
    NotificationSettingView,
    NotificationTokenView,
    UserView,
)


app_name = "user"

router = routers.DefaultRouter()
router.register(r"notifications/tokens", NotificationTokenView, basename="notiftokens")
router.register(r"notifications/settings", NotificationSettingView, basename="notifsettings")

additional_urls = [
    path("me/", UserView.as_view(), name="user"),
    path("notifications/alerts/", NotificationAlertView.as_view(), name="alert"),
]

urlpatterns = router.urls + additional_urls
