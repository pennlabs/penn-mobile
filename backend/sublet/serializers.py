from rest_framework import serializers

from sublet.models import Amenity, Favorite, Offer, Sublet, SubletImage


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = "__all__"


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = "__all__"


class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = "__all__"
        read_only_fields = ["id", "created_date", "user"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class SubletSerializer(serializers.ModelSerializer):
    amenities = AmenitySerializer(many=True, required=False)
    favorites = FavoriteSerializer(many=True, required=False, read_only=True)
    sublettees = OfferSerializer(many=True, required=False, read_only=True)

    class Meta:
        model = Sublet
        fields = "__all__"
        read_only_fields = ["id", "created_date", "subletter", "favorites", "sublettees"]

    def create(self, validated_data):
        validated_data["subletter"] = self.context["request"].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Check if the user is the subletter before allowing the update
        if (
            self.context["request"].user == instance.subletter
            or self.context["request"].user.is_superuser
        ):
            instance = super().update(instance, validated_data)
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


class FavoritesListSerializer(serializers.ModelSerializer):
    sublet = SubletSerializer()

    class Meta:
        model = Favorite
        fields = ["sublet"]
        read_only_fields = ["id"]
