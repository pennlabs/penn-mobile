import os

from pennmobile.settings.base import *  # noqa: F401, F403
from pennmobile.settings.base import INSTALLED_APPS, MIDDLEWARE


# Override default Django Test Runner to include test suite-wide Mock Patch
TEST_RUNNER = "pennmobile.test_runner.MobileTestLocalRunner"

# Development extensions
INSTALLED_APPS += ["django_extensions"]

MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE
INTERNAL_IPS = ["127.0.0.1"]

CSRF_TRUSTED_ORIGINS = ["http://localhost:3000"]

# Allow http callback for DLA
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
