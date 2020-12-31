from django.contrib import admin

from user.models import DiningPreference, LaundryPreference, NotificationToken, Profile


admin.site.register(NotificationToken)
admin.site.register(LaundryPreference)
admin.site.register(DiningPreference)
admin.site.register(Profile)
