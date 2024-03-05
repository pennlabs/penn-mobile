from django.contrib import admin

from gsr_booking.models import GSR, Group, GroupMembership, GSRBooking, Reservation


class GroupMembershipAdmin(admin.ModelAdmin):
    search_fields = ["user__username__icontains", "group__name__icontains"]


class GSRAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        return GSR.all_objects.all()

    list_display = ["name", "kind", "lid", "gid", "in_use"]
    search_fields = ["name", "lid", "gid"]
    ordering = ["-in_use"]


admin.site.register(Group)
admin.site.register(GroupMembership, GroupMembershipAdmin)
admin.site.register(GSR, GSRAdmin)
admin.site.register(GSRBooking)
admin.site.register(Reservation)
