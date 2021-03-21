from rest_framework import serializers

from dining.models import DiningBalance, DiningTransaction


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
