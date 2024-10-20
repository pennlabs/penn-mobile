from django.contrib import admin
from django.core.exceptions import ValidationError

from wrapped.models import GlobalStat, IndividualStat, UserStatKey, StatLocation, Page


class WrappedIndividualAdmin(admin.ModelAdmin):
    search_fields = ["user__username__icontains", "stat_key__stat_key__icontains", "semester__icontains"]
    list_display = ["user", "stat_key", "stat_value", "semester"]


class WrappedGlobalAdmin(admin.ModelAdmin):
    
    list_display = ["stat_key", "stat_value", "semester"]
    search_fields = ["semester__icontains","stat_key__icontains"]


class StatLocationAdmin(admin.ModelAdmin):
    list_display = ["text_field_name", "IndividualStatKey", "GlobalStatKey"]



# admin.site.register(WrappedIndividualAdmin, WrappedGlobalAdmin)
admin.site.register(IndividualStat, WrappedIndividualAdmin)
admin.site.register(GlobalStat, WrappedGlobalAdmin)
admin.site.register(UserStatKey)
admin.site.register(StatLocation, StatLocationAdmin)
# admin.site.register(Page, PageAdmin)
admin.site.register(Page)




