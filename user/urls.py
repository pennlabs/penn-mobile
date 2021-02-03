from django.urls import path

from user import views


urlpatterns = [
    path("me/", views.UserView.as_view(), name="user"),
]
