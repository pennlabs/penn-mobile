from rest_framework import serializers

from sublet.models import Sublet, SubletImage, Offer, Favorite, Amenity

class SubletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sublet
        fields = '__all__'
        read_only_fields = ("id", "created_date")

    def create(self, validated_data):

    def update(self, instance, validated_data):