from django.contrib import admin

from penndata.models import AnalyticsEvent, Event, FitnessRoom, FitnessSnapshot, HomePageOrder


admin.site.register(Event)
admin.site.register(HomePageOrder)
admin.site.register(FitnessRoom)
admin.site.register(FitnessSnapshot)
admin.site.register(AnalyticsEvent)
