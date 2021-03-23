from django.contrib import admin

from dining.models import DiningBalance, DiningTransaction, Venue


admin.site.register(Venue)
admin.site.register(DiningTransaction)
admin.site.register(DiningBalance)
