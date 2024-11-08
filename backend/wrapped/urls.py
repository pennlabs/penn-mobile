from django.contrib import admin
from django.urls import path
from .views import SemesterView

urlpatterns = [
    path('semester/<str:semester_id>/', SemesterView.as_view(), name='semester-detail'),
]