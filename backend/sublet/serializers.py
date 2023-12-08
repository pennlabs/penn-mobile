from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from rest_framework.generics import get_object_or_404

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
        fields = ["id", "image_url"]


# complex sublet serializer for use in C/U/D + getting info about a singular sublet
class SubletSerializer(serializers.ModelSerializer):
    amenities = AmenitySerializer(many=True, required=False)
    images = serializers.ListField(
        child=serializers.FileField(max_length=100000, allow_empty_file=False, use_url=False),
        required=False,
        write_only=True,
    )
    delete_images_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True
    )

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
            "min_price",
            "max_price",
            "start_date",
            "end_date",
            "expires_at",
            "images",
            "delete_images_ids",
        ]

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
        images = validated_data.pop("images")
        instance = super().create(validated_data)
        data = self.context["request"].POST
        amenities = self.parse_amenities(data.getlist("amenities"))
        instance.amenities.set(amenities)
        instance.save()
        # TODO: make this atomic
        img_serializers = []
        for img in images:
            img_serializer = SubletImageSerializer(data={"sublet": instance.id, "image": img})
            img_serializer.is_valid(raise_exception=True)
            img_serializers.append(img_serializer)
        [img_serializer.save() for img_serializer in img_serializers]
        return instance

    # delete_images is a list of image ids to delete
    def update(self, instance, validated_data):
        # Check if the user is the subletter before allowing the update
        if (
            self.context["request"].user == instance.subletter
            or self.context["request"].user.is_superuser
        ):
            amenities_data = self.context["request"].data
            if amenities_data.get("amenities") is not None:
                amenities = self.parse_amenities(amenities_data["amenities"])
                instance.amenities.set(amenities)
            validated_data.pop("amenities", None)
            delete_images_ids = validated_data.pop("delete_images_ids")
            instance = super().update(instance, validated_data)
            instance.save()
            existing_images = Sublet.objects.get(id=instance.id).images.all()
            [get_object_or_404(existing_images, id=img) for img in delete_images_ids]
            existing_images.filter(id__in=delete_images_ids).delete()
            return instance
        else:
            raise serializers.ValidationError("You do not have permission to update this sublet.")

    def destroy(self, instance):
        # Check if the user is the subletter before allowing the delete
        if (
            self.context["request"].user == instance.subletter
            or self.context["request"].user.is_superuser
        ):
            instance.delete()
        else:
            raise serializers.ValidationError("You do not have permission to delete this sublet.")


class SubletSerializerRead(serializers.ModelSerializer):
    amenities = AmenitySerializer(many=True, required=False)
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
            "min_price",
            "max_price",
            "start_date",
            "end_date",
            "expires_at",
            "images",
        ]


# simple sublet serializer for use when pulling all serializers/etc
class SubletSerializerSimple(serializers.ModelSerializer):
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
