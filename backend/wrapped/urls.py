from django.urls import path

from wrapped.views import SemesterCurrentView, SemesterView


urlpatterns = [
    path("semester/current/", SemesterCurrentView.as_view(), name="semester-current-detail"),
    path("semester/<str:semester_id>/", SemesterView.as_view(), name="semester-detail"),
]
