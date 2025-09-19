from rest_framework import serializers

from wrapped.models import GlobalStatPageField, IndividualStatPageField, Page, Semester


class PageFieldSerializer(serializers.ModelSerializer):
    stat_value = serializers.SerializerMethodField()

    class Meta:
        abstract = True
        fields = ["text_field_name", "stat_value"]

    def get_stat_value(self, obj):
        user = self.context.get("user")
        semester = self.context.get("semester")
        return obj.get_value(user, semester)


class IndividualStatPageFieldSerializer(PageFieldSerializer):
    class Meta(PageFieldSerializer.Meta):
        model = IndividualStatPageField


class GlobalStatPageFieldSerializer(PageFieldSerializer):
    class Meta(PageFieldSerializer.Meta):
        model = GlobalStatPageField


class PageSerializer(serializers.ModelSerializer):

    combined_stats = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = ["id", "name", "template_path", "combined_stats", "duration"]

    def get_combined_stats(self, obj):
        if not (semester := self.context.get("semester", obj)):
            return {}
        user = self.context.get("user")
        individual_stat_fields = IndividualStatPageFieldSerializer(
            obj.individualstatpagefield_set.all(),
            context={"semester": semester, "user": user},
            many=True,
        ).data

        global_stat_fields = GlobalStatPageFieldSerializer(
            obj.globalstatpagefield_set.all(),
            context={"semester": semester, "user": user},
            many=True,
        ).data

        field_list = individual_stat_fields + global_stat_fields

        return {field["text_field_name"]: field["stat_value"] for field in field_list}


class SemesterSerializer(serializers.ModelSerializer):
    pages = serializers.SerializerMethodField()

    class Meta:
        model = Semester
        fields = ["semester", "pages"]

    def get_pages(self, obj):
        user = self.context.get("user")
        return PageSerializer(
            obj.pages.all(), many=True, context={"semester": obj, "user": user}
        ).data
