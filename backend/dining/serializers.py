import json

from rest_framework import serializers

from dining.models import DiningItem, DiningMenu, DiningStation, Venue


class VenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        fields = "__all__"


class DiningItemSerializer(serializers.ModelSerializer):
    nutrition_info = serializers.SerializerMethodField()

    class Meta:
        model = DiningItem
        fields = "__all__"

    def get_nutrition_info(self, obj):
        try:
            return json.loads(obj.nutrition_info)
        except json.JSONDecodeError:
            return obj.nutrition_info


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
