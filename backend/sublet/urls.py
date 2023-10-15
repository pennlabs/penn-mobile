from django.urls import include, path
from rest_framework import routers
from rest_framework.routers import DefaultRouter

from sublet.views import Favorites, Offers, Properties, UserFavorites


app_name = "sublet"

router = routers.DefaultRouter()
router.register(r"properties", Properties, basename="properties")
propIdRouter = routers.DefaultRouter()
propIdRouter.register(r"offers", Offers, basename="offers")

additional_urls = [
    path("favorites/", UserFavorites.as_view(), name="favorites"),
    path(
        "properties/<sublet_id>/favorites/",
        Favorites.as_view({"post": "create", "delete": "destroy"}),
    ),
    path("properties/<sublet_id>/", include(propIdRouter.urls), name="favorites"),
]

urlpatterns = router.urls + additional_urls
