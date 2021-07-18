"""
Django settings for studentlife.

Generated by 'django-admin startproject' using Django 2.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os

import dj_database_url


DOMAIN = os.environ.get("DOMAIN", "example.com")

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
    "django.contrib.admin",
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
    "django_filters",
    "debug_toolbar",
    "gsr_booking",
    "legacy",
    "options.apps.OptionsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "accounts.middleware.OAuth2TokenMiddleware",
]

ROOT_URLCONF = "studentlife.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["studentlife/templates"],
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

WSGI_APPLICATION = "studentlife.wsgi.application"


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

LEGACY_DATABASE_URL = os.environ.get(
    "LEGACY_DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "db.sqlite3")
)

DATABASES = {
    "default": dj_database_url.config(default="sqlite:///" + os.path.join(BASE_DIR, "db.sqlite3")),
    "legacy": dj_database_url.parse(LEGACY_DATABASE_URL),
}

DATABASE_ROUTERS = ["studentlife.dbrouters.LegacyRouter"]


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

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")


# DLA Settings

PLATFORM_ACCOUNTS = {
    "REDIRECT_URI": os.environ.get("LABS_REDIRECT_URI", "http://localhost:8000/accounts/callback/"),
    "CLIENT_ID": "clientid",
    "CLIENT_SECRET": "supersecretclientsecret",
    "PLATFORM_URL": "https://platform-dev.pennlabs.org",
    "CUSTOM_ADMIN": False,
}

# Laundry API URL
LAUNDRY_URL = os.environ.get("LAUNDRY_URL", "http://suds.kite.upenn.edu")

# Dining API Credentials
DINING_USERNAME = os.environ.get("DINING_USERNAME", None)
DINING_PASSWORD = os.environ.get("DINING_PASSWORD", None)

# LIBCAL_ID = os.environ.get("LIBCAL_ID", None)
# LIBCAL_SECRET = os.environ.get("LIBCAL_SECRET", None)
# WHARTON_TOKEN = os.environ.get("WHARTON_TOKEN", None)
LIBCAL_ID = "194"
LIBCAL_SECRET = "***REMOVED***"
WHARTON_TOKEN = "***REMOVED***"
