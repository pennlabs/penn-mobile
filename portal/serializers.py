from rest_framework import serializers

from portal.models import Poll, PollOption


class UserPollSerializer(serializers.ModelSerializer):
    class Meta:
        model = Poll
        fields = ("id", "source", "question", "expire_date")

    def create(self, validated_data):
        instance = Poll(**validated_data, user=self.context["request"].user)
        instance.save()
        return instance


class AdminPollSerializer(serializers.ModelSerializer):
    class Meta:
        model = Poll
        fields = ("approved",)


class PollOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollOption
        fields = (
            "poll",
            "choice",
        )


class RetrievePollSerializer(serializers.ModelSerializer):

    options = PollOptionSerializer(source="polloption_set", many=True)

    class Meta:
        model = Poll
        fields = ("id", "source", "question", "expire_date", "options")
