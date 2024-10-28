from phonenumber_field.serializerfields import PhoneNumberField
from profanity_check import predict
from rest_framework import serializers

from market.models import Tag, Category, Offer, Item, Sublet, ItemImage


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
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


class SubletSerializer(serializers.ModelSerializer):
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
        read_only_fields = ['id', 'item']
    


# complex item serializer for use in C/U/D + getting info about a singular tag
class ItemSerializer(serializers.ModelSerializer):
    # amenities = ItemSerializer(many=True, required=False)
    # images = ItemImageURLSerializer(many=True, required=False)

    sublet = SubletSerializer(required=False)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), required=False
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
            "sublet",
            "category",
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
    
    def validate(self, data):
        print(data)
        if data.get('category').name=="Sublet" and data.get('sublet') is None:
            raise serializers.ValidationError("Sublet item must have sublet data.")
        if data.get('category').name!="Sublet" and (data.get('sublet') is not None or "sublet" not in data):
            raise serializers.ValidationError("Only Sublet items can have sublet data.")
        return data

    def create(self, validated_data):
        sublet_data = validated_data.pop('sublet', None)
        validated_data["seller"] = self.context["request"].user
        instance = super().create(validated_data)

        if sublet_data:
            Sublet.objects.create(item=instance, **sublet_data)
        
        instance.save()
        return instance

    # delete_images is a list of image ids to delete
    def update(self, instance, validated_data):
        # Check if the user is the seller before allowing the update
        sublet_data = validated_data.pop('sublet', None)
        if (
            self.context["request"].user == instance.seller
            or self.context["request"].user.is_superuser
        ):
            instance = super().update(instance, validated_data)

            if sublet_data:
                if hasattr(instance, 'sublet'):
                    # If Sublet already exists, update it
                    for attr, value in sublet_data.items():
                        setattr(instance.sublet, attr, value)
                    instance.sublet.save()
                else:
                    # If Sublet doesn't exist, create a new one
                    Sublet.objects.create(item=instance, **sublet_data)

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
            if hasattr(instance, 'sublet'):
                instance.sublet.delete()

            instance.delete()
        else:
            raise serializers.ValidationError("You do not have permission to delete this item.")


class ItemSerializerRead(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), required=False
    )
    sublet = SubletSerializer(read_only=True, required=False)
    images = ItemImageURLSerializer(many=True, required=False)

    class Meta:
        model = Item
        read_only_fields = ["id", "created_at", "seller", "buyer"]
        fields = [
            "id",
            "seller",
            "tags",
            "sublet",
            "category",
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
    sublet = SubletSerializer(required=False)
    images = ItemImageURLSerializer(many=True, required=False)

    class Meta:
        model = Item
        fields = [
            "id",
            "seller",
            "tags",
            "sublet",
            "category",
            "title",
            "price",
            "negotiable",
            "images",
        ]
        read_only_fields = ["id", "seller"]


