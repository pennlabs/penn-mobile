from django.contrib import admin

from user.models import NotificationSetting, NotificationToken, Profile


admin.site.register(NotificationToken)
admin.site.register(NotificationSetting)
admin.site.register(Profile)
