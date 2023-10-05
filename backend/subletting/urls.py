from django.urls import path
from rest_framework import routers


#from subletting.views import{}

app_name = "subletting"

router = routers.DefaultRouter()

additional_urls = []

urlpatterns = router.urls + additional_urls
