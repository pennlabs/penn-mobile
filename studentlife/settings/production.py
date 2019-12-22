import os

# import sentry_sdk
# from sentry_sdk.integrations.django import DjangoIntegration

from studentlife.settings.base import *  # noqa


DEBUG = True

# Fix MySQL Emoji support
DATABASES = {
    'default': dj_database_url.config(default='mysql://gsr:QSJcCI4kt9EiVBTT@sql.pennlabs.org:3306/gsr')
}
DATABASES['default']['OPTIONS'] = {'charset': 'utf8mb4'}

# Honour the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Allow production host headers
ALLOWED_HOSTS = ['localhost', '127.0.0.1', BACKEND_DOMAIN]

SENTRY_URL = os.environ.get('SENTRY_URL', '')

# sentry_sdk.init(
#     dsn=SENTRY_URL,
#     integrations=[DjangoIntegration()]
# )

###############################################################
# SETTINGS TO ALLOW FRONTEND TO MAKE AJAX REQUESTS TO BACKEND #
###############################################################
# DO NOT USE IF DJANGO APP IS STANDALONE
# Django CORS Settings
CORS_ORIGIN_WHITELIST = [
    'https://www.{}'.format(FRONTEND_DOMAIN),
    'https://{}'.format(FRONTEND_DOMAIN),
]

CSRF_TRUSTED_ORIGINS = [
    '.' + FRONTEND_DOMAIN,
    FRONTEND_DOMAIN,
]
