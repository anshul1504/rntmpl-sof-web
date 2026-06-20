from .base import *  # noqa

DEBUG = True

ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

CORS_ALLOW_ALL_ORIGINS = True

# ============================================================================
# EMAIL CONFIGURATION (SMTP)
# ============================================================================
# Using user's SMTP server: mail.thewebfix.in
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.thewebfix.in'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False
EMAIL_HOST_USER = 'noreply@thewebfix.in'
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = 'noreply@thewebfix.in'
SERVER_EMAIL = 'noreply@thewebfix.in'

# Optional: For development, uncomment below to see emails in console
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

SMS_BACKEND = 'console'

SHELL_PLUS_PRINT_SQL = True

