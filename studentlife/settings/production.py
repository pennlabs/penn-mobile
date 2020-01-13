import os

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from studentlife.settings.base import *  # noqa: F401, F403
from studentlife.settings.base import BACKEND_DOMAIN, DATABASES


DEBUG = True

# Fix MySQL Emoji support
DATABASES["default"]["OPTIONS"] = {"charset": "utf8mb4"}

# Honour the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Allow production host headers
ALLOWED_HOSTS = [BACKEND_DOMAIN]

# Make sure SECRET_KEY is set to a secret in production
SECRET_KEY = os.environ.get("SECRET_KEY", None)

# Sentry settings
SENTRY_URL = os.environ.get("SENTRY_URL", "")
sentry_sdk.init(dsn=SENTRY_URL, integrations=[DjangoIntegration()])

# DLA settings
PLATFORM_ACCOUNTS = {
    "REDIRECT_URI": f"https://{BACKEND_DOMAIN}/accounts/callback/",
    "ADMIN_PERMISSION": "studentlife_admin",
}
