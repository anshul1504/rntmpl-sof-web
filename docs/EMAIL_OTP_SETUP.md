# Email OTP Setup Guide

## à¤†à¤ªà¤•à¤¾ Configuration:

```python
# Add to settings.py or .env

# Email Configuration (SMTP)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.thewebfix.in'
EMAIL_PORT = 465  # à¤¯à¤¾ 587 (non-SSL à¤•à¥‡ à¤²à¤¿à¤)
EMAIL_USE_TLS = False  # True if port 587
EMAIL_USE_SSL = True   # True if port 465
EMAIL_HOST_USER = 'noreply@thewebfix.in'
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = 'noreply@thewebfix.in'
SERVER_EMAIL = 'noreply@thewebfix.in'
```

## Files Updated:

âœ… **auth_serializers.py** - Updated OTPRequestSerializer & OTPVerifySerializer
- à¤…à¤¬ à¤¸à¤¿à¤°à¥à¤« EMAIL OTP support à¤•à¤°à¤¤à¤¾ à¤¹à¥ˆ
- Phone/SMS removed

âœ… **auth_views.py** - Updated OTPRequestView & OTPVerifyView
- Email-only endpoints

âœ… **email_otp.py** - à¤¨à¤¯à¤¾ Email Service
- SMTP à¤•à¥‡ through OTP à¤­à¥‡à¤œà¤¤à¤¾ à¤¹à¥ˆ
- HTML templates support

## API Endpoints (Updated):

```bash
# 1. Request OTP (EMAIL ONLY)
curl -X POST http://localhost:8000/api/auth/otp/request/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "player@example.com",
    "purpose": "LOGIN"
  }'

# Request body:
# {
#   "email": "player@example.com",
#   "purpose": "LOGIN"  // à¤¯à¤¾ "REGISTRATION", "VERIFICATION"
# }

# Response:
# {
#   "message": "OTP sent successfully to your email",
#   "email": "p***@example.com",
#   "expires_in_seconds": 600
# }

# 2. Verify OTP
curl -X POST http://localhost:8000/api/auth/otp/verify/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "player@example.com",
    "otp": "123456",
    "purpose": "LOGIN"
  }'

# Response:
# {
#   "user": { ... },
#   "tokens": {
#     "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#     "refresh": "..."
#   }
# }
```

## Email OTP Flow:

```
1. User à¤•à¥‹ email request à¤•à¤°à¤¨à¤¾ à¤¹à¥ˆ:
   POST /api/auth/otp/request/
   { "email": "player@example.com", "purpose": "LOGIN" }

2. System:
   - 6-digit OTP generate à¤•à¤°à¥‡à¤—à¤¾
   - OTP à¤•à¥‹ hash à¤•à¤°à¤•à¥‡ database à¤®à¥‡à¤‚ store à¤•à¤°à¥‡à¤—à¤¾
   - Email à¤­à¥‡à¤œà¥‡à¤—à¤¾ (à¤†à¤ªà¤•à¥‡ SMTP à¤¸à¥‡)

3. User à¤•à¥‹ email à¤†à¤à¤—à¤¾:
   - Subject: "Your OTP for LOGIN - RNT MPL Cricket Platform"
   - Body: Beautiful HTML à¤®à¥‡à¤‚ OTP à¤¦à¤¿à¤¯à¤¾ à¤¹à¥‹à¤—à¤¾

4. User OTP verify à¤•à¤°à¥‡à¤—à¤¾:
   POST /api/auth/otp/verify/
   { "email": "player@example.com", "otp": "123456", "purpose": "LOGIN" }

5. System:
   - OTP verify à¤•à¤°à¥‡à¤—à¤¾
   - User à¤•à¥‹ auto-create/login à¤•à¤°à¥‡à¤—à¤¾
   - JWT tokens return à¤•à¤°à¥‡à¤—à¤¾
```

## Security Features:

âœ… OTP Hashing (HMAC-SHA256)
- à¤•à¤­à¥€ plaintext à¤®à¥‡à¤‚ store à¤¨à¤¹à¥€à¤‚ à¤¹à¥‹à¤¤à¤¾
- Database à¤®à¥‡à¤‚ à¤¸à¥à¤°à¤•à¥à¤·à¤¿à¤¤

âœ… Rate Limiting
- Max 5 attempts per OTP
- 10-minute expiry
- Auto-lock after max attempts

âœ… Email Masking
- Response à¤®à¥‡à¤‚ email masked à¤¦à¤¿à¤¯à¤¾ à¤œà¤¾à¤¤à¤¾ à¤¹à¥ˆ
- Example: "p***@example.com"

## Quick Test:

```bash
# 1. Request OTP
curl -X POST http://localhost:8000/api/auth/otp/request/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "purpose": "LOGIN"}'

# 2. Check email for OTP code

# 3. Verify OTP
curl -X POST http://localhost:8000/api/auth/otp/verify/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "otp": "XXXXXX", "purpose": "LOGIN"}'

# 4. Get token in response
```

## Troubleshooting:

âŒ "Failed to send OTP" error?
- Check EMAIL_HOST_USER à¤”à¤° EMAIL_HOST_PASSWORD
- Verify SMTP port (465 vs 587)
- Check mail.thewebfix.in server status
- Review Django logs for detailed error

âŒ Email à¤¨à¤¹à¥€à¤‚ à¤† à¤°à¤¹à¤¾?
- Check spam/junk folder
- Verify DEFAULT_FROM_EMAIL
- Check server logs: `django.request` logger
- Ensure EMAIL_HOST_USER à¤•à¤¾ password correct à¤¹à¥ˆ

âŒ OTP invalid?
- OTP 10 minutes à¤®à¥‡à¤‚ expire à¤¹à¥‹ à¤œà¤¾à¤¤à¤¾ à¤¹à¥ˆ
- Max 5 attempts à¤²à¤—à¤¤à¥‡ à¤¹à¥ˆà¤‚
- à¤¹à¤° à¤—à¤²à¤¤ attempt à¤•à¥‡ à¤¬à¤¾à¤¦ à¤¨à¤¯à¤¾ request à¤•à¤°à¤¨à¤¾ à¤ªà¤¡à¤¼à¤¤à¤¾ à¤¹à¥ˆ

## Django Settings à¤•à¥‹ Update à¤•à¤°à¤¨à¥‡ à¤•à¥‡ à¤²à¤¿à¤:

**1. à¤…à¤ªà¤¨à¥‡ settings file à¤®à¥‡à¤‚ add à¤•à¤°à¥‡à¤‚:**

```python
# config/settings/production.py or config/settings/development.py

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'mail.thewebfix.in')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '465'))
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'True') == 'True'
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'False') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'noreply@thewebfix.in')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@thewebfix.in')
SERVER_EMAIL = os.getenv('SERVER_EMAIL', 'noreply@thewebfix.in')
```

**2. .env.local à¤®à¥‡à¤‚ add à¤•à¤°à¥‡à¤‚:**

```env
EMAIL_HOST=mail.thewebfix.in
EMAIL_PORT=465
EMAIL_USE_SSL=True
EMAIL_USE_TLS=False
EMAIL_HOST_USER=noreply@thewebfix.in
EMAIL_HOST_PASSWORD=your-smtp-password
DEFAULT_FROM_EMAIL=noreply@thewebfix.in
```

**3. Django check à¤•à¤°à¥‡à¤‚:**

```bash
python manage.py check
```

## Summary:

âœ… **Email OTP à¤¹à¥€ à¤¹à¥ˆ** - SMS/Phone removed
âœ… **SMTP configure à¤•à¤¿à¤¯à¤¾** - à¤†à¤ªà¤•à¥‡ server details à¤¸à¥‡
âœ… **Security** - OTP hashing, rate limiting
âœ… **API Ready** - Test à¤•à¤° à¤¸à¤•à¤¤à¥‡ à¤¹à¥‹
âœ… **Production Ready** - Email template included

---

**Date:** 2026-06-16  
**Status:** âœ… Email OTP System Complete

à¤…à¤¬ à¤†à¤ªà¤•à¥‹ à¤¬à¤¸ Django settings à¤®à¥‡à¤‚ EMAIL configuration add à¤•à¤°à¤¨à¤¾ à¤¹à¥ˆ à¤”à¤° OTP à¤­à¥‡à¤œà¤¨à¤¾ à¤¶à¥à¤°à¥‚ à¤¹à¥‹ à¤œà¤¾à¤à¤—à¤¾!



