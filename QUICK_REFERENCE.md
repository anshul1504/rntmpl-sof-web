# RNT MPL - Quick Reference Guide

## ðŸš€ Start Here

Your cricket platform's **authentication system is 95% complete**. Follow these 3 steps to activate email OTP:

---

## Step 1ï¸âƒ£: Add EMAIL Settings (2 minutes)

**File:** `config/settings/development.py` (or your active settings)

**Add at the end:**

```python
# EMAIL CONFIGURATION
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.thewebfix.in'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'noreply@thewebfix.in'
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = 'noreply@thewebfix.in'
```

---

## Step 2ï¸âƒ£: Test Email (3 minutes)

```bash
cd "c:\Users\PC\Desktop\RNT MPL"
python manage.py shell
```

```python
from django.core.mail import send_mail

send_mail(
    'Test from RNT MPL',
    'Testing email configuration',
    'noreply@thewebfix.in',
    ['your-email@gmail.com'],  # Change this!
)

exit()
```

Check your email inbox (or spam folder) âœ…

---

## Step 3ï¸âƒ£: Test OTP API (5 minutes)

### Request OTP
```bash
curl -X POST http://localhost:8000/api/auth/otp/request/ \
  -H "Content-Type: application/json" \
  -d '{"email": "your-email@gmail.com", "purpose": "LOGIN"}'
```

**Response:**
```json
{
  "message": "OTP sent successfully to your email",
  "email": "y***@gmail.com",
  "expires_in_seconds": 600
}
```

### Check Email for OTP Code

### Verify OTP
```bash
curl -X POST http://localhost:8000/api/auth/otp/verify/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@gmail.com",
    "otp": "123456",
    "purpose": "LOGIN"
  }'
```

**Response:**
```json
{
  "tokens": {
    "access": "eyJ0eXAiOiJKV1Q...",
    "refresh": "eyJ0eXAiOiJKV1Q..."
  },
  "user": {
    "id": 1,
    "email": "your-email@gmail.com",
    "full_name": "Your Name"
  }
}
```

âœ… **Success! You now have JWT tokens for authenticated API calls**

---

## ðŸ“š All API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/auth/register/` | Create new account |
| POST | `/api/auth/login/` | Login with email/password |
| POST | `/api/auth/otp/request/` | Request OTP via email |
| POST | `/api/auth/otp/verify/` | Verify OTP & get tokens |
| POST | `/api/auth/token/refresh/` | Refresh JWT token |
| POST | `/api/auth/logout/` | Logout & blacklist token |
| GET | `/api/auth/me/` | Get current user |
| GET | `/api/auth/tenants/me/` | Get user's tenants |
| POST | `/api/auth/tenant/onboard/` | Create new tenant |

---

## ðŸ”‘ Register & Login Flow

### Option A: Traditional Login (Email + Password)
```bash
# 1. Register
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }'

# 2. Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

### Option B: Passwordless Login (Email OTP)
```bash
# 1. Request OTP
curl -X POST http://localhost:8000/api/auth/otp/request/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "purpose": "LOGIN"}'

# 2. Get OTP from email
# Check inbox for 6-digit code

# 3. Verify OTP & get tokens
curl -X POST http://localhost:8000/api/auth/otp/verify/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "otp": "123456",
    "purpose": "LOGIN"
  }'
```

---

## ðŸ“‹ Use JWT Token in Requests

**Add Authorization header to all authenticated requests:**

```bash
curl -X GET http://localhost:8000/api/auth/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

**Token expires in 15 minutes. Refresh it:**

```bash
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "YOUR_REFRESH_TOKEN_HERE"}'
```

---

## ðŸ‘¥ Multi-Tenant Onboarding

Create and switch between multiple teams/organizations:

```bash
curl -X POST http://localhost:8000/api/auth/tenant/onboard/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "India Cricket Team",
    "description": "National team management"
  }'
```

**Get user's tenants:**

```bash
curl -X GET http://localhost:8000/api/auth/tenants/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## ðŸ§ª Run Tests

```bash
python manage.py test apps.accounts.tests -v 2
```

**Expected output:** All 20+ tests pass âœ…

---

## ðŸ“ Important Files

| File | Purpose | Lines |
|------|---------|-------|
| `apps/accounts/auth_serializers.py` | API data validation | 400+ |
| `apps/accounts/auth_views.py` | API endpoints | 160 |
| `apps/accounts/auth_urls.py` | URL routing | 35 |
| `apps/accounts/email_otp.py` | Email service | 75 |
| `apps/accounts/test_auth.py` | Unit tests | 450+ |
| `apps/accounts/admin.py` | Admin dashboard | 350+ |

---

## ðŸ“– Full Documentation

| File | Topics |
|------|--------|
| `docs/AUTH_API.md` | Complete API reference + examples |
| `docs/QUICKSTART.md` | Full setup guide |
| `docs/EMAIL_OTP_SETUP.md` | Email configuration |
| `docs/EMAIL_OTP_HINDI.md` | à¤¹à¤¿à¤‚à¤¦à¥€ à¤®à¥‡à¤‚ à¤¸à¤¾à¤°à¤¾à¤‚à¤¶ (Hindi summary) |
| `docs/NEXT_STEPS_EMAIL_INTEGRATION.md` | Step-by-step integration |
| `docs/PHASE1_AUTH_REPORT.md` | Technical details |
| `docs/SESSION_REPORT.md` | Architecture & deployment |

---

## ðŸ”’ Security Features

âœ… **Password:** PBKDF2-SHA256 hashing  
âœ… **JWT:** HS256, 15min/7day expiry  
âœ… **OTP:** HMAC-SHA256, never plaintext  
âœ… **Rate Limiting:** 5 attempts, 10-minute lockout  
âœ… **Multi-Tenant:** Isolated user scopes  
âœ… **Token Blacklist:** Logout support  

---

## âš ï¸ Troubleshooting

| Issue | Solution |
|-------|----------|
| Email not received | Check spam folder, verify credentials |
| Connection timeout | Check firewall allows port 465, try 587 |
| "Invalid credentials" | Verify `EMAIL_HOST_PASSWORD` is set correctly in your local environment. |
| OTP expired | OTP is 10 minutes, check server time |
| Token expired | Use refresh token to get new access token |

---

## ðŸŽ¯ What's Next?

1. âœ… **Add EMAIL settings** (you are here)
2. âœ… **Test email & OTP** (then mark as done)
3. â³ **Create Postman collection** for easy testing
4. â³ **Build frontend** (login page, OTP form)
5. â³ **Enable social login** (Google, Facebook)
6. â³ **Start Phase 2** (player management)

---

## ðŸ’¡ Tips

- Use `http://localhost:8000/admin/` to manage users/tenants
- Access token goes in `Authorization: Bearer <token>` header
- Refresh token goes in POST body as `{"refresh": "<token>"}`
- Each user can have multiple tenants (organizations)
- OTP is 6 random digits, changes each time
- Tokens auto-expire (access: 15 min, refresh: 7 days)

---

## ðŸ“ž Need Help?

1. Check `docs/AUTH_API.md` for API examples
2. Check `docs/EMAIL_OTP_HINDI.md` for Hindi explanation
3. Check `docs/NEXT_STEPS_EMAIL_INTEGRATION.md` for detailed steps
4. Run `python manage.py test apps.accounts -v 2` to verify setup

---

**Status:** Email OTP system ready for activation! âœ¨  
**Time to activate:** ~10 minutes  
**Difficulty:** Very Easy (just add settings + test)


