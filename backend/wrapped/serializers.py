from rest_framework import serializers
from .models import Page, IndividualStat, GlobalStat, IndividualStatThrough, GlobalStatThrough, Semester, User

class IndividualStatSerializer(serializers.ModelSerializer):
    key = serializers.StringRelatedField()

    class Meta:
        model = IndividualStat
        fields = ['key', 'value', 'semester']


class GlobalStatSerializer(serializers.ModelSerializer):
    key = serializers.StringRelatedField()

    class Meta:
        model = GlobalStat
        fields = ['key', 'value', 'semester']


class IndividualStatThroughSerializer(serializers.ModelSerializer):
    individual_stat_value = serializers.SerializerMethodField()

    class Meta:
        model = IndividualStatThrough
        fields = ['text_field_name', 'individual_stat_value']

    def get_individual_stat_value(self, obj):
        user = self.context.get('user')
        semester = self.context.get('semester')

        try:
            individual_stat = IndividualStat.objects.get(
                user=user,
                key=obj.IndividualStatKey,
                semester=semester
            )
            return individual_stat.value
        except IndividualStat.DoesNotExist:
            return None


class GlobalStatThroughSerializer(serializers.ModelSerializer):
    global_stat_value = serializers.SerializerMethodField()

    class Meta:
        model = GlobalStatThrough
        fields = ['text_field_name', 'global_stat_value']

    def get_global_stat_value(self, obj):
        semester = self.context.get('semester')

        try:
            global_stat = GlobalStat.objects.get(
                key=obj.GlobalStatKey.key,
                semester=semester
            )
            return global_stat.value
        except GlobalStat.DoesNotExist:
            return None


class PageSerializer(serializers.ModelSerializer):
    combined_stats = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = ['name', 'template_path', 'combined_stats']

    def get_combined_stats(self, obj):
        user = self.context.get('user')
        semester = self.context.get('semester')

        individual_throughs = IndividualStatThrough.objects.filter(Page=obj)
        combined_stats = {}
        for entry in individual_throughs:
            individual_stat = IndividualStat.objects.filter(
                user=user, key=entry.IndividualStatKey, semester=semester
            ).first()
            if individual_stat:
                combined_stats[entry.text_field_name] = individual_stat.value

        global_throughs = GlobalStatThrough.objects.filter(Page=obj)
        for entry in global_throughs:
            global_stat = GlobalStat.objects.filter(
                key=entry.GlobalStatKey.key, semester=semester
            ).first()
            if global_stat:
                combined_stats[entry.text_field_name] = global_stat.value

        return combined_stats


class SemesterSerializer(serializers.ModelSerializer):
    pages = serializers.SerializerMethodField()

    class Meta:
        model = Semester
        fields = ['semester', 'pages']

    def get_pages(self, obj):
        user = self.context.get('user')

        pages = obj.pages.all()
        serializer = PageSerializer(pages, many=True, context={'user': user, 'semester': obj})
        return serializer.data
