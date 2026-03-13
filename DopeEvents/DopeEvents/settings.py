import os
import dj_database_url
from pathlib import Path
from decouple import config

# ─── PATH SETUP ───────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ─── SECURITY ─────────────────────────────────────────────────────────────────
# Added a default for SECRET_KEY to prevent startup crashes
SECRET_KEY = config('SECRET_KEY', default='django-insecure-fallback-key-for-dev')
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS', 
    default='izoza.co.ke,www.izoza.co.ke,.izoza.co.ke,vibeninjas-jbqi.onrender.com'
).split(',')

# ─── APPS ─────────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.humanize',
    'cloudinary_storage',          
    'django.contrib.staticfiles',
    'cloudinary',
    'events',
    'payments',
    'analytics',
    'seller_merchandise',
]

# ─── MIDDLEWARE ────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'analytics.middleware.VisitorTrackingMiddleware',
]

ROOT_URLCONF = 'DopeEvents.DopeEvents.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.static',
            ],
        },
    },
]

WSGI_APPLICATION = 'DopeEvents.DopeEvents.wsgi.application'

# ─── DATABASE ─────────────────────────────────────────────────────────────────
_db_url = config('DATABASE_URL', default='sqlite:///db.sqlite3')

DATABASES = {
    'default': dj_database_url.config(
        default=_db_url,
        conn_max_age=600,
    )
}

if DATABASES['default']['ENGINE'] != 'django.db.backends.sqlite3':
    DATABASES['default'].setdefault('OPTIONS', {})['sslmode'] = 'require'

# ─── STATIC & MEDIA FILES ─────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
_static_dir = BASE_DIR / 'static'
STATICFILES_DIRS = [_static_dir] if _static_dir.exists() else []

# ─── CLOUDINARY (CRASH-PROOFED) ───────────────────────────────────────────────
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': config('CLOUDINARY_CLOUD_NAME', default=''),
    'API_KEY':    config('CLOUDINARY_API_KEY',    default=''),
    'API_SECRET': config('CLOUDINARY_API_SECRET', default=''),
}
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# ─── PRODUCTION SECURITY (ENFORCED) ──────────────────────────────────────────
if not DEBUG:
    CSRF_TRUSTED_ORIGINS = [
        "https://izoza.co.ke",
        "https://www.izoza.co.ke",
        "https://*.izoza.co.ke",
        "https://vibeninjas-jbqi.onrender.com"
    ]
    
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT     = True
    SESSION_COOKIE_SECURE   = True
    CSRF_COOKIE_SECURE      = True
    
    SECURE_HSTS_SECONDS = 31536000 
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ─── EMAIL (CRASH-PROOFED) ────────────────────────────────────────────────────
EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = config('EMAIL_HOST',          default='smtp.gmail.com')
EMAIL_PORT          = config('EMAIL_PORT',          default=587, cast=int)
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = config('EMAIL_HOST_USER',     default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL  = config('DEFAULT_FROM_EMAIL',  default='noreply@izoza.co.ke')

# ─── PAYMENTS (MPESA PRODUCTION - CRASH-PROOFED) ──────────────────────────────
MPESA_CONSUMER_KEY    = config('CONSUMER_KEY',    default='')
MPESA_CONSUMER_SECRET = config('CONSUMER_SECRET', default='')
MPESA_SHORTCODE       = config('SHORTCODE',       default='')
MPESA_PASSKEY         = config('PASSKEY',         default='')
MPESA_BASE_URL        = config('BASE_URL',        default='https://api.safaricom.co.ke')
MPESA_CALLBACK_URL    = config('CALLBACK_URL',    default='')

# settings.py
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='sk_test_dummy')
STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY', default='pk_test_dummy')

# ─── AUTH ─────────────────────────────────────────────────────────────────────
LOGIN_URL           = '/login/'
LOGIN_REDIRECT_URL  = '/home/'
LOGOUT_REDIRECT_URL = '/'
AUTH_USER_MODEL     = 'events.User'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'