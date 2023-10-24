from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.db.models.functions import Trunc
from django.shortcuts import render
from django.utils import timezone
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from sublet.models import Amenity, Favorite, Offer, Sublet, SubletImage
from sublet.permissions import IsSuperUser, SubletOwnerPermission, OfferOwnerPermission
from sublet.serializers import (
    AmenitySerializer,
    FavoriteSerializer,
    FavoritesListSerializer,
    OfferSerializer,
    SubletSerializer,
    SimpleSubletSerializer,
)


User = get_user_model()


class Amenities(generics.ListAPIView):
    serializer_class = AmenitySerializer
    queryset = Amenity.objects.all()


class UserFavorites(generics.ListAPIView):
    serializer_class = FavoritesListSerializer
    permission_classes = IsAuthenticated

    def get_queryset(self):
        user = self.request.user
        # print(type(user.favorite_set))
        # return user.favorite_set
        return Favorite.objects.filter(user=user)


class UserOffers(generics.ListAPIView):
    serializer_class = OfferSerializer
    permission_classes = IsAuthenticated

    def get_queryset(self):
        user = self.request.user
        # print(type(user.favorite_set))
        # return user.favorite_set
        return Offer.objects.filter(user=user)


class Properties(viewsets.ModelViewSet):
    """
    list:
    Returns a list of Sublets that match query parameters (e.g., amenities) and belong to the user.
    
    create:
    Create a Sublet.
    
    partial_update:
    Update certain fields in the Sublet. Only the owner can edit it.
    
    destroy:
    Delete a Sublet.
    """

    # how to use the sublet owner permission
    permission_classes = [SubletOwnerPermission | IsSuperUser]
    serializer_class = SubletSerializer

    def get_queryset(self):
        # All Sublets for superusers
        # if self.request.user.is_superuser:
        #     return Sublet.objects.all()

        # # All Sublets where expires_at hasn't passed yet for regular users
        # return Sublet.objects.filter(expires_at__gte=timezone.now())
        return Sublet.objects.all()

    def create(self, request, *args, **kwargs):
        amenities = request.data.pop("amenities", [])

        # check if valid amenities
        try:
            amenities = [Amenity.objects.get(name=amenity) for amenity in amenities]
        except Amenity.DoesNotExist:
            return Response({"amenities": "Invalid amenity"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sublet = serializer.save()
        sublet.amenities.set(amenities)
        sublet.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        """Returns a list of Sublets that match query parameters and user ownership."""
        # Get query parameters from request (e.g., amenities, user_owned)
        amenities = request.query_params.getlist("amenities")
        subletter = request.query_params.get(
            "subletter", "false"
        )  # Defaults to False if not specified
        starts_before = request.query_params.get("starts_before", None)
        starts_after = request.query_params.get("starts_after", None)
        ends_before = request.query_params.get("ends_before", None)
        ends_after = request.query_params.get("ends_after", None)
        min_price = request.query_params.get("min_price", None)
        max_price = request.query_params.get("max_price", None)
        beds = request.query_params.get("beds", None)
        baths = request.query_params.get("baths", None)

        queryset = Sublet.objects.all(expires_at__gte=timezone.now())

        # Apply filters based on query parameters
        if amenities:
            queryset = queryset.filter(amenities__name__in=amenities)
        if subletter.lower() == "true":
            queryset = queryset.filter(subletter=request.user)
        if starts_before:
            queryset = queryset.filter(start_date__lt=starts_before)
        if starts_after:
            queryset = queryset.filter(start_date__gt=starts_after)
        if ends_before:
            queryset = queryset.filter(end_date__lt=ends_before)
        if ends_after:
            queryset = queryset.filter(end_date__gt=ends_after)
        if min_price:
            queryset = queryset.filter(min_price__gte=min_price)
        if max_price:
            queryset = queryset.filter(max_price__lte=max_price)
        if beds:
            queryset = queryset.filter(beds=beds)
        if baths:
            queryset = queryset.filter(baths=baths)

        # Serialize and return the queryset
        serializer = SimpleSubletSerializer(queryset, many=True)
        return Response(serializer.data)


class Favorites(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    queryset = Favorite.objects.all()
    http_method_names = ["post", "delete"]
    permission_classes = [IsAuthenticated | IsSuperUser]

    def create(self, request, *args, **kwargs):
        data = self.request.data
        data["sublet"] = int(self.kwargs["sublet_id"])
        data["user"] = self.request.user.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        filter = {"user": self.request.user.id, "sublet": int(self.kwargs["sublet_id"])}
        obj = get_object_or_404(queryset, **filter)
        self.check_object_permissions(self.request, obj)
        self.perform_destroy(obj)
        return Response(status=status.HTTP_204_NO_CONTENT)


class Offers(viewsets.ModelViewSet):
    """
    list:
    Returns a list of all offers for the sublet matching the provided ID.

    create:
    Create an offer on the sublet matching the provided ID.

    destroy:
    Delete the offer between the user and the sublet matching the ID.
    """

    permission_classes = [OfferOwnerPermission | IsSuperUser]
    serializer_class = OfferSerializer

    def get_queryset(self):
        return Offer.objects.filter(sublet_id=self.kwargs["sublet_id"]).order_by("created_date")

    def create(self, request, *args, **kwargs):
        data = request.data
        data["sublet"] = int(self.kwargs["sublet_id"])
        data["user"] = self.request.user.id
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        filter = {"user": self.request.user.id, "sublet": int(self.kwargs["sublet_id"])}
        obj = get_object_or_404(queryset, **filter)
        self.check_object_permissions(self.request, obj)
        self.perform_destroy(obj)
        return Response(status=status.HTTP_204_NO_CONTENT)
