from django.urls import path
from rest_framework import routers

from user import views


app_name = "user"

router = routers.DefaultRouter()
router.register(r"notifications", views.NotificationView, basename="notifications")


additional_urls = [
    path("me/", views.UserView.as_view(), name="user"),
]

urlpatterns = router.urls + additional_urls
