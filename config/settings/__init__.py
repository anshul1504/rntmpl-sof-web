# Local development settings
from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

CORS_ALLOW_ALL_ORIGINS = True
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.thewebfix.in'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False
EMAIL_HOST_USER = 'noreply@thewebfix.in'
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = 'noreply@thewebfix.in'
SERVER_EMAIL = 'noreply@thewebfix.in'
SMS_BACKEND = 'console'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'rnt-mpl-dev-cache',
    }
}

# Keep local terminal output limited to runserver requests and real errors.
# File logging is disabled locally to prevent Windows rollover lock traces.
LOGGING['root'] = {'handlers': ['console'], 'level': 'WARNING'}
LOGGING['loggers']['django'] = {
    'handlers': ['console'],
    'level': 'WARNING',
    'propagate': False,
}
LOGGING['loggers']['django.server'] = {
    'handlers': ['console'],
    'level': 'INFO',
    'propagate': False,
}
LOGGING['loggers']['django.db.backends'] = {
    'handlers': ['console'],
    'level': 'WARNING',
    'propagate': False,
}
LOGGING['loggers']['apps'] = {
    'handlers': ['console'],
    'level': 'WARNING',
    'propagate': False,
}

