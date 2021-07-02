from django.urls import include, path
from rest_framework import routers

from user.views import (
    NotificationSettingsView,
    RegisterNotificationToken,
    SendNotification,
    UserView,
)


router = routers.DefaultRouter()

router.register(r"notifications", SendNotification, basename="notifications")


urlpatterns = [
    path("", include(router.urls)),
    path("me/", UserView.as_view(), name="user"),
    path("notifications/settings/", NotificationSettingsView.as_view(), name="notif-settings"),
    path("notifications/register/", RegisterNotificationToken.as_view(), name="notif-register"),
]
