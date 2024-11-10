from rest_framework import serializers
from .models import Page, IndividualStat, GlobalStat, IndividualStatPageField, GlobalStatPageField, Semester, User

class IndividualStatSerializer(serializers.ModelSerializer):
    key = serializers.SlugRelatedField(
        slug_field='key',  
        read_only=True
    )
    class Meta:
        model = IndividualStat
        fields = ['key', 'value', 'semester']


class GlobalStatSerializer(serializers.ModelSerializer):
    key = serializers.SlugRelatedField(
        slug_field='key', 
        read_only=True
    )
    class Meta:
        model = GlobalStat
        fields = ['key', 'value', 'semester']


class IndividualStatPageFieldSerializer(serializers.ModelSerializer):
    individual_stat_value = serializers.SerializerMethodField()

    class Meta:
        model = IndividualStatPageField
        fields = ['text_field_name', 'individual_stat_value']

    def get_individual_stat_value(self, obj):
        user = self.context.get('user')
        semester = self.context.get('semester')

        try:
            individual_stat = IndividualStat.objects.filter(
                user=user,
                key=obj.individual_stat_key,
                semester=semester
            ).first()
            return individual_stat.value
        except IndividualStat.DoesNotExist:
            return None


class GlobalStatThroughSerializer(serializers.ModelSerializer):
    global_stat_value = serializers.SerializerMethodField()

    class Meta:
        model = GlobalStatPageField
        fields = ['text_field_name', 'global_stat_value']

    def get_global_stat_value(self, obj):
        semester = self.context.get('semester')
        try:
            global_stat = GlobalStat.objects.filter(
                key=obj.global_stat_key.key,
                semester=semester
            ).first()
            return global_stat.value
        except GlobalStat.DoesNotExist:
            return None



class PageSerializer(serializers.ModelSerializer):

    combined_stats = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = ['name', 'template_path', 'combined_stats', 'duration']

    def get_combined_stats(self, obj):
        user = self.context.get('user')
        semester = self.context.get('semester')
        combined_stats = {}

        for entry in obj.individualstatpagefield_set.all():
            individual_stat_serializer = IndividualStatPageFieldSerializer(
                entry, context={'user': user, 'semester': semester}
            )
            combined_stats[entry.text_field_name] = individual_stat_serializer.data.get('individual_stat_value')

        for entry in obj.globalstatpagefield_set.all():
            global_stat_serializer = GlobalStatThroughSerializer(
                entry, context={'semester': semester}
            )
            combined_stats[entry.text_field_name] = global_stat_serializer.data.get('global_stat_value')

        return combined_stats


class SemesterSerializer(serializers.ModelSerializer):
    pages = serializers.SerializerMethodField()

    class Meta:
        model = Semester
        fields = ['semester', 'pages']

    def get_pages(self, obj):
        user = self.context.get('user')
        return PageSerializer(obj.pages.all(), many=True, context={'user': user, 'semester': obj}).data
    
