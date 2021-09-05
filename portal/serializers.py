from rest_framework import serializers

from portal.models import Poll, PollOption, PollVote


class UserPollSerializer(serializers.ModelSerializer):
    class Meta:
        model = Poll
        fields = ("id", "source", "question", "expire_date", "admin_comment")

    def create(self, validated_data):
        # adds user to the Poll
        instance = Poll(**validated_data, user=self.context["request"].user)
        # ensuring user cannot create an admin comment upon creation
        instance.admin_comment = ""
        instance.save()
        return instance

    def update(self, instance, validated_data):
        user = self.context["request"].user
        # checks if user is allowed to update or not
        if user != instance.user:
            raise serializers.ValidationError(detail={"detail": "User not allowed to update."})
        return super().update(instance, validated_data)


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

    def update(self, instance, validated_data):
        user = self.context["request"].user
        # checks to see if user can update the option
        if user != instance.poll.user:
            raise serializers.ValidationError(detail={"detail": "User not allowed to update."})
        return super().update(instance, validated_data)


class RetrievePollSerializer(serializers.ModelSerializer):

    options = PollOptionSerializer(source="polloption_set", many=True)

    class Meta:
        model = Poll
        fields = ("id", "source", "created_date", "question", "expire_date", "options")


class CreateUpdatePollVoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollVote
        fields = ("id", "poll_option")

    def create(self, validated_data):
        # adds poll and user to the vote
        instance = PollVote(
            **validated_data,
            user=self.context["request"].user,
            poll=validated_data["poll_option"].poll
        )
        instance.save()
        return instance

    def update(self, instance, validated_data):
        user = self.context["request"].user
        # makes sure only user can adjust vote (admins cannot change votes)
        if user != instance.user:
            raise serializers.ValidationError(detail={"detail": "User not allowed to update."})
        return super().update(instance, validated_data)


class RetrievePollVoteSerializer(serializers.ModelSerializer):

    poll = RetrievePollSerializer()
    poll_option = PollOptionSerializer()

    class Meta:
        model = PollVote
        fields = ("id", "poll", "poll_option")
