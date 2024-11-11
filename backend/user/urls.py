from django.urls import path
from rest_framework import routers

from user.views import (
    ClearCookiesView,
    NotificationAlertView,
    IOSNotificationTokenView,
    AndroidNotificationTokenView,
    NotificationServiceSettingView,
    NotificationServiceView,
    UserView,
)


app_name = "user"

router = routers.DefaultRouter()
# router.register(r"notifications/settings", NotificationSettingView, basename="notifsettings")

additional_urls = [
    path("notifications/tokens/ios/<token>/", IOSNotificationTokenView.as_view(), name="ios-token"),
    path("notifications/tokens/android/<token>/", AndroidNotificationTokenView.as_view(), name="android-token"),
    path("notifications/settings/", NotificationServiceSettingView.as_view(), name="notif-settings"),
    path("notifications/services/", NotificationServiceView.as_view(), name="notif-services"),
    path("me/", UserView.as_view(), name="user"),
    path("notifications/alerts/", NotificationAlertView.as_view(), name="alert"),
    path("clear-cookies/", ClearCookiesView.as_view(), name="clear-cookies"),
]

urlpatterns = router.urls + additional_urls
