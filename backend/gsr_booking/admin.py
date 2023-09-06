from django.contrib import admin

from gsr_booking.models import GSR, Group, GroupMembership, GSRBooking, Reservation


class GroupMembershipAdmin(admin.ModelAdmin):
    search_fields = ["user__username__icontains", "group__name__icontains"]


admin.site.register(Group)
admin.site.register(GroupMembership, GroupMembershipAdmin)
admin.site.register(GSR)
admin.site.register(GSRBooking)
admin.site.register(Reservation)
