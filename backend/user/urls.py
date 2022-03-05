from django.urls import path
from rest_framework import routers

from user.views import NotificationView, UserView


app_name = "user"

router = routers.DefaultRouter()
router.register(r"notifications", NotificationView, basename="notifications")

additional_urls = [
    path("me/", UserView.as_view(), name="user"),
]

urlpatterns = router.urls + additional_urls
