from django import forms
from django.contrib import admin
from django.db.models import F

from presence.models import PresenceOptIn, Venue, linked_dining_venue


class VenueForm(forms.ModelForm):
    class Meta:
        model = Venue
        fields = "__all__"

    def clean(self):
        data = super().clean()
        if not self.instance._state.adding:
            kind = data.get("kind")
            if kind != Venue.Kind.GYM and self.instance.fitness_rooms.exists():
                self.add_error("kind", "Unlink this venue's fitness rooms before changing kind.")
            if kind != Venue.Kind.DINING and linked_dining_venue(self.instance) is not None:
                self.add_error("kind", "Unlink this venue's dining venue before changing kind.")
        return data


class VenueAdmin(admin.ModelAdmin):
    form = VenueForm
    list_display = ("name", "venue_id", "kind", "enabled", "configuration_version")
    list_filter = ("kind", "enabled")
    search_fields = ("name", "venue_id")

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
