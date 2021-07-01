from django.contrib import admin

from user.models import Degree, NotificationSetting, NotificationToken, Profile


admin.site.register(NotificationToken)
admin.site.register(Profile)
admin.site.register(Degree)
admin.site.register(NotificationSetting)
