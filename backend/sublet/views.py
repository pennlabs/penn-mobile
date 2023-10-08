from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.db.models.functions import Trunc
from django.utils import timezone
from rest_framework import generics, viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import SubletSerializer

from sublet.models import Sublet, SubletImage, Offer, Favorite, Amenity

from sublet.permissions import SubletOwnerPermission, IsSuperUser
from sublet.serializers import SubletSerializer, FavoritesListSerializer

User = get_user_model()

class Amenities(generics.ListAPIView):
    queryset = Amenity.objects.all()

class Favorites(generics.ListAPIView):
    serializer_class = FavoritesListSerializer
    def get_queryset(self):
        user = self.request.user
        return user.favorite_set

class Properties(viewsets.ModelViewSet):
    """
    browse:
    Returns a list of Sublets that match query parameters (e.g., amenities) and belong to the user.
    
    create:
    Create a Sublet.
    
    partial_update:
    Update certain fields in the Sublet. Only the owner can edit it.
    
    destroy:
    Delete a Sublet.
    """

    #how to use the sublet owner permission
    permission_classes = [SubletOwnerPermission | IsSuperUser]
    serializer_class = SubletSerializer

    def get_queryset(self):
        # All Sublets for superusers
        if self.request.user.is_superuser:
            return Sublet.objects.all()
        
        # All Sublets where expires_at hasn't passed yet for regular users
        return Sublet.objects.filter(expires_at__gte=timezone.now())

    @action(detail=False, methods=["get"])
    def browse(self, request):
        """Returns a list of Sublets that match query parameters and user ownership."""
        # Get query parameters from request (e.g., amenities, user_owned)
        amenities = request.query_params.getlist("amenities")
        subletter = request.query_params.get("subletter", False)  # Defaults to False if not specified
        starts_before = request.query_params.get("starts_before", None)
        starts_after = request.query_params.get("starts_after", None)
        ends_before = request.query_params.get("ends_before", None)
        ends_after = request.query_params.get("ends_after", None)
        min_price = request.query_params.get("min_price", None)
        max_price = request.query_params.get("max_price", None)
        beds = request.query_params.get("beds", None)
        baths = request.query_params.get("baths", None)
        
        queryset = Sublet.objects.all()
    
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
        serializer = SubletSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def view_property(self, request, pk=None):
        """Returns details of a specific Sublet."""
        sublet = self.get_object()
        serializer = SubletSerializer(sublet)
        return Response(serializer.data)
