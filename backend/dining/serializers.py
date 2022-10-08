from rest_framework import serializers

from dining.models import (
    DiningBalance,
    DiningItem,
    DiningMenu,
    DiningStation,
    DiningTransaction,
    Venue,
)


class VenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        fields = ("venue_id", "name", "image_url")


class DiningTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiningTransaction
        fields = ("date", "description", "amount", "balance")

    def to_representation(self, instance):
        date_format = "%Y-%m-%dT%H:%M:%S"
        instance.date = instance.date.strftime(date_format)
        return super().to_representation(instance)


class DiningBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiningBalance
        fields = ("dining_dollars", "swipes", "guest_swipes")


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
