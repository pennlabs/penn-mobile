from django.contrib import admin

from user.models import IOSNotificationToken, AndroidNotificationToken, NotificationService, Profile

# custom IOSNotificationToken admin
class IOSNotificationTokenAdmin(admin.ModelAdmin):
    list_display = ('token', 'user', 'is_dev')

admin.site.register(IOSNotificationToken, IOSNotificationTokenAdmin)
admin.site.register(AndroidNotificationToken)
admin.site.register(NotificationService)
admin.site.register(Profile)
