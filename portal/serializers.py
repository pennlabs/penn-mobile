from rest_framework import serializers

from portal.models import Poll, PollOption, PollVote


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
        fields = "__all__"


class PollOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollOption
        fields = (
            "id",
            "poll",
            "choice",
        )


class RetrievePollSerializer(serializers.ModelSerializer):

    options = PollOptionSerializer(source="polloption_set", many=True)

    class Meta:
        model = Poll
        fields = ("id", "source", "created_date", "question", "expire_date", "options")


class CreatePollVoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollVote
        fields = ("poll_option",)

    def create(self, validated_data):
        instance = PollVote(
            **validated_data,
            user=self.context["request"].user,
            poll=validated_data["poll_option"].poll
        )
        instance.save()
        return instance


class RetrievePollVoteSerializer(serializers.ModelSerializer):

    poll = RetrievePollSerializer()
    poll_option = PollOptionSerializer()

    class Meta:
        model = PollVote
        fields = ("id", "poll", "poll_option")
