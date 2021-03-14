from django.contrib import admin

from dining.models import DiningBalance, DiningPreference, DiningTransaction, Venue


admin.site.register(Venue)
admin.site.register(DiningPreference)
admin.site.register(DiningTransaction)
admin.site.register(DiningBalance)
