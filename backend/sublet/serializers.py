from rest_framework import serializers

from sublet.models import Amenity, Offer, Sublet, SubletImage


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = "__all__"


class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = "__all__"
        read_only_fields = ["id", "created_date", "user"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


# complex sublet serializer for use in creation/updating/deletion + getting info about a singular sublet
class SubletSerializer(serializers.ModelSerializer):
    amenities = AmenitySerializer(many=True, required=False)
    # sublettees = OfferSerializer(many=True, required=False, read_only=True)

    class Meta:
        model = Sublet
        exclude = ["favorites"]
        read_only_fields = ["id", "created_date", "subletter", "sublettees"]

    #  def parse_target_populations(self, raw_target_populations):
    #     if isinstance(raw_target_populations, list):
    #         ids = raw_target_populations
    #     else:
    #         ids = (
    #             list()
    #             if len(raw_target_populations) == 0
    #             else [int(id) for id in raw_target_populations.split(",")]
    #         )
    #     return TargetPopulation.objects.filter(id__in=ids)

    def create(self, validated_data):
        validated_data["subletter"] = self.context["request"].user
        # x = validated_data.pop("amenities")
        # print(x)

        instance = super().create(validated_data)

        # # Update target populations
        # # If none of a category was selected, then we will auto-select all populations in that categary
        data = self.context["request"].data
        print("HELLO")
        print(data)
        print(data["amenities"])
        print(Amenity.objects.all())
        amenities = Amenity.objects.filter(name__in=data["amenities"])
        print(amenities)
        # raw_amenities = 
        # raw_target_populations = self.parse_target_populations(data["target_populations"])
        # target_populations = self.update_target_populations(raw_target_populations)

        # instance.target_populations.set(target_populations)
        # instance.save()

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
