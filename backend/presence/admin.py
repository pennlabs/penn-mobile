from django import forms
from django.contrib import admin
from django.db.models import F

from presence.models import PresenceOptIn, Venue


class VenueForm(forms.ModelForm):
    class Meta:
        model = Venue
        fields = "__all__"

    def clean(self):
        data = super().clean()
        if data.get("fitness_rooms") and data.get("kind") != Venue.Kind.GYM:
            self.add_error("fitness_rooms", "Only gyms can link fitness rooms.")
        return data


class VenueAdmin(admin.ModelAdmin):
    form = VenueForm
    list_display = ("name", "venue_id", "kind", "enabled", "configuration_version")
    list_filter = ("kind", "enabled")
    search_fields = ("name", "venue_id")
    filter_horizontal = ("fitness_rooms",)

    def get_readonly_fields(self, request, obj=None):
        return ("configuration_version", "venue_id") if obj else ("configuration_version",)

    def save_model(self, request, obj, form, change):
        if change and form.changed_data:
            obj.configuration_version = F("configuration_version") + 1
        super().save_model(request, obj, form, change)
        if change:
            obj.refresh_from_db(fields=["configuration_version"])


class PresenceOptInAdmin(admin.ModelAdmin):
    list_display = ("user", "opted_in", "policy_version", "revision", "updated_at")
    list_filter = ("opted_in", "policy_version")
    search_fields = ("user__username",)
    readonly_fields = ("updated_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Venue, VenueAdmin)
admin.site.register(PresenceOptIn, PresenceOptInAdmin)
