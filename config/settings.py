"""
Loyiha sozlamalari.

Hamma o'zgaruvchan qiymatlar (parollar, hostlar, S3) environment'dan olinadi.
Shuning uchun bitta settings fayli lokalda ham, serverda ham ishlaydi —
farq faqat .env faylida.
"""

import os
import sys
from pathlib import Path

from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent


def env(name, default=""):
    return os.environ.get(name, default)


def env_bool(name, default=False):
    return env(name, str(default)).lower() in ("1", "true", "yes", "on")


def env_list(name, default=""):
    return [item.strip() for item in env(name, default).split(",") if item.strip()]


# .env faylini o'qiymiz (agar bor bo'lsa). Alohida kutubxona shart emas,
# format oddiy: KALIT=qiymat. Mavjud environment qiymatlari ustun turadi.
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


DEBUG = env_bool("DEBUG")
TESTING = len(sys.argv) > 1 and sys.argv[1] == "test"
SECRET_KEY = env("SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-only-secret-key"
    else:
        raise RuntimeError("SECRET_KEY berilmagan")

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.postgres",
    "apps.core",
    "apps.accounts",
    "apps.landing",
    "apps.panel",
    "apps.warehouses",
    "apps.catalog",
    "apps.inventory",
    "apps.operations",
    "apps.reports",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.CompanyMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", "wms"),
        "USER": env("DB_USER", "postgres"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST", "localhost"),
        "PORT": env("DB_PORT", "5432"),
        # Ulanishni har so'rovda yangidan ochmaslik uchun — RDS bilan sezilarli tezroq
        "CONN_MAX_AGE": 60,
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {"sslmode": env("DB_SSLMODE", "prefer")},
    }
}

AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:after_login"
LOGOUT_REDIRECT_URL = "landing:home"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Sessiyalar bazada saqlanadi. Bir nechta web replika bo'lganda foydalanuvchining
# so'rovi qaysi replikaga tushishidan qat'i nazar, sessiya topiladi.
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 60 * 60 * 12

LANGUAGE_CODE = "uz"
LANGUAGES = [("uz", _("O'zbekcha")), ("ru", _("Русский"))]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

USE_S3 = env_bool("USE_S3")
AWS_S3_BUCKET = env("AWS_S3_BUCKET")
AWS_REGION = env("AWS_REGION", "eu-central-1")

STORAGES = {
    "default": {
        "BACKEND": (
            "apps.core.storage.S3Storage"
            if USE_S3
            else "django.core.files.storage.FileSystemStorage"
        ),
    },
    "staticfiles": {
        # Production'da fayl nomiga hash qo'shiladi (app.3f9a1c.css) — brauzer keshi
        # yangi versiyani darhol oladi. Lokalda va testlarda bunga ehtiyoj yo'q.
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG or TESTING
            else "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
        ),
    },
}

# Yuklanadigan fayl chegarasi (rasm va hujjatlar uchun yetarli)
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Landing va sayt ma'lumotlari — bir joydan boshqariladi
SITE_NAME = env("SITE_NAME", "OmborHub")
CONTACT_PHONE = env("CONTACT_PHONE")
CONTACT_EMAIL = env("CONTACT_EMAIL")

# Bitta IP dan bir soatda nechta ariza qabul qilinadi
LEAD_LIMIT_PER_HOUR = 5

# Xavfsizlik: Nginx HTTPS ni o'zi qabul qiladi va Django'ga X-Forwarded-Proto beradi
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = env_bool("SECURE_COOKIES")
CSRF_COOKIE_SECURE = env_bool("SECURE_COOKIES")
SESSION_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"},
    },
    "handlers": {
        # Konteynerda stdout ga yozamiz — Docker uni CloudWatch Logs ga yuboradi
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}
