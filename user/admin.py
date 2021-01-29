from django.contrib import admin

from user.models import NotificationToken, Profile, Degree

admin.site.register(NotificationToken)
admin.site.register(Profile)
admin.site.register(Degree)

