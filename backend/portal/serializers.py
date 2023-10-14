from rest_framework import serializers

from portal.logic import check_targets, get_user_clubs, get_user_populations
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
        # ensures user is part of club
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

        year = False
        major = False
        school = False
        degree = False

        for population in validated_data["target_populations"]:
            if population.kind == TargetPopulation.KIND_YEAR:
                year = True
            elif population.kind == TargetPopulation.KIND_MAJOR:
                major = True
            elif population.kind == TargetPopulation.KIND_SCHOOL:
                school = True
            elif population.kind == TargetPopulation.KIND_DEGREE:
                degree = True

        if not year:
            validated_data["target_populations"] += list(
                TargetPopulation.objects.filter(kind=TargetPopulation.KIND_YEAR)
            )
        if not major:
            validated_data["target_populations"] += list(
                TargetPopulation.objects.filter(kind=TargetPopulation.KIND_MAJOR)
            )
        if not school:
            validated_data["target_populations"] += list(
                TargetPopulation.objects.filter(kind=TargetPopulation.KIND_SCHOOL)
            )
        if not degree:
            validated_data["target_populations"] += list(
                TargetPopulation.objects.filter(kind=TargetPopulation.KIND_DEGREE)
            )

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
        fields = ("id", "id_hash", "poll", "poll_options", "created_date")
        read_only_fields = (
            "id",
            "created_date",
        )


class PostSerializer(serializers.ModelSerializer):

    image = serializers.ImageField(write_only=True, required=False, allow_null=True)
    image_url = serializers.SerializerMethodField("get_image_url")

    def get_image_url(self, obj):
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

    class Meta:
        model = Post
        fields = (
            "id",
            "club_code",
            "title",
            "subtitle",
            "post_url",
            "image",
            "image_url",
            "created_date",
            "start_date",
            "expire_date",
            "club_comment",
            "admin_comment",
            "status",
            "target_populations",
        )
        read_only_fields = ("id", "created_date", "target_populations")

    def parse_target_populations(self, raw_target_populations):
        if isinstance(raw_target_populations, list):
            ids = raw_target_populations
        else:
            ids = (
                list()
                if len(raw_target_populations) == 0
                else [int(id) for id in raw_target_populations.split(",")]
            )
        return TargetPopulation.objects.filter(id__in=ids)

    def update_target_populations(self, target_populations):
        year = False
        major = False
        school = False
        degree = False

        for population in target_populations:
            if population.kind == TargetPopulation.KIND_YEAR:
                year = True
            elif population.kind == TargetPopulation.KIND_MAJOR:
                major = True
            elif population.kind == TargetPopulation.KIND_SCHOOL:
                school = True
            elif population.kind == TargetPopulation.KIND_DEGREE:
                degree = True

        if not year:
            target_populations |= TargetPopulation.objects.filter(kind=TargetPopulation.KIND_YEAR)
        if not major:
            target_populations |= TargetPopulation.objects.filter(kind=TargetPopulation.KIND_MAJOR)
        if not school:
            target_populations |= TargetPopulation.objects.filter(kind=TargetPopulation.KIND_SCHOOL)
        if not degree:
            target_populations |= TargetPopulation.objects.filter(kind=TargetPopulation.KIND_DEGREE)

        return target_populations

    def create(self, validated_data):
        club_code = validated_data["club_code"]
        # Ensures user is part of club
        if club_code not in [
            x["club"]["code"] for x in get_user_clubs(self.context["request"].user)
        ]:
            raise serializers.ValidationError(
                detail={"detail": "You do not access to create a Poll under this club."}
            )

        # Ensuring user cannot create an admin comment upon creation
        validated_data["admin_comment"] = None
        validated_data["status"] = Post.STATUS_DRAFT

        instance = super().create(validated_data)

        # Update target populations
        # If none of a category was selected, then we will auto-select all populations in that categary
        data = self.context["request"].data
        raw_target_populations = self.parse_target_populations(data["target_populations"])
        target_populations = self.update_target_populations(raw_target_populations)

        instance.target_populations.set(target_populations)
        instance.save()

        return instance

    def update(self, instance, validated_data):
        # if post is updated, then approved should be false
        if not self.context["request"].user.is_superuser:
            validated_data["status"] = Post.STATUS_DRAFT

        data = self.context["request"].data

        # Additional logic for target populations
        if "target_populations" in data:
            target_populations = self.parse_target_populations(data["target_populations"])
            data = self.context["request"].data
            raw_target_populations = self.parse_target_populations(data["target_populations"])
            target_populations = self.update_target_populations(raw_target_populations)

            validated_data["target_populations"] = target_populations

        return super().update(instance, validated_data)
