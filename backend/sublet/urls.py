from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework import routers
from sublet.views import Properties


#from subletting.views import{}

app_name = "sublet"

router = routers.DefaultRouter()
router.register(r'properties', Properties, basename="properties")

additional_urls = []

urlpatterns = router.urls + additional_urls