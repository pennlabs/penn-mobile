from django.contrib import admin
from django.utils.safestring import SafeText, mark_safe

from sublet.models import Amenity, Offer, Sublet, SubletImage


class SubletAdmin(admin.ModelAdmin):
    def image_tag(self, instance: Sublet) -> SafeText:
        # type: ignore[attr-defined]
        images = ['<img src="%s" height="150" />' for image in instance.images.all()]
        return mark_safe("<br>".join(images))

    image_tag.short_description = "Sublet Images"  # type: ignore[attr-defined]
    readonly_fields = ("image_tag",)


admin.site.register(Offer)
admin.site.register(Amenity)
admin.site.register(Sublet, SubletAdmin)
admin.site.register(SubletImage)
