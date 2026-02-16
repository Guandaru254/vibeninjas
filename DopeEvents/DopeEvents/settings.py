import os
import dj_database_url
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- SECURITY ---
# In development, this can be in your .env. In production (Render), set it in the Dashboard.
SECRET_KEY = config('SECRET_KEY', default='django-insecure-local-key-for-dev')

# DEBUG should be True locally and False on Render
DEBUG = config('DEBUG', default=True, cast=bool)

# ALLOWED_HOSTS includes local and your future Render domain
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost,.onrender.com').split(',')

# --- APPS ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.humanize',
    'cloudinary_storage',  # Must be above staticfiles
    'django.contrib.staticfiles',
    'cloudinary',
    'events',
    'payments',
    'analytics',
    'seller_merchandise',
]

# --- MIDDLEWARE ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Critical for Render static files
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

# --- DATABASE ---
# Production-ready: Use DATABASE_URL from environment (Render/Supabase)
# Fallback: Local SQLite for development if no URL is found
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=600,
        conn_params={'sslmode': 'require'}
    )
}

# --- STATIC & MEDIA FILES ---
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# WhiteNoise Optimization for Production
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Cloudinary Configuration for Image Uploads
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': config('CLOUDINARY_CLOUD_NAME', default='dr6mf1spn'),
    'API_KEY': config('CLOUDINARY_API_KEY', default='353117476641669'),
    'API_SECRET': config('CLOUDINARY_API_SECRET', default='A3sgGJBXl_EjBS7Web6EEoFbxKU'),
}
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# --- PRODUCTION SECURITY ---
if not DEBUG:
    CSRF_TRUSTED_ORIGINS = [f"https://{origin.strip()}" for origin in config('CSRF_TRUSTED_ORIGINS', default='').split(',') if origin.strip()]
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# --- INTEGRATIONS ---
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@vibeninjas.com')

# M-Pesa / Stripe / Twilio (Configs kept from your source)
MPESA_CONSUMER_KEY = config('CONSUMER_KEY', default='') 
MPESA_CONSUMER_SECRET = config('CONSUMER_SECRET', default='')   
MPESA_SHORTCODE = config('SHORTCODE', default='')   
MPESA_PASSKEY = config('PASSKEY', default='') 
MPESA_BASE_URL = config('BASE_URL', default='https://api.safaricom.co.ke')
MPESA_CALLBACK_URL = config('CALLBACK_URL', default='')

STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')

TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', default='')
TWILIO_PHONE_NUMBER = config('TWILIO_PHONE_NUMBER', default='')

# --- AUTHENTICATION ---
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'
AUTH_USER_MODEL = 'events.User'

# --- MISC ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'