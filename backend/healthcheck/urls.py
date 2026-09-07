from django.urls import path

from healthcheck.views import FeatureHealth


urlpatterns = [
    path("features/", FeatureHealth.as_view(), name="feature-health"),
]
