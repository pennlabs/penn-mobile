from phonenumber_field.serializerfields import PhoneNumberField
from profanity_check import predict
from rest_framework import serializers

from market.models import Tag, Category, Offer, Item, Sublet, ItemImage
from django.contrib.auth import get_user_model

User = get_user_model()

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["name"]
        read_only_fields = ["name"]


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
        fields = ["item", "image"]


# Browse images
class ItemImageURLSerializer(serializers.ModelSerializer):
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
        model = ItemImage
        fields = ["id", "image_url"]


# complex item serializer for use in C/U/D + getting info about a singular tag
class ItemSerializer(serializers.ModelSerializer):
    # amenities = ItemSerializer(many=True, required=False)
    # images = ItemImageURLSerializer(many=True, required=False)

    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), required=False
    )
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), required=True
    )
    seller = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    favorites = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(), required=False
    )

    class Meta:
        model = Item
        read_only_fields = [
            "id",
            "created_at",
            "seller",
            "buyer",
            # "images"
        ]
        fields = [
            "id",
            "seller",
            "tags",
            "category",
            "favorites",
            "title",
            "description",
            "external_link",
            "price",
            "negotiable",
            "expires_at",
            # "images",
            # images are now created/deleted through a separate endpoint (see urls.py)
            # this serializer isn't used for getting,
            # but gets on tags will include ids/urls for images
        ]

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
        category_name = validated_data.pop("category")
        category_instance = Category.objects.get(name=category_name)
        validated_data["category"] = category_instance
        instance = super().create(validated_data)
        instance.save()
        return instance

    # delete_images is a list of image ids to delete
    def update(self, instance, validated_data):
        # Check if the user is the seller before allowing the update
        if (
            self.context["request"].user == instance.seller
            or self.context["request"].user.is_superuser
        ):
            instance = super().update(instance, validated_data)
            instance.save()
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


class ItemSerializerRead(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), required=False
    )
    images = ItemImageURLSerializer(many=True, required=False)
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), required=True
    )
    seller = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)

    class Meta:
        model = Item
        read_only_fields = ["id", "created_at", "seller", "buyer"]
        fields = [
            "id",
            "seller",
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


# simple tag serializer for use when pulling all serializers/etc
class ItemSerializerSimple(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), required=False
    )
    images = ItemImageURLSerializer(many=True, required=False)
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), required=True
    )
    seller = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)

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
        read_only_fields = ["id", "seller"]


class SubletSerializer(serializers.ModelSerializer):
    item = ItemSerializer(required=True)
    class Meta:
        model = Sublet
        fields = [
            'id',
            'item',
            'address',
            'beds',
            'baths',
            'start_date',
            'end_date'
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        item_data = validated_data.pop('item')
        item_serializer = ItemSerializer(data=item_data, context=self.context)
        item_serializer.is_valid(raise_exception=True)
        item_instance = item_serializer.save(seller=self.context['request'].user)
        sublet_instance = Sublet.objects.create(item=item_instance, **validated_data)
        return sublet_instance

    def update(self, instance, validated_data):
        if (
            self.context["request"].user == instance.item.seller
            or self.context["request"].user.is_superuser
        ):
            item_data = validated_data.pop('item', None)
            if item_data:
                tags = item_data.pop('tags', None)  # Extract tags if present
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
            if self.context["request"].user == instance.item.seller or self.context["request"].user.is_superuser:
                instance.item.delete()
                instance.delete()
            else:
                raise serializers.ValidationError("You do not have permission to delete this sublet.")