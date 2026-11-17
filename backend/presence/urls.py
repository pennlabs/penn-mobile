from django.urls import path

from presence.views import HeartbeatView, OptInView, TokenKeyView, TokenView, VenueListView


urlpatterns = [
    path("venues/", VenueListView.as_view(), name="presence-venues"),
    path("opt-in/", OptInView.as_view(), name="presence-opt-in"),
    path("token-key/", TokenKeyView.as_view(), name="presence-token-key"),
    path("token/", TokenView.as_view(), name="presence-token"),
    path("heartbeat/", HeartbeatView.as_view(), name="presence-heartbeat"),
]
