from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from presence.models import PresenceOptIn
from presence.store import ACTIVE_WINDOW_SECONDS, TOKEN_TTL_SECONDS


def current_policy():
    return {
        "version": settings.PRESENCE_PRIVACY_POLICY_VERSION,
        "collection_active": True,
        "description": (
            "Phones report a venue ID and temporary token while present. Raw GPS stays on "
            "the phone. Opt-in and token issuance use your account; heartbeats use only "
            "the token. No token-to-account mapping or visit history is stored. Authenticated "
            "token issuance and rotation can still be correlated by the server. Opting out "
            "stops new token issuance; the app must stop heartbeats and discard its token. "
            "Previously issued tokens remain valid until expiry."
        ),
        "token_ttl_seconds": TOKEN_TTL_SECONDS,
        "active_window_seconds": ACTIVE_WINDOW_SECONDS,
    }


def get_consent(user):
    return PresenceOptIn.objects.filter(user=user).first() or PresenceOptIn(user=user)


@transaction.atomic
def update_consent(user, opted_in, policy_version=""):
    if opted_in and policy_version != settings.PRESENCE_PRIVACY_POLICY_VERSION:
        raise ValidationError({"policy_version": "Accept the current policy version to opt in."})
    # The account row also serializes concurrent first-time grants.
    get_user_model().objects.select_for_update().only("pk").get(pk=user.pk)
    consent = get_consent(user)
    if consent.opted_in != opted_in or (opted_in and consent.policy_version != policy_version):
        consent.opted_in = opted_in
        if opted_in:
            consent.policy_version = policy_version
            consent.consented_at = timezone.now()
        consent.revision += 1
        consent.save()
    user.presence_opt_in = consent
    return consent
