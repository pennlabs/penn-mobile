from rest_framework import serializers

from sublet.models import Sublet, SubletImage, Offer, Favorite, Amenity


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = '__all__'
        read_only_fields = ("name",)


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = '__all__'


class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = '__all__'
        read_only_fields = ["id", "created_date", "user"]


class SubletSerializer(serializers.ModelSerializer):
    amenities = AmenitySerializer(many=True, required=False)
    favorites = FavoriteSerializer(many=True, required=False)
    sublettees = OfferSerializer(many=True, required=False)

    class Meta:
        model = Sublet
        fields = '__all__'
        read_only_fields = ["id", "created_date", "favorites", "sublettees"]