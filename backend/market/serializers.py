from django.contrib.auth import get_user_model
from phonenumber_field.serializerfields import PhoneNumberField
from profanity_check import predict
from rest_framework import serializers

from market.models import Category, Item, ItemImage, Offer, Sublet, Tag


User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"
        read_only_fields = [field.name for field in model._meta.fields]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"
        read_only_fields = [field.name for field in model._meta.fields]


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
class ItemImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = ItemImage
        fields = "__all__"


# Browse images
class ItemImageURLSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

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
        model = ItemImage
        fields = "__all__"
        read_only_fields = [field.name for field in model._meta.fields]


# complex item serializer for use in C/U/D + getting info about a singular tag
class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = [
            "id",
            "seller",
            "buyers",
            "tags",
            "category",
            "favorites",
            "title",
            "description",
            "external_link",
            "price",
            "negotiable",
            "expires_at",
            "images",
        ]
        read_only_fields = ["id", "created_at", "seller", "buyers", "images"]

    def validate_title(self, value):
        if self.contains_profanity(value):
            raise serializers.ValidationError("The title contains inappropriate language.")
        return value

    def validate_description(self, value):
        if self.contains_profanity(value):
            raise serializers.ValidationError("The description contains inappropriate language.")
        return value

    def contains_profanity(self, text):
        return predict([text])[0]

    def create(self, validated_data):
        validated_data["seller"] = self.context["request"].user
        instance = super().create(validated_data)
        return instance

    # delete_images is a list of image ids to delete
    def update(self, instance, validated_data):
        # Check if the user is the seller before allowing the update
        if (
            self.context["request"].user == instance.seller
            or self.context["request"].user.is_superuser
        ):
            instance = super().update(instance, validated_data)
            return instance
        else:
            raise serializers.ValidationError("You do not have permission to update this item.")

    def destroy(self, instance):
        # Check if the user is the seller before allowing the delete
        if (
            self.context["request"].user == instance.seller
            or self.context["request"].user.is_superuser
        ):
            instance.delete()
        else:
            raise serializers.ValidationError("You do not have permission to delete this item.")


# Read-only serializer for use when pulling all items/etc
class ItemSerializerRead(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = [
            "id",
            "seller",
            "tags",
            "category",
            "favorites",
            "title",
            "price",
            "negotiable",
            "images",
        ]
        read_only_fields = fields


class SubletSerializer(serializers.ModelSerializer):
    item = ItemSerializer(required=True)

    class Meta:
        model = Sublet
        fields = ["id", "item", "address", "beds", "baths", "start_date", "end_date"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        item_serializer = ItemSerializer(data=validated_data.pop("item"), context=self.context)
        item_serializer.is_valid(raise_exception=True)
        validated_data["item"] = item_serializer.save()
        instance = super().create(validated_data)
        return instance

    def update(self, instance, validated_data):
        if (
            self.context["request"].user == instance.item.seller
            or self.context["request"].user.is_superuser
        ):
            item_data = validated_data.pop("item", None)
            if item_data:
                tags = item_data.pop("tags", None)  # Extract tags if present
                for attr, value in item_data.items():
                    setattr(instance.item, attr, value)
                instance.item.save()

                # Update tags if provided
                if tags is not None:
                    instance.item.tags.set(tags)  # Use .set() for many-to-many fields

            # Update the remaining Sublet fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance

    def destroy(self, instance):
        if (
            self.context["request"].user == instance.item.seller
            or self.context["request"].user.is_superuser
        ):
            if (
                self.context["request"].user == instance.item.seller
                or self.context["request"].user.is_superuser
            ):
                instance.item.delete()
                instance.delete()
            else:
                raise serializers.ValidationError(
                    "You do not have permission to delete this sublet."
                )
