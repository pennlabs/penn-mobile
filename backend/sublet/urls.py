from django.urls import path
from rest_framework import routers


#from sublet.views import{}

app_name = "sublet"

router = routers.DefaultRouter()

additional_urls = []

urlpatterns = router.urls + additional_urls
