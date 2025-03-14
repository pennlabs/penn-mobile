"""
Django settings for pennmobile.
Generated by 'django-admin startproject' using Django 2.1.2.
For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/
For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os

import dj_database_url


DOMAINS = os.environ.get("DOMAINS", "example.com").split(",")

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY", "o7ql0!vuk0%rgrh9p2bihq#pege$qqlm@zo#8&t==%&za33m*2")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    "pennmobile.admin.PennMobileAdminConfig",  # "replaces django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "user.apps.UserConfig",
    "dining.apps.DiningConfig",
    "laundry.apps.LaundryConfig",
    "penndata.apps.PenndataConfig",
    "accounts.apps.AccountsConfig",
    "identity.apps.IdentityConfig",
    "analytics.apps.AnalyticsConfig",
    "wrapped.apps.WrappedConfig",
    "django_filters",
    "debug_toolbar",
    "gsr_booking",
    "portal",
    "options.apps.OptionsConfig",
    "sublet",
    "phonenumber_field",
    "market",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "pennmobile.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["pennmobile/templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "pennmobile.wsgi.application"


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases
DATABASES = {
    "default": dj_database_url.config(default="sqlite:///" + os.path.join(BASE_DIR, "db.sqlite3")),
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Authentication Backends

AUTHENTICATION_BACKENDS = [
    "accounts.backends.LabsUserBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "America/New_York"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = "/assets/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")


# DLA Settings

PLATFORM_ACCOUNTS = {
    "REDIRECT_URI": os.environ.get("LABS_REDIRECT_URI", "http://localhost:8000/accounts/callback/"),
    "CLIENT_ID": os.environ.get("CLIENT_ID", "clientid"),
    "CLIENT_SECRET": os.environ.get("CLIENT_SECRET", "supersecretclientsecret"),
    "PLATFORM_URL": os.environ.get("PLATFORM_URL", "https://platform.pennlabs.org"),
    "CUSTOM_ADMIN": False,
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
        "accounts.authentication.PlatformAuthentication",
    ],
}

# Redis for Celery & Caching
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/1")

# Celery Settings (read automatically by celery.py)
CELERY_BROKER_URL = REDIS_URL
CELERY_TIMEZONE = TIME_ZONE

# Laundry API URL
# LAUNDRY_URL = os.environ.get("LAUNDRY_URL", "http://suds.kite.upenn.edu")
LAUNDRY_URL = "https://api.alliancelslabs.com"
LAUNDRY_X_API_KEY = os.environ.get("LAUNDRY_X_API_KEY", None)
LAUNDRY_ALLIANCELS_API_KEY = os.environ.get("LAUNDRY_ALLIANCE_LS_KEY", None)
LAUNDRY_HEADERS = {
    "x-api-key": LAUNDRY_X_API_KEY,
    "alliancels-auth-token": LAUNDRY_ALLIANCELS_API_KEY,
}

# Dining API Credentials
DINING_USERNAME = os.environ.get("DINING_USERNAME", None)
DINING_PASSWORD = os.environ.get("DINING_PASSWORD", None)
DINING_ID = os.environ.get("DINING_ID", None)
DINING_SECRET = os.environ.get("DINING_SECRET", None)

LIBCAL_ID = os.environ.get("LIBCAL_ID", None)
LIBCAL_SECRET = os.environ.get("LIBCAL_SECRET", None)
WHARTON_TOKEN = os.environ.get("WHARTON_TOKEN", None)

# Upload file storage
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", None)
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", None)
AWS_STORAGE_BUCKET_NAME = "penn.mobile.portal"
AWS_QUERYSTRING_AUTH = False
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = "public-read"

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("SMTP_HOST", "")
EMAIL_USE_TLS = True
EMAIL_PORT = os.environ.get("SMTP_PORT", 587)
EMAIL_HOST_USER = os.environ.get("SMTP_USERNAME", "")
EMAIL_HOST_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get("SMTP_FROM_EMAIL", EMAIL_HOST_USER)
