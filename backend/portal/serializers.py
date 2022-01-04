from rest_framework import serializers

from portal.logic import get_user_clubs, get_user_populations
from portal.models import Poll, PollOption, PollVote, Post, TargetPopulation


class TargetPopulationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TargetPopulation
        fields = "__all__"


class PollSerializer(serializers.ModelSerializer):
    class Meta:
        model = Poll
        fields = (
            "id",
            "club_code",
            "question",
            "created_date",
            "start_date",
            "expire_date",
            "multiselect",
            "club_comment",
            "admin_comment",
            "status",
            "target_populations",
        )
        read_only_fields = ("id", "created_date")

    def create(self, validated_data):
        club_code = validated_data["club_code"]
        if club_code not in [
            x["club"]["code"] for x in get_user_clubs(self.context["request"].user)
        ]:
            raise serializers.ValidationError(
                detail={"detail": "You do not access to create a Poll under this club."}
            )
        # ensuring user cannot create an admin comment upon creation
        validated_data["admin_comment"] = None
        validated_data["status"] = Poll.STATUS_DRAFT

        # TODO: toggle this off when multiselect functionality is available
        validated_data["multiselect"] = False

        if len(validated_data["target_populations"]) == 0:
            validated_data["target_populations"] = list(TargetPopulation.objects.all())

        return super().create(validated_data)

    def update(self, instance, validated_data):
        # if Poll is updated, then approve should be false
        if not self.context["request"].user.is_superuser:
            validated_data["status"] = Poll.STATUS_DRAFT
        return super().update(instance, validated_data)


class PollOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollOption
        fields = (
            "id",
            "poll",
            "choice",
            "vote_count",
        )
        read_only_fields = ("id", "vote_count")

    def create(self, validated_data):
        poll_options_count = PollOption.objects.filter(poll=validated_data["poll"]).count()
        if poll_options_count >= 5:
            raise serializers.ValidationError(
                detail={"detail": "You cannot have more than 5 poll options for a poll"}
            )
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # if Poll Option is updated, then corresponding Poll approval should be false
        instance.poll.status = Poll.STATUS_DRAFT
        instance.poll.save()
        return super().update(instance, validated_data)


class RetrievePollSerializer(serializers.ModelSerializer):

    target_populations = TargetPopulationSerializer(many=True)
    options = PollOptionSerializer(source="polloption_set", many=True)

    class Meta:
        model = Poll
        fields = (
            "id",
            "club_code",
            "question",
            "created_date",
            "start_date",
            "expire_date",
            "multiselect",
            "club_comment",
            "status",
            "options",
            "target_populations",
        )


class PollVoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollVote
        fields = ("id", "id_hash", "poll_options", "created_date")
        read_only_fields = (
            "id",
            "created_date",
        )

    def create(self, validated_data):

        options = validated_data["poll_options"]
        id_hash = validated_data["id_hash"]

        poll = options[0].poll
        # checks if user has already voted
        if PollVote.objects.filter(id_hash=id_hash, poll=poll).exists():
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
        # check if user is in target population
        if (
            not poll.target_populations.filter(
                id__in=[x.id for x in get_user_populations(self.context["request"].user)]
            ).exists()
            and not self.context["request"].user.is_superuser
        ):
            raise serializers.ValidationError(
                detail={"detail": "You cannot vote for this poll (not in any target population)"}
            )
        # adds poll to the vote
        validated_data["poll"] = poll

        # increments poll options vote count from the vote
        for option in options:
            option.vote_count += 1
            option.save()

        # populates target populations
        validated_data["target_populations"] = [
            x.id for x in get_user_populations(self.context["request"].user)
        ]

        return super().create(validated_data)

    def update(self, instance, validated_data):
        # update poll options count
        for option in instance.poll_options.all():
            option.vote_count -= 1
            option.save()
        for option in validated_data["poll_options"]:
            option.vote_count += 1
            option.save()
        return super().update(instance, validated_data)


class RetrievePollVoteSerializer(serializers.ModelSerializer):

    poll = RetrievePollSerializer()
    poll_options = PollOptionSerializer(many=True)

    class Meta:
        model = PollVote
        fields = ("id", "id_hash", "poll", "poll_options", "created_date")


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = (
            "id",
            "source",
            "title",
            "subtitle",
            "post_url",
            "image_url",
            "target_populations",
            "start_date",
            "expire_date",
            "approved",
            "created_at",
        )

    def create(self, validated_data):
        # adds the creator to the post
        validated_data["user"] = self.context["request"].user
        # ensuring user cannot create an admin comment upon creation
        validated_data["approved"] = False
        validated_data["admin_comment"] = None
        if len(validated_data["target_populations"]) == 0:
            validated_data["target_populations"] = list(TargetPopulation.objects.all())
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # if post is updated, then approved should be false
        if not self.context["request"].user.is_superuser:
            validated_data["approved"] = False
        if "approved" in validated_data and validated_data["approved"]:
            instance.admin_comment = None
        return super().update(instance, validated_data)
