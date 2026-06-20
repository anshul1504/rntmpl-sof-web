"""
JWT Authentication & OTP Tests
Comprehensive test cases for auth endpoints
"""
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from apps.accounts.models import Tenant, UserTenant, Role, OTPVerification
from apps.common.encryption import hash_otp

User = get_user_model()


class RegistrationTests(APITestCase):
    """Test user registration endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/v1/auth/register/'

    def test_register_valid_user(self):
        """Register new user with email and password."""
        data = {
            'email': 'newuser@example.com',
            'full_name': 'John Doe',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertEqual(response.data['user']['email'], 'newuser@example.com')
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_register_duplicate_email(self):
        """Cannot register with duplicate email."""
        User.objects.create_user(email='existing@example.com', password='Pass123')
        data = {
            'email': 'existing@example.com',
            'full_name': 'John Doe',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_register_password_mismatch(self):
        """Cannot register with mismatched passwords."""
        data = {
            'email': 'newuser@example.com',
            'full_name': 'John Doe',
            'password': 'SecurePass123!',
            'password_confirm': 'DifferentPass123!',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_register_returns_jwt_tokens(self):
        """Successful registration returns JWT tokens."""
        data = {
            'email': 'newuser@example.com',
            'full_name': 'John Doe',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])


class LoginTests(APITestCase):
    """Test user login endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.login_url = '/api/v1/auth/login/'
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='TestPass123!',
            full_name='Test User'
        )

    def test_login_valid_credentials(self):
        """Login with valid email and password."""
        data = {
            'email': 'testuser@example.com',
            'password': 'TestPass123!',
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])

    def test_login_invalid_password(self):
        """Cannot login with wrong password."""
        data = {
            'email': 'testuser@example.com',
            'password': 'WrongPassword!',
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_user(self):
        """Cannot login with non-existent email."""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'AnyPassword!',
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_inactive_user(self):
        """Cannot login with deactivated account."""
        self.user.is_active = False
        self.user.save()
        data = {
            'email': 'testuser@example.com',
            'password': 'TestPass123!',
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class OTPTests(APITestCase):
    """Test OTP request and verification endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.otp_request_url = '/api/v1/auth/otp/request/'
        self.otp_verify_url = '/api/v1/auth/otp/verify/'

    def test_request_otp_email(self):
        """Request OTP for email address."""
        data = {
            'email': 'user@example.com',
            'purpose': 'LOGIN',
        }
        response = self.client.post(self.otp_request_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('email', response.data)
        self.assertTrue(OTPVerification.objects.filter(email='user@example.com').exists())

    def test_request_otp_phone_fails(self):
        """Request OTP for phone number fails because only email is supported."""
        data = {
            'email': '+919876543210',  # Not a valid email
            'purpose': 'LOGIN',
        }
        response = self.client.post(self.otp_request_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_request_otp_invalid_email(self):
        """Cannot request OTP with invalid email."""
        data = {
            'email': 'notanemail',
            'purpose': 'LOGIN',
        }
        response = self.client.post(self.otp_request_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_otp_valid(self):
        """Verify valid OTP for new user."""
        # Generate OTP
        otp = '123456'
        email = 'newuser@example.com'
        otp_hash = hash_otp(otp, email)
        OTPVerification.objects.create(
            email=email,
            otp_hash=otp_hash,
            purpose=OTPVerification.OTPPurpose.LOGIN,
            expires_at=timezone.now() + timezone.timedelta(minutes=10),
        )

        # Verify OTP
        data = {
            'email': email,
            'otp': otp,
            'purpose': 'LOGIN',
        }
        response = self.client.post(self.otp_verify_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        # User should be created
        self.assertTrue(User.objects.filter(email=email).exists())

    def test_verify_otp_invalid(self):
        """Cannot verify invalid OTP."""
        email = 'user@example.com'
        otp_hash = hash_otp('123456', email)
        OTPVerification.objects.create(
            email=email,
            otp_hash=otp_hash,
            purpose=OTPVerification.OTPPurpose.LOGIN,
            expires_at=timezone.now() + timezone.timedelta(minutes=10),
        )

        data = {
            'email': email,
            'otp': '999999',  # Wrong OTP
            'purpose': 'LOGIN',
        }
        response = self.client.post(self.otp_verify_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_otp_expired(self):
        """Cannot verify expired OTP."""
        email = 'user@example.com'
        otp_hash = hash_otp('123456', email)
        OTPVerification.objects.create(
            email=email,
            otp_hash=otp_hash,
            purpose=OTPVerification.OTPPurpose.LOGIN,
            expires_at=timezone.now() - timezone.timedelta(minutes=1),  # Expired
        )

        data = {
            'email': email,
            'otp': '123456',
            'purpose': 'LOGIN',
        }
        response = self.client.post(self.otp_verify_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_otp_max_attempts(self):
        """OTP locked after 5 failed attempts."""
        email = 'user@example.com'
        otp_hash = hash_otp('123456', email)
        otp_record = OTPVerification.objects.create(
            email=email,
            otp_hash=otp_hash,
            purpose=OTPVerification.OTPPurpose.LOGIN,
            expires_at=timezone.now() + timezone.timedelta(minutes=10),
            attempts=4,  # One away from lock
        )

        data = {
            'email': email,
            'otp': '999999',  # Wrong OTP
            'purpose': 'LOGIN',
        }
        response = self.client.post(self.otp_verify_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Next attempt should fail immediately
        response = self.client.post(self.otp_verify_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class MeEndpointTests(APITestCase):
    """Test GET /api/auth/me/ endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.me_url = '/api/v1/auth/me/'
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='TestPass123!',
            full_name='Test User'
        )

    def test_me_authenticated(self):
        """Get current user details when authenticated."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)
        self.assertEqual(response.data['full_name'], self.user.full_name)

    def test_me_unauthenticated(self):
        """Cannot get /me without authentication."""
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TenantOnboardingTests(APITestCase):
    """Test tenant creation endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.onboard_url = '/api/v1/auth/onboard-tenant/'
        self.user = User.objects.create_user(
            email='organizer@example.com',
            password='TestPass123!',
            full_name='Test Organizer'
        )

    def test_create_tenant_authenticated(self):
        """Create tenant when authenticated."""
        self.client.force_authenticate(user=self.user)
        data = {
            'name': 'Mumbai Cricket Academy',
            'tenant_type': 'ACADEMY',
            'subdomain': 'mca',
            'primary_color': '#1a56db',
            'secondary_color': '#7c3aed',
        }
        response = self.client.post(self.onboard_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tenant', response.data)
        self.assertIn('membership', response.data)
        self.assertEqual(response.data['tenant']['name'], 'Mumbai Cricket Academy')
        self.assertEqual(response.data['membership']['role'], 'TENANT_ADMIN')
        self.assertTrue(response.data['membership']['is_primary'])

    def test_create_tenant_unauthenticated(self):
        """Cannot create tenant without authentication."""
        data = {
            'name': 'Mumbai Cricket Academy',
            'tenant_type': 'ACADEMY',
        }
        response = self.client.post(self.onboard_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_tenant_duplicate_subdomain(self):
        """Cannot create tenant with duplicate subdomain."""
        Tenant.objects.create(
            name='Existing Academy',
            tenant_type=Tenant.TenantType.ACADEMY,
            subdomain='mca'
        )
        self.client.force_authenticate(user=self.user)
        data = {
            'name': 'New Academy',
            'tenant_type': 'ACADEMY',
            'subdomain': 'mca',  # Already taken
        }
        response = self.client.post(self.onboard_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_tenant_admin_role_created(self):
        """Tenant admin role created and assigned."""
        self.client.force_authenticate(user=self.user)
        data = {
            'name': 'Mumbai Cricket Academy',
            'tenant_type': 'ACADEMY',
            'subdomain': 'mca',
        }
        response = self.client.post(self.onboard_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        tenant_id = response.data['tenant']['id']
        tenant = Tenant.objects.get(id=tenant_id)
        membership = UserTenant.objects.get(user=self.user, tenant=tenant)
        self.assertIsNotNone(membership.role)
        self.assertEqual(membership.role.code, 'TENANT_ADMIN')
        self.assertTrue(membership.is_primary)


class TokenRefreshTests(APITestCase):
    """Test token refresh endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.refresh_url = '/api/v1/auth/refresh/'
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='TestPass123!',
        )

    def test_refresh_valid_token(self):
        """Refresh token with valid refresh token."""
        # Get tokens from login
        login_response = self.client.post('/api/v1/auth/login/', {
            'email': 'testuser@example.com',
            'password': 'TestPass123!',
        })
        refresh_token = login_response.data['tokens']['refresh']

        # Refresh
        data = {'refresh': refresh_token}
        response = self.client.post(self.refresh_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_refresh_invalid_token(self):
        """Cannot refresh with invalid token."""
        data = {'refresh': 'invalid.token.here'}
        response = self.client.post(self.refresh_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


if __name__ == '__main__':
    import unittest
    unittest.main()
