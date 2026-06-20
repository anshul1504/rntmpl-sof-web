# RNT MPL Authentication & Onboarding API

## Phase 1: Authentication System Implementation

### ✅ Completed (2026-06-16)

1. **JWT Authentication Endpoints**
   - `POST /api/auth/register/` - User registration with email/password
   - `POST /api/auth/login/` - Login with email/password, returns JWT tokens
   - `POST /api/auth/refresh/` - Refresh access token
   - `POST /api/auth/logout/` - Logout (blacklist if enabled)

2. **OTP-Based Authentication**
   - `POST /api/auth/otp/request/` - Request OTP for email or phone
   - `POST /api/auth/otp/verify/` - Verify OTP and login/register

3. **Tenant Onboarding**
   - `POST /api/auth/onboard-tenant/` - Create new organization/tenant

4. **User Management**
   - `GET /api/auth/me/` - Get authenticated user details
   - `POST /api/auth/verify-email/` - Verify email (post-link click)

### Implementation Details

#### Serializers (apps/accounts/auth_serializers.py)

**RegisterSerializer**
- Creates new user with email and password
- Returns JWT tokens (access + refresh)
- Validates duplicate email

**LoginSerializer**
- Authenticates user with email/password
- Records login history and IP
- Returns JWT tokens

**OTPRequestSerializer**
- Generates 6-digit OTP
- Stores hashed OTP for verification
- Masks target (email/phone) in response
- Supports login, registration, phone verification purposes

**OTPVerifySerializer**
- Verifies OTP against stored hash
- Rate-limited to 5 attempts
- Auto-creates user if doesn't exist
- Returns JWT tokens

**TenantOnboardingSerializer**
- Creates tenant organization with branding
- Auto-assigns creator as primary tenant admin
- Validates subdomain/domain uniqueness
- Creates TENANT_ADMIN role

**UserDetailSerializer**
- Shows user info, verification status, subscriptions
- Includes tenant memberships
- Read-only (audit trail)

#### Views (apps/accounts/auth_views.py)

All views use:
- Standard DRF APIView pattern
- Appropriate permission classes (AllowAny or IsAuthenticated)
- Consistent error responses

#### URL Routes (apps/accounts/auth_urls.py)

```
/api/auth/register/       - User registration
/api/auth/login/          - Email/password login
/api/auth/refresh/        - Token refresh
/api/auth/logout/         - Logout
/api/auth/me/             - Current user details
/api/auth/otp/request/    - Request OTP
/api/auth/otp/verify/     - Verify OTP
/api/auth/verify-email/   - Email verification
/api/auth/onboard-tenant/ - Create tenant/org
```

### Security Features

1. **Hashed OTP Storage**
   - Uses `hash_otp()` from apps.common.encryption
   - Keyed with SECRET_KEY and target email/phone
   - HMAC-SHA256 comparison (constant-time)

2. **JWT Token Management**
   - Uses `djangorestframework-simplejwt`
   - Access + refresh token pattern
   - Configurable expiry in settings

3. **Tenant Isolation**
   - UserTenant tracks memberships
   - Primary tenant designation
   - Role-based membership

4. **Rate Limiting**
   - OTP max 5 verification attempts
   - 10-minute OTP expiry

5. **Email/Phone Verification**
   - Fields: email_verified, phone_verified, is_verified
   - Tracked in LoginHistory

### Testing the Endpoints

```bash
# 1. Register new user
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "player@example.com",
    "full_name": "John Cricket",
    "password": "SecurePass123",
    "password_confirm": "SecurePass123"
  }'

# Response:
# {
#   "user": { ... user details ... },
#   "tokens": {
#     "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#     "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
#   }
# }

# 2. Login with email
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "player@example.com",
    "password": "SecurePass123"
  }'

# 3. Request OTP
curl -X POST http://localhost:8000/api/auth/otp/request/ \
  -H "Content-Type: application/json" \
  -d '{
    "email_or_phone": "9876543210",
    "purpose": "LOGIN"
  }'

# Response (dev mode shows OTP):
# {
#   "otp": "123456",  # DEV ONLY - remove in production
#   "message": "OTP sent successfully",
#   "target": "***3210",
#   "expires_in_seconds": 600
# }

# 4. Verify OTP and login
curl -X POST http://localhost:8000/api/auth/otp/verify/ \
  -H "Content-Type: application/json" \
  -d '{
    "email_or_phone": "9876543210",
    "otp": "123456",
    "purpose": "LOGIN"
  }'

# 5. Get current user
curl -X GET http://localhost:8000/api/auth/me/ \
  -H "Authorization: Bearer <access_token>"

# 6. Create tenant (requires auth)
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

# 7. Refresh token
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

### Next Steps (Phase 1)

1. **Generate migrations** for accounts app
2. **Test with database** - SQLite locally, MySQL in Docker
3. **Admin registrations** - Register auth models in Django admin
4. **RBAC enforcement** - Add permission checks to API endpoints
5. **Email/SMS adapters** - Implement OTP delivery (SendGrid, Twilio)
6. **Social login** - Add OAuth (Google, Facebook)
7. **2FA setup/verification** - Enable in serializers
8. **Tournament management MVP** - Player/team CRUD

### Database Schema Additions

No migrations created yet. The following models need migrations:
- User (already exists, may need tenant_id if enforcing tenant isolation)
- Tenant (already exists)
- UserTenant (already exists)
- Role (already exists)
- OTPVerification (already exists)
- LoginHistory (already exists)
- UserSession (already exists)

Run: `python manage.py makemigrations accounts`

### Configuration Notes

**settings.py** already has:
```python
AUTH_USER_MODEL = 'accounts.User'
REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = [
    'rest_framework_simplejwt.authentication.JWTAuthentication',
]
SIMPLE_JWT settings (expiry, algorithm, etc.)
```

### Security Checklist for Production

- [ ] Disable OTP display in to_representation() for OTPRequestSerializer
- [ ] Implement token blacklist for logout
- [ ] Add rate limiting middleware (django-ratelimit)
- [ ] Implement CORS restrictions for specific domains
- [ ] Use environment variables for SECRET_KEY
- [ ] Add email verification link workflow
- [ ] Add SMS provider configuration (Twilio, SNS, etc.)
- [ ] Enable HTTPS-only for JWT cookies
- [ ] Add audit logging for auth events
- [ ] Implement password strength validation
- [ ] Add account lockout after failed attempts (django-axes)
- [ ] Implement email verification requirement before full access

### API Response Patterns

**Success (2xx):**
```json
{
  "user": { ... },
  "tokens": { "access": "...", "refresh": "..." },
  "message": "..."
}
```

**Error (4xx/5xx):**
```json
{
  "email": ["Email already registered."],
  "detail": "Invalid token."
}
```

### Related Models

- User (custom, email-based)
- Tenant (multi-tenant support)
- UserTenant (membership)
- Role (RBAC)
- OTPVerification (OTP storage)
- LoginHistory (audit trail)

---

**Author:** Copilot  
**Date:** 2026-06-16  
**Phase:** 1 - Authentication & Onboarding MVP
