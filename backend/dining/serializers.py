from rest_framework import serializers

from dining.models import DiningItem, DiningMenu, DiningStation, Venue


class VenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        fields = "__all__"


class DiningItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiningItem
        fields = "__all__"


class DiningStationSerializer(serializers.ModelSerializer):
    items = DiningItemSerializer(many=True)

    class Meta:
        model = DiningStation
        fields = ("name", "items")


class DiningMenuSerializer(serializers.ModelSerializer):
    venue = VenueSerializer()
    stations = DiningStationSerializer(many=True)

    class Meta:
        model = DiningMenu
        fields = "__all__"
