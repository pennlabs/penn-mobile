import os

import sentry_sdk
from sentry_sdk import Event, Hint
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration

from pennmobile.settings.base import *  # noqa: F401, F403
from pennmobile.settings.base import DOMAINS, REDIS_URL


DEBUG = False

# Honour the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Allow production host headers
ALLOWED_HOSTS = DOMAINS

# Make sure SECRET_KEY is set to a secret in production
SECRET_KEY = os.environ.get("SECRET_KEY", None)

# Sentry settings
SENTRY_URL = os.environ.get("SENTRY_URL", "")


def before_send(event: Event, hint: Hint) -> Event | None:
    if (
        "logentry" in event
        and "message" in event["logentry"]
        and "Wharton: Error 403 when reserving data" in event["logentry"]["message"]
    ):
        return None
    return event


sentry_sdk.init(
    dsn=SENTRY_URL,
    integrations=[CeleryIntegration(), DjangoIntegration()],
    before_send=before_send,
)

# DLA settings
PLATFORM_ACCOUNTS = {"ADMIN_PERMISSION": "penn_mobile_admin"}

# Cache settings
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}
