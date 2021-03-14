from rest_framework import serializers

from dining.models import DiningBalance, DiningTransaction


class DiningTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiningTransaction
        fields = ("date", "description", "amount", "balance")


class DiningBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiningBalance
        fields = ("dollars", "swipes", "guest_swipes")
