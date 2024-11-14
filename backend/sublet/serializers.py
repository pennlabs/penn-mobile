from typing import Any, Optional, cast

from phonenumber_field.serializerfields import PhoneNumberField
from profanity_check import predict
from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.request import Request

from sublet.models import Amenity, Offer, Sublet, SubletImage
from utils.types import get_auth_user


class BaseModelSerializer(serializers.ModelSerializer):
    def get_request(self) -> Request:
        return cast(Request, self.context.get("request"))


class AmenitySerializer(BaseModelSerializer):
    name = serializers.CharField(max_length=255)

    class Meta:
        model = Amenity
        fields = "__all__"


class OfferSerializer(BaseModelSerializer):
    phone_number = PhoneNumberField()
    email = serializers.EmailField(allow_null=True)
    message = serializers.CharField(max_length=255)
    created_date = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Offer
        fields = "__all__"
        read_only_fields = ["id", "created_date", "user"]

    def create(self, validated_data: dict[str, Any]) -> Offer:
        validated_data["user"] = self.get_request().user
        return super().create(validated_data)


# Create/Update Image Serializer
class SubletImageSerializer(BaseModelSerializer):
    image = serializers.ImageField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = SubletImage
        fields = ["sublet", "image"]


# Browse images
class SubletImageURLSerializer(BaseModelSerializer):
    image_url = serializers.SerializerMethodField("get_image_url")

    def get_image_url(self, obj: SubletImage) -> Optional[str]:
        if not obj.image:
            return None

        image_url = obj.image.url
        if image_url.startswith("http"):
            return image_url

        request = self.get_request()
        return request.build_absolute_uri(image_url) if request else image_url

    class Meta:
        model = SubletImage
        fields = ["id", "image_url"]


# complex sublet serializer for use in C/U/D + getting info about a singular sublet
class SubletSerializer(BaseModelSerializer):
    # amenities = AmenitySerializer(many=True, required=False)
    # images = SubletImageURLSerializer(many=True, required=False)
    amenities: PrimaryKeyRelatedField = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Amenity.objects.all(), required=False
    )

    class Meta:
        model = Sublet
        read_only_fields = [
            "id",
            "created_at",
            "subletter",
            "sublettees",
            # "images"
        ]
        fields = [
            "id",
            "subletter",
            "amenities",
            "title",
            "address",
            "beds",
            "baths",
            "description",
            "external_link",
            "price",
            "negotiable",
            "start_date",
            "end_date",
            "expires_at",
            # "images",
            # images are now created/deleted through a separate endpoint (see urls.py)
            # this serializer isn't used for getting,
            # but gets on sublets will include ids/urls for images
        ]

    def _validate_text_content(self, text: str, field_name: str) -> str:
        """Validates text content for profanity"""
        if predict([text])[0]:
            raise serializers.ValidationError(f"The {field_name} contains inappropriate language.")
        return text

    def validate_title(self, value: str) -> str:
        return self._validate_text_content(value, "title")

    def validate_description(self, value: str) -> str:
        return self._validate_text_content(value, "description")

    def create(self, validated_data: dict[str, Any]) -> Sublet:
        validated_data["subletter"] = self.get_request().user
        instance = super().create(validated_data)
        instance.save()
        return instance

    # delete_images is a list of image ids to delete
    def update(self, instance: Sublet, validated_data: dict[str, Any]) -> Sublet:
        # Check if the user is the subletter before allowing the update
        user = get_auth_user(self.get_request())
        if user == instance.subletter or user.is_superuser:
            instance = super().update(instance, validated_data)
            instance.save()
            return instance
        raise serializers.ValidationError("You do not have permission to update this sublet.")

    def destroy(self, instance: Sublet) -> None:
        # Check if the user is the subletter before allowing the delete
        user = get_auth_user(self.get_request())
        if user == instance.subletter or user.is_superuser:
            instance.delete()
        else:
            raise serializers.ValidationError("You do not have permission to delete this sublet.")


class SubletSerializerRead(BaseModelSerializer):
    amenities: PrimaryKeyRelatedField = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Amenity.objects.all(), required=False
    )
    images = SubletImageURLSerializer(many=True, required=False)

    class Meta:
        model = Sublet
        read_only_fields = ["id", "created_at", "subletter", "sublettees"]
        fields = [
            "id",
            "subletter",
            "amenities",
            "title",
            "address",
            "beds",
            "baths",
            "description",
            "external_link",
            "price",
            "negotiable",
            "start_date",
            "end_date",
            "expires_at",
            "images",
        ]

    def to_representation(self, instance: Sublet) -> dict[str, Any]:
        """Override to ensure proper typing of returned data"""
        data = super().to_representation(instance)
        assert isinstance(data, dict)
        return data


# simple sublet serializer for use when pulling all serializers/etc
class SubletSerializerSimple(BaseModelSerializer):
    amenities: PrimaryKeyRelatedField = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Amenity.objects.all(), required=False
    )
    images = SubletImageURLSerializer(many=True, required=False)

    class Meta:
        model = Sublet
        fields = [
            "id",
            "subletter",
            "amenities",
            "title",
            "address",
            "beds",
            "baths",
            "price",
            "negotiable",
            "start_date",
            "end_date",
            "images",
        ]
        read_only_fields = ["id", "subletter"]

    def to_representation(self, instance: Sublet) -> dict[str, Any]:
        """Override to ensure proper typing of returned data"""
        data = super().to_representation(instance)
        assert isinstance(data, dict)
        return data
