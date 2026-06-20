# RNT MPL - Phase 1 Quick Start Guide

## Getting Started with Authentication & Onboarding

This guide covers setting up and using the new JWT-based authentication system for the RNT MPL cricket platform.

### Prerequisites

- Python 3.12+
- Django 6.0+
- PostgreSQL or MySQL (or SQLite for development)
- git

### Installation & Setup

#### 1. Clone & Install Dependencies

```bash
git clone <repo-url> rnt-mpl
cd rnt-mpl
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 2. Configure Environment

Create `.env.local`:

```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Emails (development)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-password

# OTP (development)
OTP_EXPIRY_MINUTES=10
OTP_MAX_ATTEMPTS=5

# JWT
SIMPLE_JWT_ALGORITHM=HS256
SIMPLE_JWT_SIGNING_KEY=your-secret-key
SIMPLE_JWT_ACCESS_TOKEN_LIFETIME=15m
SIMPLE_JWT_REFRESH_TOKEN_LIFETIME=7d
```

#### 3. Database Setup

```bash
# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load fixtures (if available)
python manage.py loaddata initial_data
```

#### 4. Run Development Server

```bash
python manage.py runserver
```

Access:
- App: http://localhost:8000
- Admin: http://localhost:8000/admin

### API Usage Examples

#### 1. User Registration

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "player@example.com",
    "full_name": "John Cricket",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!"
  }'

# Response:
# {
#   "user": {
#     "id": 1,
#     "email": "player@example.com",
#     "full_name": "John Cricket",
#     ...
#   },
#   "tokens": {
#     "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#     "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
#   }
# }
```

#### 2. Login with Email/Password

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "player@example.com",
    "password": "SecurePass123!"
  }'
```

#### 3. Login with OTP

**Step 1: Request OTP**

```bash
curl -X POST http://localhost:8000/api/auth/otp/request/ \
  -H "Content-Type: application/json" \
  -d '{
    "email_or_phone": "player@example.com",
    "purpose": "LOGIN"
  }'

# Response (DEV MODE - OTP visible):
# {
#   "otp": "123456",
#   "message": "OTP sent successfully",
#   "target": "p***@example.com",
#   "expires_in_seconds": 600
# }
```

**Step 2: Verify OTP & Login**

```bash
curl -X POST http://localhost:8000/api/auth/otp/verify/ \
  -H "Content-Type: application/json" \
  -d '{
    "email_or_phone": "player@example.com",
    "otp": "123456",
    "purpose": "LOGIN"
  }'

# Returns tokens like registration endpoint
```

#### 4. Get Current User

```bash
curl -X GET http://localhost:8000/api/auth/me/ \
  -H "Authorization: Bearer <access_token>"
```

#### 5. Create Organization/Tenant

```bash
curl -X POST http://localhost:8000/api/auth/onboard-tenant/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mumbai Cricket Academy",
    "tenant_type": "ACADEMY",
    "subdomain": "mca",
    "primary_color": "#1a56db",
    "secondary_color": "#7c3aed"
  }'

# Response:
# {
#   "tenant": {
#     "id": 1,
#     "name": "Mumbai Cricket Academy",
#     "tenant_type": "ACADEMY",
#     "domain": null,
#     "subdomain": "mca",
#     ...
#   },
#   "membership": {
#     "role": "TENANT_ADMIN",
#     "is_primary": true,
#     "joined_at": "2026-06-16T12:00:00Z"
#   }
# }
```

#### 6. Refresh Token

```bash
curl -X POST http://localhost:8000/api/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "<refresh_token>"
  }'

# Response:
# {
#   "access": "new_access_token",
#   "refresh": "new_refresh_token"
# }
```

#### 7. Logout

```bash
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H "Authorization: Bearer <access_token>"
```

### Admin Interface

#### Access Admin Dashboard

1. Go to http://localhost:8000/admin
2. Login with superuser credentials

#### Manage Users

- View all registered users with filters (user type, verification status, etc.)
- Search by email, name, or phone
- Edit user profiles, permissions, subscriptions
- View login history and device access
- Manage 2FA settings

#### Manage Tenants

- Create/edit organizations (Academy, League, Tournament, etc.)
- Manage branding (colors, logos)
- View member count and subscription status
- Set domain/subdomain

#### Manage Memberships

- Assign users to tenants
- Set roles (TENANT_ADMIN, MEMBER, etc.)
- Mark primary tenant
- Track join dates and activity

#### Manage Roles & Permissions

- Create custom roles per tenant
- Define permission matrices
- Control resource access (CREATE, READ, UPDATE, DELETE, APPROVE, EXPORT)

### Testing

#### Run Unit Tests

```bash
python manage.py test apps.accounts.test_auth --verbosity=2
```

#### Test with Postman

1. Import `docs/AUTH_API.md` to Postman
2. Set base URL to `http://localhost:8000/api`
3. Create variables:
   - `access_token` - set after login
   - `refresh_token` - set after login
   - `tenant_id` - set after onboarding

#### Manual API Testing

Use the curl examples above or import to Postman/Insomnia

### Database Models

#### User
- Email-based authentication
- User types (SUPER_ADMIN, PLAYER, FAN, etc.)
- Verification status (email, phone, Aadhaar, PAN)
- 2FA settings
- Login history and IP tracking

#### Tenant
- Multi-tenant organization support
- Tenant types (ACADEMY, LEAGUE, TOURNAMENT, etc.)
- Branding customization
- Subscription management
- Domain/subdomain configuration

#### UserTenant
- User-tenant membership mapping
- Primary tenant designation
- Role assignment
- Activity tracking (joined_at)

#### Role
- System and custom roles
- Tenant-scoped (TENANT_ADMIN, MEMBER, etc.)
- Permission matrix definition

#### OTPVerification
- Email/phone OTP storage (hashed)
- Purpose-based (LOGIN, REGISTRATION, VERIFICATION)
- Expiry and attempt tracking
- Used/unused status

#### LoginHistory
- Login attempt tracking
- Success/failure status
- IP address and device info
- Location tracking (optional)

### Security Features

✅ **Implemented:**
- [x] JWT token-based authentication
- [x] Hashed OTP storage (HMAC-SHA256)
- [x] Rate limiting (5 attempts, 10 min expiry)
- [x] Email/phone verification
- [x] Multi-tenant isolation
- [x] Role-based access control (RBAC)
- [x] Login history auditing
- [x] IP and device tracking

🔄 **In Development:**
- [ ] Email/SMS delivery integration
- [ ] Social login (Google, Facebook)
- [ ] 2FA TOTP
- [ ] Token blacklist for logout
- [ ] Permission matrix enforcement

### Environment Variables

```env
# Core
DEBUG=True/False
SECRET_KEY=<random-secret>
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgres://user:pass@localhost/dbname

# Email (SendGrid)
SENDGRID_API_KEY=<key>
DEFAULT_FROM_EMAIL=noreply@platform.com

# SMS (Twilio)
TWILIO_ACCOUNT_SID=<sid>
TWILIO_AUTH_TOKEN=<token>
TWILIO_PHONE_NUMBER=<number>

# JWT
SIMPLE_JWT_ALGORITHM=HS256
SIMPLE_JWT_ACCESS_TOKEN_LIFETIME=15 minutes
SIMPLE_JWT_REFRESH_TOKEN_LIFETIME=7 days

# OTP
OTP_EXPIRY_MINUTES=10
OTP_MAX_ATTEMPTS=5

# Stripe/Razorpay
STRIPE_PUBLIC_KEY=<key>
STRIPE_SECRET_KEY=<key>

# AWS S3 (for media)
AWS_ACCESS_KEY_ID=<key>
AWS_SECRET_ACCESS_KEY=<key>
AWS_STORAGE_BUCKET_NAME=<bucket>
```

### Troubleshooting

#### OTP Not Sending?

1. Check `settings.EMAIL_BACKEND` - should be configured for production
2. Verify `SENDGRID_API_KEY` is set
3. Check email logs for errors

#### Token Expired?

1. Use the `refresh/` endpoint with your refresh token
2. Refresh tokens last 7 days by default
3. Set `SIMPLE_JWT_REFRESH_TOKEN_LIFETIME` in settings

#### Tenant Isolation Issues?

1. Verify user has `UserTenant` membership
2. Check role permissions in Permission Matrix
3. Verify tenant_id is set on all tenant-owned records

#### Admin Access Denied?

1. Verify user `is_staff=True` and `is_superuser=True`
2. Check user is active (`is_active=True`)
3. Verify permission matrix allows ADMIN access

### Common Workflows

#### Workflow 1: Sign Up & Create Organization

```
1. User registers with email/password
2. System creates User record, sends verification email
3. User creates tenant (organization)
4. System creates Tenant and assigns user as TENANT_ADMIN
5. User can now invite team members
```

#### Workflow 2: Login with OTP

```
1. User requests OTP for email/phone
2. System generates and stores hashed OTP
3. System sends OTP via email/SMS
4. User enters OTP
5. System validates, creates/retrieves User
6. System returns JWT tokens
```

#### Workflow 3: Token Refresh

```
1. User makes API request with access token
2. Server returns 401 if token expired
3. Client uses refresh token to get new access token
4. Client retries request with new token
```

### Project Structure

```
rnt-mpl/
├── apps/
│   ├── accounts/           # User, tenant, RBAC models
│   │   ├── auth_serializers.py   # JWT/OTP serializers
│   │   ├── auth_views.py         # API endpoints
│   │   ├── auth_urls.py          # Auth routes
│   │   ├── admin.py              # Admin interface
│   │   └── models.py             # User, Tenant, Role
│   ├── api/                # API configuration
│   │   ├── urls.py         # Main API routes
│   │   └── views.py        # API viewsets
│   └── common/             # Shared utilities
│       ├── encryption.py   # Field encryption
│       └── models.py       # Base models & mixins
├── config/                 # Django settings
│   ├── settings/
│   │   ├── base.py        # Common settings
│   │   ├── development.py # Dev settings
│   │   └── production.py  # Prod settings
│   ├── urls.py            # Main URL routing
│   └── wsgi.py            # WSGI application
├── docs/                   # Documentation
│   ├── AUTH_API.md        # API reference
│   ├── PHASE1_AUTH_REPORT.md
│   └── DEEP_ENTERPRISE_AUDIT.md
└── manage.py              # Django CLI

```

### Next Steps

1. **Integrate Email/SMS** - Connect SendGrid and Twilio for OTP delivery
2. **Add Social Login** - Implement Google and Facebook OAuth
3. **Enable 2FA** - Add TOTP to login flow
4. **Test Integration** - Run full E2E tests with Docker Compose
5. **Player Management** - Build CRUD for players/teams
6. **Tournament Setup** - Implement tournament registration and fixtures

### Support & Resources

- **API Documentation:** See `/docs/AUTH_API.md`
- **Test Cases:** See `/apps/accounts/test_auth.py`
- **Django Docs:** https://docs.djangoproject.com/
- **DRF Docs:** https://www.django-rest-framework.org/
- **JWT Reference:** https://simplejwt.readthedocs.io/

### Contributing

1. Create feature branch: `git checkout -b feature/auth-improvements`
2. Implement changes with tests
3. Submit PR with description
4. Code review and merge

### License

[Add your license here]

---

**Last Updated:** 2026-06-16  
**Phase:** 1 - Authentication & Onboarding MVP  
**Status:** In Development (40% complete)

