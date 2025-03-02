from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework.schemas import get_schema_view


urlpatterns = [
    path("gsr/", include("gsr_booking.urls")),
    path("portal/", include("portal.urls")),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("user/", include("user.urls")),
    path("laundry/", include("laundry.urls")),
    path(
        "openapi/",
        get_schema_view(title="Penn Mobile Backend Documentation", public=True),
        name="openapi-schema",
    ),
    path(
        "documentation/",
        TemplateView.as_view(
            template_name="redoc.html", extra_context={"schema_url": "openapi-schema"}
        ),
        name="documentation",
    ),
    path("dining/", include("dining.urls")),
    path("penndata/", include("penndata.urls")),
    path("sublet/", include("sublet.urls")),
    path("market/", include("market.urls")),
    path("wrapped/", include("wrapped.urls")),
]


def universal_identifier_link(request):
    return JsonResponse(
        {
            "applinks": {
                "details": [
                    {
                        "appIDs": [
                            "VU59R57FGM.org.pennlabs.PennMobile",
                            "VU59R57FGM.org.pennlabs.PennMobile.dev",
                        ],
                        "components": [
                            {"/": "ios/gsr/share/*", "?": {"data": "*"}, "comment": "GSR Sharing."}
                        ],
                    }
                ]
            }
        }
    )


urlpatterns = [
    path("api/", include(urlpatterns)),
    path("", include((urlpatterns, "apex"))),
    path(
        ".well-known/apple-app-site-association", universal_identifier_link, name="universal-links"
    ),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
