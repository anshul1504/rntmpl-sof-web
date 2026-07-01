from .base import *  # noqa

import os


def env_bool(name, default):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.lower() in ('true', '1', 'yes', 'on')


DEBUG = False

ALLOWED_HOSTS = os.environ.get(
    'DJANGO_ALLOWED_HOSTS', '.cricketecosystem.com'
).split(',')

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY must be set in production")

# MySQL in production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'connect_timeout': 10,
        },
        'ATOMIC_REQUESTS': True,
        'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', 60)),
    }
}

# Security
SECURE_SSL_REDIRECT = env_bool('DJANGO_SECURE_SSL_REDIRECT', True)
SESSION_COOKIE_SECURE = env_bool('DJANGO_SESSION_COOKIE_SECURE', True)
CSRF_COOKIE_SECURE = env_bool('DJANGO_CSRF_COOKIE_SECURE', True)
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SAMESITE = 'Lax'
SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_SECURE_HSTS_SECONDS', 31536000))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool('DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS', True)
SECURE_HSTS_PRELOAD = env_bool('DJANGO_SECURE_HSTS_PRELOAD', True)
SECURE_BROWSER_XSS_FILTER = env_bool('DJANGO_SECURE_BROWSER_XSS_FILTER', True)
SECURE_CONTENT_TYPE_NOSNIFF = env_bool('DJANGO_SECURE_CONTENT_TYPE_NOSNIFF', True)

# CORS
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = os.environ.get(
    'CORS_ALLOWED_ORIGINS', 'https://*.cricketecosystem.com'
).split(',')

CSRF_TRUSTED_ORIGINS = os.environ.get(
    'CSRF_TRUSTED_ORIGINS', 'https://*.cricketecosystem.com'
).split(',')

# Cache
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_CACHE_ALIAS = 'default'

# Email (SMTP)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', EMAIL_HOST)
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', EMAIL_PORT))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() in ('true', '1')
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'False').lower() in ('true', '1')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', EMAIL_HOST_USER)
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', EMAIL_HOST_PASSWORD)
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', DEFAULT_FROM_EMAIL)
SERVER_EMAIL = os.environ.get('SERVER_EMAIL', DEFAULT_FROM_EMAIL)

# AWS S3 Storage
if os.environ.get('AWS_STORAGE_BUCKET_NAME'):
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'

# Logging
LOGGING['root']['handlers'] = ['console', 'file']  # noqa
LOGGING['root']['level'] = 'WARNING'  # noqa

# Throttle
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {  # noqa
    'anon': '20/hour',
    'user': '500/hour',
}

# Static files
STATIC_ROOT = '/app/staticfiles'
MEDIA_ROOT = '/app/media'
