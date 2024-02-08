from django.urls import path
from rest_framework import routers

from sublet.views import (
    Amenities,
    CreateImages,
    DeleteImage,
    Favorites,
    Offers,
    Properties,
    UserFavorites,
    UserOffers,
)


app_name = "sublet"

router = routers.DefaultRouter()
router.register(r"properties", Properties, basename="properties")

additional_urls = [
    path("amenities/", Amenities.as_view(), name="amenities"),
    path("favorites/", UserFavorites.as_view(), name="user-favorites"),
    path("offers/", UserOffers.as_view(), name="user-offers"),
    path(
        "properties/<sublet_id>/favorites/",
        Favorites.as_view({"post": "create", "delete": "destroy"}),
    ),
    path(
        "properties/<sublet_id>/offers/",
        Offers.as_view({"get": "list", "post": "create", "delete": "destroy"}),
    ),
    path("properties/<sublet_id>/images/", CreateImages.as_view()),
    path("properties/images/<image_id>/", DeleteImage.as_view()),
]

urlpatterns = router.urls + additional_urls
