# Next Steps: Complete Email OTP Integration

## ðŸŽ¯ Immediate Action Items (To Make Email OTP Work)

### Step 1: Update Django Settings
**File:** `config/settings/development.py` (or your active settings file)

**Add these lines at the end:**

```python
# ============================================================================
# EMAIL CONFIGURATION
# ============================================================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.thewebfix.in'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False
EMAIL_HOST_USER = 'noreply@thewebfix.in'
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = 'noreply@thewebfix.in'
SERVER_EMAIL = 'noreply@thewebfix.in'
```

**Why?** Django needs these settings to know how to connect to your SMTP server.

---

### Step 2: Create Email Templates (Optional but Recommended)

**Directory Structure:**
```
templates/
â”œâ”€â”€ emails/
â”‚   â”œâ”€â”€ otp_email.html
â”‚   â””â”€â”€ otp_email.txt
```

**File:** `templates/emails/otp_email.html`
```html
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #1e88e5; color: white; padding: 20px; text-align: center; }
        .otp-code { font-size: 32px; font-weight: bold; color: #1e88e5; text-align: center; padding: 20px; }
        .footer { text-align: center; color: #666; font-size: 12px; margin-top: 30px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>RNT MPL - OTP Verification</h1>
        </div>
        
        <p>Hi {{ user_email }},</p>
        
        <p>Your One-Time Password (OTP) for login is:</p>
        
        <div class="otp-code">{{ otp_code }}</div>
        
        <p>This code will expire in <strong>10 minutes</strong>.</p>
        
        <p style="color: #d32f2f;">
            <strong>âš ï¸ Security Notice:</strong> 
            Do not share this OTP with anyone. RNT MPL support team will never ask you for this code.
        </p>
        
        <div class="footer">
            <p>This is an automated email. Please do not reply.</p>
            <p>&copy; 2024 RNT MPL. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
```

**File:** `templates/emails/otp_email.txt`
```
RNT MPL - OTP VERIFICATION
============================

Hi {{ user_email }},

Your One-Time Password (OTP) for login is:

{{ otp_code }}

This code will expire in 10 minutes.

SECURITY NOTICE: Do not share this OTP with anyone. 
RNT MPL support team will never ask you for this code.

---
This is an automated email. Please do not reply.
Â© 2024 RNT MPL. All rights reserved.
```

**Note:** If you don't create these, Django will send plain text emails. It's functional but less professional.

---

### Step 3: Update EmailOTPService (Optional Enhancement)

**File:** `apps/accounts/email_otp.py`

Add template rendering (if you created templates above):

```python
from django.template.loader import render_to_string

class EmailOTPService:
    @staticmethod
    def send_otp(email, otp_code, purpose="LOGIN"):
        """Send OTP via email with template rendering"""
        
        subject = f"RNT MPL - Your OTP for {purpose}"
        
        # If templates exist, use them; otherwise use plain text
        context = {
            'user_email': email,
            'otp_code': otp_code,
            'purpose': purpose,
        }
        
        try:
            html_message = render_to_string('emails/otp_email.html', context)
        except:
            html_message = None
        
        message = render_to_string('emails/otp_email.txt', context)
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return True
```

---

## ðŸ§ª Testing Email OTP

### Test 1: Django Email Backend Test

```bash
cd "c:\Users\PC\Desktop\RNT MPL"
python manage.py shell
```

```python
from django.core.mail import send_mail

result = send_mail(
    'Test from RNT MPL',
    'This is a test email to verify SMTP configuration',
    'noreply@thewebfix.in',
    ['your-test-email@gmail.com'],  # Change this to your email
    fail_silently=False,
)

print(f"Email sent: {result}")
exit()
```

âœ… If result is `1`, email was sent successfully!  
âŒ If you get error, check:
- EMAIL settings in settings.py
- SMTP credentials are configured through local environment variables.
- Port 465 is accessible (might be blocked by firewall)

---

### Test 2: API Test - OTP Request

```bash
curl -X POST http://localhost:8000/api/auth/otp/request/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-test-email@gmail.com",
    "purpose": "LOGIN"
  }'
```

**Expected Response:**
```json
{
  "message": "OTP sent successfully to your email",
  "email": "y***@gmail.com",
  "expires_in_seconds": 600
}
```

âœ… If successful, check your email inbox (or spam folder)

---

### Test 3: API Test - OTP Verify

Once you receive the OTP in your email:

```bash
curl -X POST http://localhost:8000/api/auth/otp/verify/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-test-email@gmail.com",
    "otp": "123456",
    "purpose": "LOGIN"
  }'
```

**Expected Response:**
```json
{
  "user": {
    "id": 1,
    "email": "your-test-email@gmail.com",
    "full_name": "Your Name",
    "is_active": true,
    "date_joined": "2024-06-16T12:00:00Z"
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  },
  "message": "Login successful"
}
```

âœ… If successful, you have JWT tokens and can make authenticated API calls!

---

## ðŸ“‹ Troubleshooting

| Issue | Solution |
|-------|----------|
| **Email not received** | Check spam folder, verify EMAIL_HOST_USER/PASSWORD correct, try port 587 instead of 465 |
| **Connection timeout** | Check if port 465 is blocked by firewall, try TLS on port 587 instead |
| **"Invalid credentials"** | Verify `EMAIL_HOST_PASSWORD` is set correctly in your local environment. |
| **Django error: Settings not configured** | Make sure EMAIL_BACKEND is set before sending mail |
| **OTP showing as expired** | OTP is set to 10 minutes, make sure your server time is correct |

---

## ðŸš€ After Email OTP Works

Once you verify email OTP is working:

1. âœ… Create Postman collection for all 9 auth endpoints
2. âœ… Setup Docker Compose (MySQL, Redis, Nginx)
3. âœ… Add permission matrix enforcement
4. âœ… Create frontend login page (React/Vue)
5. âœ… Add social login (Google/Facebook)
6. âœ… Implement async email sending (Celery)
7. âœ… Setup email queues and retry logic

---

## ðŸ“ Files Already Ready

| File | Status | Purpose |
|------|--------|---------|
| `apps/accounts/auth_serializers.py` | âœ… Ready | OTP serializers |
| `apps/accounts/auth_views.py` | âœ… Ready | OTP endpoints |
| `apps/accounts/email_otp.py` | âœ… Ready | Email sending service |
| `apps/accounts/auth_urls.py` | âœ… Ready | URL routing |
| `docs/AUTH_API.md` | âœ… Ready | API documentation |
| `docs/EMAIL_OTP_SETUP.md` | âœ… Ready | Setup guide |
| `templates/emails/` | â³ Optional | Email templates |

---

## ðŸŽ¯ Summary

To complete email OTP integration:

1. **Add EMAIL settings** to `config/settings/development.py` (copy from Step 1 above)
2. **Test with Django shell** (copy from Test 1 above)
3. **Test with API** (use curl commands from Test 2 & 3)
4. **Check inbox** for OTP emails

**Estimated time:** 5-10 minutes

---

**Questions?** Check `docs/EMAIL_OTP_HINDI.md` for detailed Hindi explanation or `docs/AUTH_API.md` for API examples.


