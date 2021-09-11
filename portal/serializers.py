from rest_framework import serializers

from portal.logic import get_user_populations
from portal.models import Poll, PollOption, PollVote, TargetPopulation


class TargetPopulationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TargetPopulation
        fields = "__all__"


class PollSerializer(serializers.ModelSerializer):
    class Meta:
        model = Poll
        fields = (
            "id",
            "source",
            "question",
            "image_url",
            "created_date",
            "expire_date",
            "multiselect",
            "user_comment",
            "admin_comment",
            "approved",
            "target_populations",
        )
        read_only_fields = ("id", "created_date")

    def create(self, validated_data):
        # adds user to the Poll
        validated_data["user"] = self.context["request"].user
        # ensuring user cannot create an admin comment upon creation
        validated_data["admin_comment"] = ""
        validated_data["approved"] = False
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # if Poll is updated, then approve should be false
        if not self.context["request"].user.is_superuser:
            validated_data["approved"] = False
        return super().update(instance, validated_data)


class PollOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollOption
        fields = (
            "id",
            "poll",
            "choice",
        )

    def update(self, instance, validated_data):
        # if Poll Option is updated, then corresponding Poll approval should be false
        instance.poll.approved = False
        instance.poll.save()
        return super().update(instance, validated_data)


class RetrievePollSerializer(serializers.ModelSerializer):

    target_populations = TargetPopulationSerializer(many=True)
    options = PollOptionSerializer(source="polloption_set", many=True)

    class Meta:
        model = Poll
        fields = (
            "id",
            "source",
            "question",
            "image_url",
            "created_date",
            "expire_date",
            "multiselect",
            "user_comment",
            "options",
            "target_populations",
        )


class PollVoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollVote
        fields = ("id", "poll_options", "created_date")
        read_only_fields = ("created_date",)

    def create(self, validated_data):

        options = validated_data["poll_options"]
        poll = options[0].poll
        # checks if user has already voted
        if PollVote.objects.filter(user=self.context["request"].user, poll=poll).exists():
            raise serializers.ValidationError(
                detail={"detail": "You have already voted for this Poll"}
            )
        # check if user can multiselect or not
        if len(options) > 1 and not poll.multiselect:
            raise serializers.ValidationError(
                detail={"detail": "You cannot select multiple choices for this Poll"}
            )
        # check if poll options are all from same Poll
        for option in options:
            if option.poll != poll:
                raise serializers.ValidationError(
                    detail={"detail": "Voting options are from different Polls"}
                )
        # checks if user belongs to target population
        if not any(
            i in list(poll.target_populations.all().values_list("id", flat=True))
            for i in get_user_populations(self.context["request"].user)
        ):
            raise serializers.ValidationError(
                detail={"detail": "You cannot vote for this poll (not in any target population)"}
            )
        # adds poll and user to the vote
        validated_data["user"] = self.context["request"].user
        validated_data["poll"] = poll
        return super().create(validated_data)


class RetrievePollVoteSerializer(serializers.ModelSerializer):

    poll = RetrievePollSerializer()
    poll_options = PollOptionSerializer(many=True)

    class Meta:
        model = PollVote
        fields = ("id", "poll", "poll_options", "created_date")
