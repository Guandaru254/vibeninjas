"""
Django settings for DopeEvents project - CSRF PRODUCTION FIX + TEMPLATE DEBUG
Updated with BREVO API (Anymail) Integration
"""

import os
from pathlib import Path
from decouple import config, Csv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-change-in-production')
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='zozaprime.com,www.zozaprime.com,vibeninjas-jbqi.onrender.com,izoza.co.ke,localhost,127.0.0.1',
    cast=Csv()
)

INSTALLED_APPS = [
    'admin_interface',
    'colorfield',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django_summernote',
    'cloudinary_storage',
    'cloudinary',
    'storages',
    'anymail',  # Added for Brevo
    'analytics',
    'blog',
    'events',
    'payments',
    'seller_merchandise',
    'DopeEvents',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'DopeEvents.DopeEvents.urls'

if DEBUG:
    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [BASE_DIR / 'DopeEvents' / 'templates'],
            'APP_DIRS': False,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                    'django.template.context_processors.media',
                ],
                'debug': True,
                'loaders': [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ],
            },
        },
    ]
else:
    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [BASE_DIR / 'DopeEvents' / 'templates'],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                    'django.template.context_processors.media',
                ],
            },
        },
    ]

WSGI_APPLICATION = 'DopeEvents.DopeEvents.wsgi.application'

if config('DATABASE_URL', default=None):
    DATABASES = {
        'default': dj_database_url.config(
            default=config('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'events.User'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': config('CLOUDINARY_CLOUD_NAME', default=''),
    'API_KEY': config('CLOUDINARY_API_KEY', default=''),
    'API_SECRET': config('CLOUDINARY_API_SECRET', default=''),
}

SUMMERNOTE_CONFIG = {
    'summernote': {
        'width': '100%',
        'height': '400',
        'toolbar': [
            ['style', ['style']],
            ['font', ['bold', 'italic', 'underline', 'clear']],
            ['fontname', ['fontname']],
            ['color', ['color']],
            ['para', ['ul', 'ol', 'paragraph']],
            ['table', ['table']],
            ['insert', ['link', 'picture', 'video']],
            ['view', ['fullscreen', 'codeview', 'help']],
        ],
    },
    'attachment_require_authentication': True,
    'disable_attachment': False,
}

# ════════════════════════════════════════════════════════════════════
# M-PESA SETTINGS
# ════════════════════════════════════════════════════════════════════
_mpesa_env = config('MPESA_ENVIRONMENT', default='sandbox')
MPESA_ENVIRONMENT = _mpesa_env

if _mpesa_env == 'production':
    MPESA_BASE_URL = 'https://api.safaricom.co.ke'
else:
    MPESA_BASE_URL = 'https://sandbox.safaricom.co.ke'

MPESA_CONSUMER_KEY = config('MPESA_CONSUMER_KEY', default='')
MPESA_CONSUMER_SECRET = config('MPESA_CONSUMER_SECRET', default='')
MPESA_SHORTCODE = config('MPESA_SHORTCODE', default='')
MPESA_PASSKEY = config('MPESA_PASSKEY', default='')
MPESA_INITIATOR_NAME = config('MPESA_INITIATOR_NAME', default='')
MPESA_SECURITY_CREDENTIAL = config('MPESA_SECURITY_CREDENTIAL', default='')
MPESA_CALLBACK_URL = config('MPESA_CALLBACK_URL', default='https://www.zozaprime.com/payments/mpesa-callback/')

# ════════════════════════════════════════════════════════════════════
# PAYSTACK SETTINGS
# ════════════════════════════════════════════════════════════════════
PAYSTACK_PUBLIC_KEY = config('PAYSTACK_PUBLIC_KEY', default='')
PAYSTACK_SECRET_KEY = config('PAYSTACK_SECRET_KEY', default='')
PAYSTACK_WEBHOOK_SECRET = config('PAYSTACK_WEBHOOK_SECRET', default='')
CARDS_ENABLED = config('CARDS_ENABLED', default=False, cast=bool)

# ════════════════════════════════════════════════════════════════════
# BREVO EMAIL (via ANYMAIL)
# ════════════════════════════════════════════════════════════════════
# Using Anymail to leverage Brevo's API for better deliverability
ANYMAIL = {
    "BREVO_API_KEY": config('BREVO_API_KEY', default=''),
}
EMAIL_BACKEND = "anymail.backends.brevo.EmailBackend"
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='ZOZAPRIME <tickets@zozaprime.com>')

# ════════════════════════════════════════════════════════════════════
# PRODUCTION SECURITY SETTINGS
# ════════════════════════════════════════════════════════════════════
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = False 
    CSRF_COOKIE_SAMESITE = 'Lax'

    CSRF_TRUSTED_ORIGINS = [
        'https://www.zozaprime.com',
        'https://zozaprime.com',
        'https://vibeninjas-jbqi.onrender.com',
        'https://izoza.co.ke',
    ]

    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'SAMEORIGIN'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    CSRF_COOKIE_SECURE = False
    CSRF_COOKIE_HTTPONLY = False
    CSRF_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False

# ════════════════════════════════════════════════════════════════════
# LOGGING
# ════════════════════════════════════════════════════════════════════
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'payments': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

SILENCED_SYSTEM_CHECKS = ['security.W019']

# ════════════════════════════════════════════════════════════════════
# SITE / PLATFORM
# ════════════════════════════════════════════════════════════════════
SITE_NAME = 'ZOZAPRIME'
SITE_URL = config('SITE_URL', default='https://www.zozaprime.com')
PLATFORM_FEE_PERCENTAGE = config('PLATFORM_FEE_PERCENTAGE', default=7.0, cast=float)
FOUNDING_FAN_FEE_PERCENTAGE = config('FOUNDING_FAN_FEE_PERCENTAGE', default=0.0, cast=float)

# ════════════════════════════════════════════════════════════════════
# WHITENOISE / UPLOADS
# ════════════════════════════════════════════════════════════════════
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = DEBUG
WHITENOISE_MANIFEST_STRICT = False

FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880
PAGINATE_BY = 20