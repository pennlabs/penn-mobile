from django.contrib import admin
from django.urls import path
from .views import GeneratePage
urlpatterns = [
    path('generate/', GeneratePage.as_view({"get" : "user_generation"}), name='user_generation'),
]

