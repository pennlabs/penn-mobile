from typing import Any, ClassVar, Type, cast

from django.db.models import Model
from django.http.request import QueryDict
from rest_framework import serializers

from portal.logic import check_targets, get_user_clubs, get_user_populations
from portal.models import Content, Poll, PollOption, PollVote, Post, TargetPopulation


class TargetPopulationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TargetPopulation
        fields = "__all__"


class ContentSerializer(serializers.ModelSerializer):
    class Meta:
        model: ClassVar[Type[Model]]
        fields: tuple[str, ...] = (
            "id",
            "club_code",
            "created_date",
            "start_date",
            "expire_date",
            "club_comment",
            "admin_comment",
            "status",
            "target_populations",
        )
        read_only_fields: tuple[str, ...] = ("id", "created_date")
        abstract = True

    def _auto_add_target_population(self, validated_data: dict[str, Any]) -> None:
        # auto add all target populations of a kind if not specified
        if target_populations := validated_data.get("target_populations"):
            auto_add_kind = [
                kind
                for kind, _ in TargetPopulation.KIND_OPTIONS
                if not any(population.kind == kind for population in target_populations)
            ]
            validated_data["target_populations"] += TargetPopulation.objects.filter(
                kind__in=auto_add_kind
            )
        else:
            validated_data["target_populations"] = list(TargetPopulation.objects.all())

    def create(self, validated_data: dict[str, Any]) -> Poll:
        club_code: str = validated_data["club_code"]
        user = self.context["request"].user
        # ensures user is part of club
        if not any([x["club"]["code"] == club_code for x in get_user_clubs(user)]):
            model_name = (
                self.Meta.model._meta.model_name.capitalize()
                if self.Meta.model._meta.model_name is not None
                else "content"
            )
            raise serializers.ValidationError(
                detail={
                    "detail": f"You do not have access to create a {model_name} under this club."
                }
            )

        # ensuring user cannot create an admin comment upon creation
        validated_data["admin_comment"] = None
        validated_data["status"] = Content.STATUS_DRAFT

        self._auto_add_target_population(validated_data)

        validated_data["creator"] = user

        return super().create(validated_data)

    def update(self, instance: Content, validated_data: dict[str, Any]) -> Content:
        # if Content is updated, then approve should be false
        if not self.context["request"].user.is_superuser:
            validated_data["status"] = Content.STATUS_DRAFT

        self._auto_add_target_population(validated_data)

        return super().update(instance, validated_data)


class PollSerializer(ContentSerializer):
    class Meta(ContentSerializer.Meta):
        model = Poll
        fields: tuple[str, ...] = (*ContentSerializer.Meta.fields, "question", "multiselect")


class PollOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollOption
        fields: tuple[str, ...] = ("id", "poll", "choice", "vote_count")
        read_only_fields: tuple[str, ...] = ("id", "vote_count")

    def create(self, validated_data: dict[str, Any]) -> PollOption:
        poll_options_count = PollOption.objects.filter(poll=validated_data["poll"]).count()
        if poll_options_count >= 5:
            raise serializers.ValidationError(
                detail={"detail": "You cannot have more than 5 poll options for a poll"}
            )
        return super().create(validated_data)

    def update(self, instance: PollOption, validated_data: dict[str, Any]) -> PollOption:
        # if Poll Option is updated, then corresponding Poll approval should be false
        poll = cast(Poll, instance.poll)
        poll.status = Poll.STATUS_DRAFT
        poll.save()
        return super().update(instance, validated_data)


class RetrievePollSerializer(serializers.ModelSerializer):

    target_populations = TargetPopulationSerializer(many=True)
    options = PollOptionSerializer(source="polloption_set", many=True)

    class Meta:
        model = Poll
        fields: tuple[str, ...] = (
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
        fields: tuple[str, ...] = ("id", "id_hash", "poll_options", "created_date")
        read_only_fields: tuple[str, ...] = ("id", "created_date")

    def create(self, validated_data: dict[str, Any]) -> PollVote:

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

        # # check if user is in target population
        if not check_targets(poll, self.context["request"].user):
            raise serializers.ValidationError(
                detail={"detail": "You cannot vote for this poll (not in any target population)"}
            )

        # adds poll to the vote
        validated_data["poll"] = poll

        # increments poll options vote count from the vote
        for option in options:
            option.vote_count += 1
            option.save()

        # add populations to poll data
        populations = get_user_populations(self.context["request"].user)
        population_list = populations[0] + populations[1] + populations[2] + populations[3]

        # populates target populations
        validated_data["target_populations"] = [x.id for x in population_list]

        return super().create(validated_data)


class RetrievePollVoteSerializer(serializers.ModelSerializer):

    poll = RetrievePollSerializer()
    poll_options = PollOptionSerializer(many=True)
    created_date = serializers.DateTimeField()

    class Meta:
        model = PollVote
        fields: tuple[str, ...] = ("id", "id_hash", "poll", "poll_options", "created_date")
        read_only_fields: tuple[str, ...] = ("id", "created_date")


class PostSerializer(ContentSerializer):

    image = serializers.ImageField(write_only=True, required=False, allow_null=True)
    image_url = serializers.SerializerMethodField("get_image_url")

    def get_image_url(self, obj: Post) -> str | None:
        # use thumbnail if exists
        image = obj.image

        # fix image path in development
        if not image:
            return None
        if image.url.startswith("http"):
            return image.url
        elif "request" in self.context:
            return self.context["request"].build_absolute_uri(image.url)
        else:
            return image.url

    class Meta(ContentSerializer.Meta):
        model = Post
        fields: tuple[str, ...] = (
            *ContentSerializer.Meta.fields,
            "title",
            "subtitle",
            "post_url",
            "image",
            "image_url",
        )

    def is_valid(self, *args: Any, **kwargs: Any) -> bool:
        if isinstance(self.initial_data, QueryDict):
            data = self.initial_data.dict()
            target_populations = data.get("target_populations", "")
            if isinstance(target_populations, str):
                data["target_populations"] = (
                    list(map(int, target_populations.split(",")))
                    if target_populations.strip()
                    else []
                )
            self.initial_data = data
        return super().is_valid(*args, **kwargs)
