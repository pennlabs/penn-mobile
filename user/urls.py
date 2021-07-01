from django.urls import path

from user.views import NotificationSettingsView, RegisterNotificationToken, UserView


urlpatterns = [
    path("me/", UserView.as_view(), name="user"),
    path("notifications/settings/", NotificationSettingsView.as_view()),
    path("notifications/register/", RegisterNotificationToken.as_view()),
]
