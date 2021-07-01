from django.urls import include, path

from user.views import NotificationSettingsView, RegisterNotificationToken, UserView, SendNotification
from rest_framework import routers

router = routers.DefaultRouter()

router.register(r"notifications", SendNotification)


urlpatterns = [
    path("", include(router.urls)),
    path("me/", UserView.as_view(), name="user"),
    path("notifications/settings/", NotificationSettingsView.as_view()),
    path("notifications/register/", RegisterNotificationToken.as_view()),
]
