from django.urls import path

from penndata.views import News


urlpatterns = [
    path("news/", News.as_view(), name="news"),
]
