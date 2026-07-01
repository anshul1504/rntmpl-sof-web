"""
Email Configuration for OTP
Add these settings to your Django settings file
"""

# ============================================================================
# EMAIL CONFIGURATION (FOR OTP)
# ============================================================================
# Your SMTP Server: mail.thewebfix.in
# Email: noreply@thewebfix.in
# Port: 465 (SSL) or 587 (TLS)

import os

# Email Backend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# SMTP Server Details
EMAIL_HOST = os.getenv('EMAIL_HOST', 'mail.thewebfix.in')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '465'))

# SSL vs TLS (choose one)
# For port 465: use SSL
# For port 587: use TLS
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'True') == 'True'
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'False') == 'True'

# Credentials
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'noreply@thewebfix.in')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

# Default From Email
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@thewebfix.in')
SERVER_EMAIL = os.getenv('SERVER_EMAIL', 'noreply@thewebfix.in')

# ============================================================================
# How to use these settings:
# ============================================================================
# 
# Option 1: Hardcode in settings (for development only)
# -------------------------------------------------------
# EMAIL_HOST = 'mail.thewebfix.in'
# EMAIL_PORT = 465
# EMAIL_USE_SSL = True
# EMAIL_HOST_USER = 'noreply@thewebfix.in'
# EMAIL_HOST_PASSWORD = 'your-smtp-password'
#
# Option 2: Use environment variables (RECOMMENDED for production)
# -----------------------------------------------------------------
# Create .env file:
#   EMAIL_HOST=mail.thewebfix.in
#   EMAIL_PORT=465
#   EMAIL_USE_SSL=True
#   EMAIL_HOST_USER=noreply@thewebfix.in
#   EMAIL_HOST_PASSWORD=your-smtp-password
#
# Then in settings:
#   from dotenv import load_dotenv
#   load_dotenv()
#   EMAIL_HOST = os.getenv('EMAIL_HOST')
#   EMAIL_PORT = int(os.getenv('EMAIL_PORT'))
#   ...
#
# ============================================================================


