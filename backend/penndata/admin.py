from django.contrib import admin

from penndata.models import AnalyticsEvent, Event, HomePageOrder


admin.site.register(Event)
admin.site.register(HomePageOrder)
admin.site.register(AnalyticsEvent)
