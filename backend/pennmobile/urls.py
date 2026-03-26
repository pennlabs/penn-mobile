from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


urlpatterns = [
    path("gsr/", include("gsr_booking.urls")),
    path("portal/", include("portal.urls")),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("user/", include("user.urls")),
    path("laundry/", include("laundry.urls")),
    path("openapi/", SpectacularAPIView.as_view(), name="openapi-schema"),
    path(
        "documentation/",
        SpectacularSwaggerView.as_view(url_name="openapi-schema"),
        name="documentation",
    ),
    path("redoc/", SpectacularRedocView.as_view(url_name="openapi-schema"), name="redoc"),
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
                            {"/": "/gsr/share/*", "?": {"data": "*"}, "comment": "GSR Sharing."}
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
