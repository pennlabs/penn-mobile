from rest_framework import serializers

from portal.models import Poll, PollOption, PollVote


class PollSerializer(serializers.ModelSerializer):
    class Meta:
        model = Poll
        fields = ("id", "source", "question", "expire_date", "admin_comment", "approved")

    def create(self, validated_data):
        # adds user to the Poll
        validated_data["user"] = self.context["request"].user
        # ensuring user cannot create an admin comment upon creation
        validated_data["admin_comment"] = ""
        validated_data["approved"] = False
        return super().create(validated_data)


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
        fields = (
            "id",
            "source",
            "question",
            "created_date",
            "expire_date",
            "options",
            "admin_comment",
            "approved",
        )


class PollVoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollVote
        fields = ("id", "poll_option")

    def create(self, validated_data):
        # adds poll and user to the vote
        validated_data["user"] = self.context["request"].user
        validated_data["poll"] = validated_data["poll_option"].poll
        return super().create(validated_data)


class RetrievePollVoteSerializer(serializers.ModelSerializer):

    poll = RetrievePollSerializer()
    poll_option = PollOptionSerializer()

    class Meta:
        model = PollVote
        fields = ("id", "poll", "poll_option")
