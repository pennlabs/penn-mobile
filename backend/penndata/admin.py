from django.contrib import admin
from django.utils.html import escape, mark_safe

from penndata.models import AnalyticsEvent, Event, FitnessRoom, FitnessSnapshot, HomePageOrder


# custom fitness room admin
class FitnessRoomAdmin(admin.ModelAdmin):
    def image_tag(self, instance):
        return mark_safe('<img src="%s" height="300" />' % escape(instance.image_url))

    image_tag.short_description = "Image"
    image_tag.allow_tags = True
    readonly_fields = ("image_tag",)


admin.site.register(Event)
admin.site.register(HomePageOrder)
admin.site.register(FitnessRoom, FitnessRoomAdmin)
admin.site.register(FitnessSnapshot)
admin.site.register(AnalyticsEvent)
