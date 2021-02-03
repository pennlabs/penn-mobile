from django.contrib import admin

from user.models import Degree, NotificationToken, Profile


admin.site.register(NotificationToken)
admin.site.register(Profile)
admin.site.register(Degree)
