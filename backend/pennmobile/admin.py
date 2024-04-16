# CUSTOM ADMIN SETTUP FOR PENN MOBILE
from django.contrib import admin, messages
from django.contrib.admin.apps import AdminConfig
from django.urls import reverse
from django.utils.html import format_html


def add_post_poll_message(request, model):
    if (count := model.objects.filter(model.ACTION_REQUIRED_CONDITION).count()) > 0:
        link = reverse(f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist")
        messages.info(
            request,
            format_html(
                f"Action Required: There {'is' if count == 1 else 'are'} {count} "
                + f"<a href='{link}'>{model._meta.verbose_name_plural}</a> "
                + "that need to be reviewed."
            ),
        )


class CustomAdminSite(admin.AdminSite):
    site_header = "Penn Mobile Backend Admin"

    def index(self, request, extra_context=None):
        from portal.models import Poll, Post

        add_post_poll_message(request, Post)
        add_post_poll_message(request, Poll)

        return super().index(request, extra_context)


class PennMobileAdminConfig(AdminConfig):
    default_site = "pennmobile.admin.CustomAdminSite"
