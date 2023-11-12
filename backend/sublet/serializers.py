from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

from sublet.models import Amenity, Offer, Sublet, SubletImage


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = "__all__"


class OfferSerializer(serializers.ModelSerializer):
    phone_number = PhoneNumberField()

    class Meta:
        model = Offer
        fields = "__all__"
        read_only_fields = ["id", "created_date", "user"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


# Create/Update Image Serializer
class SubletImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = SubletImage
        fields = ["sublet", "image"]
        read_only_fields = ["sublet", "image"]


# Browse images
class SubletImageURLSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField("get_image_url")

    def get_image_url(self, obj):
        image = obj.image

        if not image:
            return None
        if image.url.startswith("http"):
            return image.url
        elif "request" in self.context:
            return self.context["request"].build_absolute_uri(image.url)
        else:
            return image.url

    class Meta:
        model = SubletImage
        fields = ["image_url"]


# complex sublet serializer for use in C/U/D + getting info about a singular sublet
class SubletSerializer(serializers.ModelSerializer):
    amenities = AmenitySerializer(many=True, required=False)

    class Meta:
        model = Sublet
        exclude = ["favorites"]
        read_only_fields = ["id", "created_at", "subletter", "sublettees"]

    def parse_amenities(self, raw_amenities):
        if isinstance(raw_amenities, list):
            ids = raw_amenities
        else:
            ids = (
                list() if len(raw_amenities) == 0 else [str(id) for id in raw_amenities.split(",")]
            )
        return Amenity.objects.filter(name__in=ids)

    def create(self, validated_data):
        validated_data["subletter"] = self.context["request"].user
        instance = super().create(validated_data)
        data = self.context["request"].POST
        amenities = self.parse_amenities(data.getlist("amenities"))
        instance.amenities.set(amenities)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        # Check if the user is the subletter before allowing the update
        if (
            self.context["request"].user == instance.subletter
            or self.context["request"].user.is_superuser
        ):
            amenities_data = self.context["request"].data
            if amenities_data.get("amenities") is not None:
                amenities = self.parse_amenities(amenities_data.getlist("amenities"))
                instance.amenities.set(amenities)
            validated_data.pop("amenities", None)
            instance = super().update(instance, validated_data)
            instance.save()
        else:
            raise serializers.ValidationError("You do not have permission to update this sublet.")

        return instance

    def destroy(self, instance):
        # Check if the user is the subletter before allowing the delete
        if (
            self.context["request"].user == instance.subletter
            or self.context["request"].user.is_superuser
        ):
            instance.delete()
        else:
            raise serializers.ValidationError("You do not have permission to delete this sublet.")


# simple sublet serializer for use when pulling all serializers/etc
class SimpleSubletSerializer(serializers.ModelSerializer):
    amenities = AmenitySerializer(many=True, required=False)
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
            "min_price",
            "max_price",
            "start_date",
            "end_date",
            "images",
        ]
        read_only_fields = ["id", "subletter"]
