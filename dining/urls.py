from django.urls import path

from dining.views import Dashboard


app_name = "main"

urlpatterns = [path(r"", Dashboard.as_view())]
