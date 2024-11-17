from django.urls import path

from wrapped.views import SemesterView


urlpatterns = [
    path("semester/<str:semester_id>/", SemesterView.as_view(), name="semester-detail"),
]
