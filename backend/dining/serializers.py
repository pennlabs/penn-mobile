from rest_framework import serializers

from dining.models import DiningItem, DiningMenu, DiningStation, Venue


class VenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        fields = ("venue_id", "name", "image_url")


class DiningItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiningItem
        fields = ("item_id", "name", "description", "ingredients")


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
        fields = ("venue", "date", "start_time", "end_time", "stations", "service")
