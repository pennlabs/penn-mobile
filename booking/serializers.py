from django.contrib.auth import get_user_model

from rest_framework import serializers

from booking.models import GroupMembership, Group

User = get_user_model()


class GroupMembershipSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())
    group = serializers.SlugRelatedField(slug_field='name', queryset=Group.objects.all())

    class Meta:
        model = GroupMembership
        fields = '__all__'


class GroupSerializer(serializers.ModelSerializer):
    owner = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())
    members = serializers.SlugRelatedField(many=True, slug_field='username', read_only=True)

    class Meta:
        model = Group
        fields = ['owner', 'members', 'name', 'color', 'id']

    def create(self, validated_data):
        group = super().create(validated_data)
        group.members.add(validated_data['owner'])
        memship = group.groupmembership_set.all()[0]
        memship.accepted = True
        memship.save()
        return group


class GroupField(serializers.RelatedField):
    def to_representation(self, value):
        return {
            'name': value.name,
            'id': value.id,
        }

    def to_internal_value(self, data):
        return None  # TODO: If you want to update based on BookingField, implement this.


class UserSerializer(serializers.ModelSerializer):
    booking_groups = GroupField(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['username', 'booking_groups']
