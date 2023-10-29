from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

from sublet.models import Amenity, Offer, Sublet


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
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


# complex sublet serializer for use in C/U/D + getting info about a singular sublet
class SubletSerializer(serializers.ModelSerializer):
    amenities = AmenitySerializer(many=True, required=False)
    # sublettees = OfferSerializer(many=True, required=False, read_only=True)

    class Meta:
        model = Sublet
        exclude = ["favorites"]
        read_only_fields = ["id", "created_at", "subletter", "sublettees"]

    def parse_amenities(self, raw_amenities):
        if isinstance(raw_amenities, list):
            ids = raw_amenities
        else:
            ids = (
                list() if len(raw_amenities) == 0 else [str(id) for id in raw_amenities.split(",")]
            )
        return Amenity.objects.filter(name__in=ids)

    def create(self, validated_data):
        validated_data["subletter"] = self.context["request"].user
        instance = super().create(validated_data)
        data = self.context["request"].POST
        amenities = self.parse_amenities(data.getlist("amenities"))
        instance.amenities.set(amenities)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        # Check if the user is the subletter before allowing the update
        if (
            self.context["request"].user == instance.subletter
            or self.context["request"].user.is_superuser
        ):
            amenities_data = self.context["request"].data
            if amenities_data.get("amenities") is not None:
                amenities = self.parse_amenities(amenities_data.getlist("amenities"))
                instance.amenities.set(amenities)
            validated_data.pop("amenities", None)
            instance = super().update(instance, validated_data)
            instance.save()
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


# simple sublet serializer for use when pulling all serializers/etc
class SimpleSubletSerializer(serializers.ModelSerializer):
    amenities = AmenitySerializer(many=True, required=False)

    class Meta:
        model = Sublet
        fields = [
            "id",
            "subletter",
            "amenities",
            "title",
            "address",
            "beds",
            "baths",
            "min_price",
            "max_price",
            "start_date",
            "end_date",
        ]
        read_only_fields = ["id", "subletter"]
