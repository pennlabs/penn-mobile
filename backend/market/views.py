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
    SubletOwnerPermission,
)
from market.serializers import (
    TagSerializer,
    OfferSerializer,
    CategorySerializer,
    ItemImageSerializer,
    ItemImageURLSerializer,
    ItemSerializer,
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


def apply_filters(queryset, params, filter_mappings, user=None, is_sublet=False, tag_field="tags__name"):
    # Build dynamic filters based on filter mappings
    filters = {}
    for param, field in filter_mappings.items():
        if param_value := params.get(param):
            filters[field] = param_value

    # Handle seller/owner filtering based on user ownership


    # Apply basic filters to the queryset

    # Exclude specific categories if provided
    if not is_sublet:
        queryset = queryset.exclude(category__name__in=["Sublet"])
        if params.get("seller", "false").lower() == "true" and user:
            filters["seller"] = user
        else:
            filters["expires_at__gte"] = timezone.now()
    else :
        queryset = queryset.filter(item__category__name__in=["Sublet"])
        if params.get("seller", "false").lower() == "true" and user:
            filters["item__seller"] = user
        else:
            filters["item__expires_at__gte"] = timezone.now()

    queryset = queryset.filter(**filters)

    # Apply tag filtering iteratively if "tags" parameter is provided
    if tags := params.getlist("tags"):
        for tag in tags:
            queryset = queryset.filter(**{tag_field: tag})

    return queryset


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
    serializer_class = ItemSerializer
    queryset = Item.objects.all()

    def list(self, request, *args, **kwargs):
        """Returns a list of Items that match query parameters and user ownership."""
        params = request.query_params
        queryset = self.get_queryset()

        # Define a dictionary mapping query parameters to filter fields
        filter_mappings = {
            "category": "category__name",
            "title": "title__icontains",
            "min_price": "price__gte",
            "max_price": "price__lte",
            "negotiable": "negotiable",
        }

        # Apply filters using the helper function
        queryset = apply_filters(
            queryset=queryset,
            params=params,
            filter_mappings=filter_mappings,
            user=request.user,
            is_sublet=True
        )

        # Serialize and return the queryset
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
 

class Sublets(viewsets.ModelViewSet):
    permission_classes = [SubletOwnerPermission | IsSuperUser]
    serializer_class = SubletSerializer
    queryset = Sublet.objects.all()

    def list(self, request, *args, **kwargs):
        """Returns a filtered list of Sublets based on query parameters."""
        params = request.query_params
        queryset = self.get_queryset()

        # Define filter mappings
        filter_mappings = {
            "title": "item__title__icontains",
            "min_price": "item__price__gte",
            "max_price": "item__price__lte",
            "negotiable": "item__negotiable",
            "address": "address__icontains",
            "beds": "beds",
            "baths": "baths",
            "start_date_min": "start_date__gte",
            "start_date_max": "start_date__lte",
            "end_date_min": "end_date__gte",
            "end_date_max": "end_date__lte",
        }

        # Apply filters using the helper function
        queryset = apply_filters(
            queryset=queryset,
            params=params,
            filter_mappings=filter_mappings,
            user=request.user,
            is_sublet=True,
            tag_field="item__tags__name",
        )

        # Serialize and return the queryset
        serializer = self.get_serializer(queryset, many=True)
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
