import os
from pathlib import Path

import stripe
from decouple import config
from django.core.exceptions import ImproperlyConfigured
import dj_database_url


# ====== BASE PROJECT PATH ======
BASE_DIR = Path(__file__).resolve().parent.parent


def config_bool(name, default=False):
    value = config(name, default=str(default))
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "f", "no", "n", "off", "prod", "production", "release"}:
        return False
    raise ImproperlyConfigured(f"{name} must be a boolean value.")


# ====== STRIPE CONFIGURATION ======
STRIPE_PUBLISHABLE_KEY = config("STRIPE_PUBLISHABLE_KEY", default="")
STRIPE_SECRET_KEY = config("STRIPE_SECRET_KEY", default="")
STRIPE_WEBHOOK_SECRET = config("STRIPE_WEBHOOK_SECRET", default="")

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY



# ====== AUTH / LOGIN SETTINGS ======
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "home"
LOGIN_URL = "login"


# ====== CORE DJANGO SECURITY ======
DEBUG = config_bool("DEBUG", default=False)

SECRET_KEY = config("SECRET_KEY", default="")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "django-insecure-local-development-key"
    else:
        raise ImproperlyConfigured("SECRET_KEY must be set when DEBUG=False.")

ALLOWED_HOSTS = [
    host.strip()
    for host in config("ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",")
    if host.strip()
]
if not DEBUG and not ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS must be set when DEBUG=False.")

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in config("CSRF_TRUSTED_ORIGINS", default="").split(",")
    if origin.strip()
]


# ====== INSTALLED APPS ======
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Project apps
    "store",
    "cart",
    "transaction",
    "vendors",
    "reviews",
    "coupons",
    "users",

    # Third-party
    "widget_tweaks",
    "anymail",
    "django.contrib.humanize",
]


# ====== EMAIL (MAILGUN) ======
EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
ANYMAIL = {
    "MAILGUN_API_KEY": config("MAILGUN_API_KEY", default=""),
    "MAILGUN_SENDER_DOMAIN": config("MAILGUN_SENDER_DOMAIN", default=""),
}

DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="LIBRA Store <noreply@example.com>")
SERVER_EMAIL = DEFAULT_FROM_EMAIL


# ====== CUSTOM USER MODEL ======
AUTH_USER_MODEL = "users.CustomUser"


# ====== MIDDLEWARE ======
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    # Custom
    "cart.middleware.NoCacheMiddleware",
    "librashop.middleware.RequestLoggingMiddleware",
]


# ====== TEMPLATES ======
ROOT_URLCONF = "librashop.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "store.context_processors.cart_wishlist_counts",
            ],
        },
    },
]

WSGI_APPLICATION = "librashop.wsgi.application"


# ====== DATABASE CONFIG ======
DATABASE_URL = config("DATABASE_URL", default="")
if not DATABASE_URL and not DEBUG:
    raise ImproperlyConfigured("DATABASE_URL must be set when DEBUG=False.")

DATABASES = {
    "default": dj_database_url.config(
        default=DATABASE_URL or f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=config("DATABASE_CONN_MAX_AGE", default=600, cast=int),
        ssl_require=config_bool("DATABASE_SSL_REQUIRE", default=not DEBUG),
    )
}

# ====== PASSWORD VALIDATORS ======
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]



# ====== INTERNATIONALIZATION ======
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True



# ====== STATIC & MEDIA FILES ======
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"



# ====== LOGGING ======

LOG_TO_FILE = config_bool("LOG_TO_FILE", default=DEBUG)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} {module} {message}", "style": "{"},
        "simple": {"format": "{levelname} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": config("DJANGO_LOG_LEVEL", default="INFO"),
            "propagate": False,
        },
    },
}

if LOG_TO_FILE:
    LOGS_DIR = BASE_DIR / "logs"
    LOGS_DIR.mkdir(exist_ok=True)
    LOGGING["handlers"]["file"] = {
        "class": "logging.FileHandler",
        "filename": LOGS_DIR / "django.log",
        "formatter": "verbose",
    }
    LOGGING["root"]["handlers"].append("file")
    LOGGING["loggers"]["django"]["handlers"].append("file")



# ====== CSRF / SECURITY SETTINGS ======

CSRF_COOKIE_NAME = "csrftoken"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_USE_SESSIONS = False
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"

if not DEBUG:
    SECURE_SSL_REDIRECT = config_bool("SECURE_SSL_REDIRECT", default=True)
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=31536000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = config_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True)
    SECURE_HSTS_PRELOAD = config_bool("SECURE_HSTS_PRELOAD", default=True)
else:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False



# ====== CUSTOM HOMEPAGE IMAGES ======
HOME_HERO_IMAGES = [
    "images/banners/heroban.png",
    "images/banners/heroban2.png",
    "images/banners/heroban3.png",
]
