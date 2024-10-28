from django.contrib.auth import get_user_model
from django.db.models import prefetch_related_objects
from django.utils import timezone
from rest_framework import exceptions, generics, mixins, status, viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from market.models import Tag, Category, Offer, Item, Sublet, ItemImage
from market.permissions import (
    IsSuperUser,
    OfferOwnerPermission,
    ItemImageOwnerPermission,
    ItemOwnerPermission,
)
from market.serializers import (
    TagSerializer,
    OfferSerializer,
    CategorySerializer,
    ItemImageSerializer,
    ItemImageURLSerializer,
    ItemSerializer,
    ItemSerializerRead,
    ItemSerializerRead,
    ItemSerializerSimple,
    SubletSerializer,
)
from pennmobile.analytics import Metric, record_analytics


User = get_user_model()


class Tags(generics.ListAPIView):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()

    def get(self, request, *args, **kwargs):
        temp = super().get(self, request, *args, **kwargs).data
        response_data = [a["name"] for a in temp]
        return Response(response_data)


class Categories(generics.ListAPIView):
    serializer_class = CategorySerializer
    queryset = Category.objects.all()

    def get(self, request, *args, **kwargs):
        temp = super().get(self, request, *args, **kwargs).data
        response_data = [a["name"] for a in temp]
        return Response(response_data)


class UserFavorites(generics.ListAPIView):
    serializer_class = ItemSerializerSimple
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return user.items_favorited


class UserOffers(generics.ListAPIView):
    serializer_class = OfferSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Offer.objects.filter(user=user)


class Items(viewsets.ModelViewSet):
    """
    list:
    Returns a list of Items that match query parameters (e.g., amenities) and belong to the user.

    create:
    Create an Item.

    partial_update:
    Update certain fields in the Item. Only the owner can edit it.

    destroy:
    Delete an Item.
    """

    permission_classes = [ItemOwnerPermission | IsSuperUser]

    def get_serializer_class(self):
        return ItemSerializerRead if self.action == "retrieve" else ItemSerializer

    def get_queryset(self):
        return Item.objects.prefetch_related('sublet').all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # Check if the data is valid
        instance = serializer.save()  # Create the Item
        instance_serializer = ItemSerializerRead(instance=instance, context={"request": request})

        #record_analytics(Metric.SUBLET_CREATED, request.user.username)

        return Response(instance_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        queryset = self.filter_queryset(self.get_queryset())
        # no clue what this does but I copied it from the DRF source code
        if queryset._prefetch_related_lookups:
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance,
            # and then re-prefetch related objects
            instance._prefetched_objects_cache = {}
            prefetch_related_objects([instance], *queryset._prefetch_related_lookups)
        return Response(ItemSerializerRead(instance=instance).data)

    # This is currently redundant but will leave for use when implementing image creation
    # def create(self, request, *args, **kwargs):
    #     # amenities = request.data.pop("amenities", [])
    #     new_data = request.data
    #     amenities = new_data.pop("amenities", [])

    #     # check if valid amenities
    #     try:
    #         amenities = [Amenity.objects.get(name=amenity) for amenity in amenities]
    #     except Amenity.DoesNotExist:
    #         return Response({"amenities": "Invalid amenity"}, status=status.HTTP_400_BAD_REQUEST)

    #     serializer = self.get_serializer(data=new_data)
    #     serializer.is_valid(raise_exception=True)
    #     item = serializer.save()
    #     item.amenities.set(amenities)
    #     item.save()
    # return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # Check if the user has permission to delete the Item and Sublet
        if self.request.user == instance.seller or self.request.user.is_superuser:
            # Delete associated Sublet if it exists
            if hasattr(instance, 'sublet'):
                instance.sublet.delete()

            # Delete the Item
            instance.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            raise serializers.ValidationError("You do not have permission to delete this item.")
        

    def list(self, request, *args, **kwargs):
        """Returns a list of Items that match query parameters and user ownership."""
        # Get query parameters from request (e.g., tags, user_owned)
        params = request.query_params
        category = params.get("category")
        tags = params.getlist("tags")
        title = params.get("title")
        address = params.get("address")
        seller = params.get("seller", "false")  # Defaults to False if not specified
        starts_before = params.get("starts_before", None)
        starts_after = params.get("starts_after", None)
        ends_before = params.get("ends_before", None)
        ends_after = params.get("ends_after", None)
        min_price = params.get("min_price", None)
        max_price = params.get("max_price", None)
        negotiable = params.get("negotiable", None)
        beds = params.get("beds", None)
        baths = params.get("baths", None)

        queryset = self.get_queryset()
        # Apply filters based on query parameters

        if seller.lower() == "true":
            queryset = queryset.filter(seller=request.user)
        else:
            queryset = queryset.filter(expires_at__gte=timezone.now())
        
        if title:
            queryset = queryset.filter(title__icontains=title)
        if address:
            queryset = queryset.filter(address__icontains=address)
        if tags:
            for tag in tags:
                queryset = queryset.filter(tags__name=tag)
        if category:
            queryset = queryset.filter(category__name=category)
        if starts_before:
            queryset = queryset.filter(start_date__lt=starts_before)
        if starts_after:
            queryset = queryset.filter(start_date__gt=starts_after)
        if ends_before:
            queryset = queryset.filter(end_date__lt=ends_before)
        if ends_after:
            queryset = queryset.filter(end_date__gt=ends_after)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        if negotiable:
            queryset = queryset.filter(negotiable=negotiable)
        if beds:
            queryset = queryset.filter(beds=beds)
        if baths:
            queryset = queryset.filter(baths=baths)
        if address:
            queryset = queryset.filter(sublet__address__icontains=address)
        if starts_before:
            queryset = queryset.filter(sublet__start_date__lt=starts_before)
        if starts_after:
            queryset = queryset.filter(sublet__start_date__gt=starts_after)
        if ends_before:
            queryset = queryset.filter(sublet__end_date__lt=ends_before)
        if ends_after:
            queryset = queryset.filter(sublet__end_date__gt=ends_after)
        if beds:
            queryset = queryset.filter(sublet__beds=beds)
        if baths:
            queryset = queryset.filter(sublet__baths=baths)

        #record_analytics(Metric.SUBLET_BROWSE, request.user.username)
        # Serialize and return the queryset
        serializer = ItemSerializerSimple(queryset, many=True)
        return Response(serializer.data)


class CreateImages(generics.CreateAPIView):
    serializer_class = ItemImageSerializer
    http_method_names = ["post"]
    permission_classes = [ItemImageOwnerPermission | IsSuperUser]
    parser_classes = (
        MultiPartParser,
        FormParser,
    )

    def get_queryset(self, *args, **kwargs):
        item = get_object_or_404(Item, id=int(self.kwargs["item_id"]))
        return ItemImage.objects.filter(item=item)

    # takes an image multipart form data and creates a new image object
    def post(self, request, *args, **kwargs):
        images = request.data.getlist("images")
        item_id = int(self.kwargs["item_id"])
        self.get_queryset()  # check if item exists
        img_serializers = []
        for img in images:
            img_serializer = self.get_serializer(data={"item": item_id, "image": img})
            img_serializer.is_valid(raise_exception=True)
            img_serializers.append(img_serializer)
        instances = [img_serializer.save() for img_serializer in img_serializers]
        data = [ItemImageURLSerializer(instance=instance).data for instance in instances]
        return Response(data, status=status.HTTP_201_CREATED)


class DeleteImage(generics.DestroyAPIView):
    serializer_class = ItemImageSerializer
    http_method_names = ["delete"]
    permission_classes = [ItemImageOwnerPermission | IsSuperUser]
    queryset = ItemImage.objects.all()

    def destroy(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        filter = {"id": self.kwargs["image_id"]}
        obj = get_object_or_404(queryset, **filter)
        # checking permissions here is kind of redundant
        self.check_object_permissions(self.request, obj)
        self.perform_destroy(obj)
        return Response(status=status.HTTP_204_NO_CONTENT)


class Favorites(mixins.DestroyModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = ItemSerializer
    http_method_names = ["post", "delete"]
    permission_classes = [IsAuthenticated | IsSuperUser]

    def get_queryset(self):
        user = self.request.user
        return user.items_favorited

    def create(self, request, *args, **kwargs):
        item_id = int(self.kwargs["item_id"])
        queryset = self.get_queryset()
        if queryset.filter(id=item_id).exists():
            raise exceptions.NotAcceptable("Favorite already exists")
        item = get_object_or_404(Item, id=item_id)
        self.get_queryset().add(item)

        #record_analytics(Metric.SUBLET_FAVORITED, request.user.username)

        return Response(status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        item = get_object_or_404(queryset, pk=int(self.kwargs["item_id"]))
        self.get_queryset().remove(item)
        return Response(status=status.HTTP_204_NO_CONTENT)


class Offers(viewsets.ModelViewSet):
    """
    list:
    Returns a list of all offers for the item matching the provided ID.

    create:
    Create an offer on the item matching the provided ID.

    destroy:
    Delete the offer between the user and the item matching the ID.
    """

    permission_classes = [OfferOwnerPermission | IsSuperUser]
    serializer_class = OfferSerializer

    def get_queryset(self):
        return Offer.objects.filter(item_id=int(self.kwargs["item_id"])).order_by(
            "created_date"
        )

    def create(self, request, *args, **kwargs):
        data = request.data
        request.POST._mutable = True
        if self.get_queryset().filter(user=self.request.user).exists():
            raise exceptions.NotAcceptable("Offer already exists")
        data["item"] = int(self.kwargs["item_id"])
        data["user"] = self.request.user.id
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        #record_analytics(Metric.SUBLET_OFFER, request.user.username)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        filter = {"user": self.request.user.id, "item": int(self.kwargs["item_id"])}
        obj = get_object_or_404(queryset, **filter)
        # checking permissions here is kind of redundant
        self.check_object_permissions(self.request, obj)
        self.perform_destroy(obj)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def list(self, request, *args, **kwargs):
        self.check_object_permissions(request, Item.objects.get(pk=int(self.kwargs["item_id"])))
        return super().list(request, *args, **kwargs)
