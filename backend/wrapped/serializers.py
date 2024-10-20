from django.contrib.auth import get_user_model
from rest_framework import serializers

from wrapped.models import GlobalStat, IndividualStat, UserStatKey, StatLocation, Page

User = get_user_model()

class MiniUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name"]


class StatLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatLocation
        fields = ["IndividualStatKey", "GlobalStatKey", "text_field_name"]

class IndividualStatSerializer(serializers.ModelSerializer):
    class Meta: 
        model = IndividualStat
        fields = ["user", "stat_key", "stat_value", "semester"]

class GlobalStatSerializer(serializers.ModelSerializer):
    class Meta: 
        model = GlobalStat
        fields = ["stat_key", "stat_value", "semester"]

class UserStatKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserStatKey
        fields = ["stat_key"]

class PageSerializer(serializers.ModelSerializer):
    stat_location_data = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = ["name", "template_path", "stat_location_data"]
    
    def get_stat_location_data(self, obj):
        location_stat_dict = {}
        for stat_location in obj.stat_locations.all():
            individual_stat_data = None
            if stat_location.IndividualStatKey:
                individual_stats = IndividualStat.objects.filter(stat_key=stat_location.IndividualStatKey).filter(semester=obj.semester)
                individual_stat_data = IndividualStatSerializer(individual_stats, many=True).data
                        
            global_stat_data = None
            if stat_location.GlobalStatKey:
                global_stat_data = GlobalStatSerializer(stat_location.GlobalStatKey, many=False).data

            if global_stat_data == None:

                location_stat_dict[stat_location.text_field_name] = individual_stat_data[0]["stat_value"]
            else:
                location_stat_dict[stat_location.text_field_name] = global_stat_data["stat_value"]

                
        return location_stat_dict



    

