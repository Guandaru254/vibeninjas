import os
import dj_database_url
from pathlib import Path
from decouple import config

# ─── PATH SETUP ───────────────────────────────────────────────────────────────
# settings.py lives at:  vibeninjas/DopeEvents/DopeEvents/settings.py
# BASE_DIR resolves to:  vibeninjas/DopeEvents/
BASE_DIR = Path(__file__).resolve().parent.parent

# ─── SECURITY ─────────────────────────────────────────────────────────────────
SECRET_KEY = config('SECRET_KEY', default='django-insecure-local-key-for-dev-only')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='127.0.0.1,localhost,.onrender.com'
).split(',')

# ─── APPS ─────────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.humanize',
    'cloudinary_storage',          # Must be above staticfiles
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
# • Locally:     falls back to SQLite if DATABASE_URL is not set in .env
# • On Render:   uses the DATABASE_URL environment variable you set in the dashboard
#
# IMPORTANT — Supabase URL must use port 6543 (Transaction Pooler), NOT 5432.
# Get it from: Supabase Dashboard → Connect → Connection String
#              → Type: URI  |  Source: Session Pooler  |  Method: Transaction Pooler
# It looks like:
#   postgresql://postgres.PROJECTREF:PASSWORD@aws-0-eu-central-1.pooler.supabase.com:6543/postgres

_db_url = config('DATABASE_URL', default='sqlite:///db.sqlite3')

DATABASES = {
    'default': dj_database_url.config(
        default=_db_url,
        conn_max_age=600,
    )
}

# Add SSL only for PostgreSQL connections (Supabase requires it)
if DATABASES['default']['ENGINE'] != 'django.db.backends.sqlite3':
    DATABASES['default'].setdefault('OPTIONS', {})['sslmode'] = 'require'

# ─── STATIC & MEDIA FILES ─────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Your static folder is at  vibeninjas/DopeEvents/static/
# BASE_DIR is               vibeninjas/DopeEvents/
# So BASE_DIR / 'static' is the correct path ✓
_static_dir = BASE_DIR / 'static'
STATICFILES_DIRS = [_static_dir] if _static_dir.exists() else []

# Do NOT use WhiteNoise's CompressedStaticFilesStorage or
# CompressedManifestStaticFilesStorage — both cause FileNotFoundError
# on Render during collectstatic due to a race condition in their
# compression worker threads. WhiteNoise middleware still serves
# static files correctly without a custom STATICFILES_STORAGE.

# ─── CLOUDINARY ───────────────────────────────────────────────────────────────
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': config('CLOUDINARY_CLOUD_NAME', default=''),
    'API_KEY':    config('CLOUDINARY_API_KEY',    default=''),
    'API_SECRET': config('CLOUDINARY_API_SECRET', default=''),
}
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# ─── PRODUCTION SECURITY ──────────────────────────────────────────────────────
if not DEBUG:
    CSRF_TRUSTED_ORIGINS = [
        f"https://{o.strip()}"
        for o in config('CSRF_TRUSTED_ORIGINS', default='').split(',')
        if o.strip()
    ]
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT     = True
    SESSION_COOKIE_SECURE   = True
    CSRF_COOKIE_SECURE      = True

# ─── EMAIL ────────────────────────────────────────────────────────────────────
EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = config('EMAIL_HOST',          default='smtp.gmail.com')
EMAIL_PORT          = config('EMAIL_PORT',          default=587, cast=int)
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = config('EMAIL_HOST_USER',     default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL  = config('DEFAULT_FROM_EMAIL',  default='noreply@vibeninjas.com')

# ─── PAYMENTS & INTEGRATIONS ──────────────────────────────────────────────────
MPESA_CONSUMER_KEY    = config('CONSUMER_KEY',    default='')
MPESA_CONSUMER_SECRET = config('CONSUMER_SECRET', default='')
MPESA_SHORTCODE       = config('SHORTCODE',       default='')
MPESA_PASSKEY         = config('PASSKEY',         default='')
MPESA_BASE_URL        = config('BASE_URL',        default='https://api.safaricom.co.ke')
MPESA_CALLBACK_URL    = config('CALLBACK_URL',    default='')

STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_SECRET_KEY      = config('STRIPE_SECRET_KEY',      default='')

TWILIO_ACCOUNT_SID  = config('TWILIO_ACCOUNT_SID',  default='')
TWILIO_AUTH_TOKEN   = config('TWILIO_AUTH_TOKEN',   default='')
TWILIO_PHONE_NUMBER = config('TWILIO_PHONE_NUMBER', default='')

# ─── AUTH ─────────────────────────────────────────────────────────────────────
LOGIN_URL           = '/login/'
LOGIN_REDIRECT_URL  = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'
AUTH_USER_MODEL     = 'events.User'

# ─── MISC ─────────────────────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'