"""
Accounts & Authentication Models
User model, Tenant system, Roles, Permissions, Sessions, Devices
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

from apps.common.models import (
    BaseModel, NamedModel, AddressMixin, ContactMixin, TimestampMixin,
    SoftDeleteMixin, generate_uuid, ActiveManager
)


class UserManager(BaseUserManager):
    """Custom user manager with email as identifier."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', User.UserType.SUPER_ADMIN)
        extra_fields.setdefault('is_verified', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser, ContactMixin, AddressMixin):
    """
    Custom User Model - Central to the entire ecosystem.
    Supports all 19+ user roles defined in the platform.
    """

    class UserType(models.TextChoices):
        SUPER_ADMIN = 'SUPER_ADMIN', 'Super Admin'
        PLATFORM_ADMIN = 'PLATFORM_ADMIN', 'Platform Admin'
        ASSOCIATION_ADMIN = 'ASSOCIATION_ADMIN', 'Association Admin'
        TOURNAMENT_DIRECTOR = 'TOURNAMENT_DIRECTOR', 'Tournament Director'
        LEAGUE_MANAGER = 'LEAGUE_MANAGER', 'League Manager'
        ACADEMY_MANAGER = 'ACADEMY_MANAGER', 'Academy Manager'
        TEAM_OWNER = 'TEAM_OWNER', 'Team Owner'
        TEAM_MANAGER = 'TEAM_MANAGER', 'Team Manager'
        COACH = 'COACH', 'Coach'
        SELECTOR = 'SELECTOR', 'Selector'
        PLAYER = 'PLAYER', 'Player'
        SCORER = 'SCORER', 'Scorer'
        UMPIRE = 'UMPIRE', 'Umpire'
        MATCH_REFEREE = 'MATCH_REFEREE', 'Match Referee'
        COMMENTATOR = 'COMMENTATOR', 'Commentator'
        SPONSOR = 'SPONSOR', 'Sponsor'
        FAN = 'FAN', 'Fan'
        MEDIA_MANAGER = 'MEDIA_MANAGER', 'Media Manager'
        FINANCE_MANAGER = 'FINANCE_MANAGER', 'Finance Manager'

    class Gender(models.TextChoices):
        MALE = 'M', 'Male'
        FEMALE = 'F', 'Female'
        OTHER = 'O', 'Other'

    class OnboardingState(models.TextChoices):
        GUEST = 'GUEST', 'Guest'
        PLAYER_PAYMENT_PENDING = 'PLAYER_PAYMENT_PENDING', 'Player Payment Pending'
        PLAYER_TRIAL_ELIGIBLE = 'PLAYER_TRIAL_ELIGIBLE', 'Trial Eligible'
        PLAYER_SELECTED = 'PLAYER_SELECTED', 'Selected Player'

    username = models.CharField(
        max_length=150, unique=True, blank=True, null=True,
        help_text='Optional username'
    )
    email = models.EmailField(unique=True, db_index=True)
    full_name = models.CharField(max_length=255, blank=True, default='')
    user_type = models.CharField(
        max_length=30, choices=UserType.choices,
        default=UserType.FAN, db_index=True
    )
    onboarding_state = models.CharField(
        max_length=40,
        choices=OnboardingState.choices,
        default=OnboardingState.GUEST,
        db_index=True,
    )
    gender = models.CharField(
        max_length=2, choices=Gender.choices, blank=True, default=''
    )
    date_of_birth = models.DateField(null=True, blank=True)
    photo = models.ImageField(upload_to='users/photos/', blank=True, null=True)

    # Verification
    is_verified = models.BooleanField(default=False, db_index=True)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    is_2fa_enabled = models.BooleanField(default=False)
    two_factor_method = models.CharField(
        max_length=20, blank=True, default='',
        choices=[('APP', 'Authenticator App'), ('SMS', 'SMS'), ('EMAIL', 'Email')]
    )

    # Aadhaar/PAN Verification (encrypted at rest, masked on display)
    aadhaar_number_encrypted = models.TextField(blank=True, default='')
    aadhaar_number_hash = models.CharField(max_length=64, blank=True, default='', db_index=True)
    aadhaar_verified = models.BooleanField(default=False)
    pan_number_encrypted = models.TextField(blank=True, default='')
    pan_number_hash = models.CharField(max_length=64, blank=True, default='', db_index=True)
    pan_verified = models.BooleanField(default=False)

    # Device & Security
    last_login_ip = models.CharField(max_length=45, blank=True, default='')
    last_login_device = models.TextField(blank=True, default='')
    login_attempts = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    locked_until = models.DateTimeField(null=True, blank=True)
    last_password_change = models.DateTimeField(null=True, blank=True)
    password_expiry_days = models.IntegerField(default=90)

    # Social Auth
    google_id = models.CharField(max_length=255, blank=True, default='', db_index=True)
    facebook_id = models.CharField(max_length=255, blank=True, default='', db_index=True)

    # Subscription
    subscription_plan = models.CharField(max_length=50, blank=True, default='free')
    subscription_end = models.DateTimeField(null=True, blank=True)

    # Meta
    metadata = models.JSONField(default=dict, blank=True)
    preferences = models.JSONField(default=dict, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        db_table = 'accounts_users'
        indexes = [
            models.Index(fields=['email', 'user_type']),
            models.Index(fields=['user_type', 'is_verified']),
            models.Index(fields=['is_active', 'is_verified']),
        ]

    def __str__(self):
        return self.full_name or self.email

    def save(self, *args, **kwargs):
        if not self.full_name:
            self.full_name = self.email.split('@')[0]
        if not self.username:
            self.username = self.email.split('@')[0]
        super().save(*args, **kwargs)

    def record_login(self, request):
        """Record login details."""
        self.last_login = timezone.now()
        self.last_login_ip = self._get_client_ip(request)
        self.last_login_device = request.META.get('HTTP_USER_AGENT', '')[:500]
        self.login_attempts = 0
        self.save(update_fields=['last_login', 'last_login_ip', 'last_login_device', 'login_attempts'])

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')

    @property
    def is_premium(self):
        return self.subscription_plan != 'free' and self.subscription_end and self.subscription_end > timezone.now()


class Tenant(NamedModel, AddressMixin, ContactMixin):
    """
    Multi-Tenant Model.
    Supports: Association, Academy, League, Tournament, Franchise, Corporate Organization
    Each tenant has data isolation.
    """

    class TenantType(models.TextChoices):
        ASSOCIATION = 'ASSOCIATION', 'Association'
        ACADEMY = 'ACADEMY', 'Academy'
        LEAGUE = 'LEAGUE', 'League'
        TOURNAMENT = 'TOURNAMENT', 'Tournament'
        FRANCHISE = 'FRANCHISE', 'Franchise'
        CORPORATE = 'CORPORATE', 'Corporate Organization'

    tenant_type = models.CharField(
        max_length=20, choices=TenantType.choices, db_index=True
    )
    domain = models.CharField(max_length=255, blank=True, default=None, unique=True, null=True)
    subdomain = models.CharField(max_length=100, blank=True, default=None, unique=True, null=True)
    logo = models.ImageField(upload_to='tenants/logos/', blank=True, null=True)
    favicon = models.ImageField(upload_to='tenants/favicons/', blank=True, null=True)
    primary_color = models.CharField(max_length=7, default='#1a56db', help_text='Primary brand color (hex)')
    secondary_color = models.CharField(max_length=7, default='#7c3aed', help_text='Secondary brand color (hex)')
    custom_css = models.TextField(blank=True, default='')
    is_public = models.BooleanField(default=True)
    max_users = models.IntegerField(default=100)
    max_teams = models.IntegerField(default=50)
    storage_limit_mb = models.IntegerField(default=500)
    subscription_plan = models.CharField(max_length=50, default='free')
    subscription_start = models.DateTimeField(null=True, blank=True)
    subscription_end = models.DateTimeField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'
        db_table = 'accounts_tenants'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_tenant_type_display()})"


class UserTenant(models.Model):
    """Maps users to tenants with specific roles."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='tenant_memberships'
    )
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name='members'
    )
    role = models.ForeignKey('Role', on_delete=models.SET_NULL, null=True, blank=True)
    is_primary = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'User Tenant'
        verbose_name_plural = 'User Tenants'
        db_table = 'accounts_user_tenants'
        unique_together = [['user', 'tenant']]
        indexes = [
            models.Index(fields=['user', 'tenant', 'is_active']),
        ]

    def __str__(self):
        return f"{self.user.email} @ {self.tenant.name}"


class Role(TimestampMixin):
    """Role-Based Access Control - Custom roles per tenant."""
    class RoleCategory(models.TextChoices):
        PLATFORM = 'PLATFORM', 'Platform'
        TENANT = 'TENANT', 'Tenant'
        TOURNAMENT = 'TOURNAMENT', 'Tournament'
        TEAM = 'TEAM', 'Team'

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, null=True, blank=True,
        related_name='roles', help_text='Tenant scope; NULL = platform-wide role.'
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, db_index=True)
    category = models.CharField(max_length=20, choices=RoleCategory.choices, default=RoleCategory.TENANT)
    description = models.TextField(blank=True, default='')
    is_system = models.BooleanField(default=False, help_text='System-defined roles cannot be deleted')
    permissions = models.ManyToManyField(
        Permission, blank=True, related_name='custom_roles'
    )

    class Meta:
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'
        db_table = 'accounts_roles'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['code', 'tenant'],
                name='unique_role_code_per_tenant',
            ),
        ]

    def __str__(self):
        if self.tenant:
            return f"{self.name} ({self.tenant.name})"
        return self.name


class PermissionMatrix(TimestampMixin):
    """
    Granular permission matrix for fine-grained access control.
    Allows per-feature permissions on specific models/actions.
    """
    class Action(models.TextChoices):
        CREATE = 'CREATE', 'Create'
        READ = 'READ', 'Read'
        UPDATE = 'UPDATE', 'Update'
        DELETE = 'DELETE', 'Delete'
        APPROVE = 'APPROVE', 'Approve'
        EXPORT = 'EXPORT', 'Export'
        IMPORT = 'IMPORT', 'Import'

    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='permission_matrix')
    content_type_model = models.CharField(max_length=100, db_index=True)
    action = models.CharField(max_length=20, choices=Action.choices)
    is_allowed = models.BooleanField(default=True)
    conditions = models.JSONField(default=dict, blank=True, help_text='JSON conditions for dynamic permissions')

    class Meta:
        verbose_name = 'Permission Matrix'
        verbose_name_plural = 'Permission Matrices'
        db_table = 'accounts_permission_matrix'
        unique_together = [['role', 'content_type_model', 'action']]

    def __str__(self):
        return f"{self.role.name} - {self.content_type_model} - {self.action}"


class LoginHistory(TimestampMixin):
    """Tracks all login attempts for audit and security."""
    class LoginStatus(models.TextChoices):
        SUCCESS = 'SUCCESS', 'Success'
        FAILED = 'FAILED', 'Failed'
        LOCKED = 'LOCKED', 'Account Locked'
        OTP_REQUIRED = 'OTP_REQUIRED', 'OTP Required'

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='login_history'
    )
    ip_address = models.CharField(max_length=45)
    user_agent = models.TextField(blank=True, default='')
    device_type = models.CharField(max_length=50, blank=True, default='')
    device_name = models.CharField(max_length=255, blank=True, default='')
    location = models.CharField(max_length=255, blank=True, default='')
    status = models.CharField(max_length=20, choices=LoginStatus.choices)
    failure_reason = models.CharField(max_length=255, blank=True, default='')
    session_key = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        verbose_name = 'Login History'
        verbose_name_plural = 'Login History'
        db_table = 'accounts_login_history'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['ip_address', 'status']),
        ]


class UserSession(TimestampMixin):
    """Active user sessions management."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sessions'
    )
    session_key = models.CharField(max_length=255, unique=True, db_index=True)
    ip_address = models.CharField(max_length=45, blank=True, default='')
    user_agent = models.TextField(blank=True, default='')
    device_info = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    jwt_token = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'
        db_table = 'accounts_sessions'
        indexes = [
            models.Index(fields=['user', 'is_active', 'last_activity']),
        ]

    def __str__(self):
        return f"Session for {self.user.email} - {self.ip_address}"


class UserDevice(TimestampMixin):
    """Track user devices for security and notifications."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='devices'
    )
    device_id = models.CharField(max_length=255, db_index=True)
    device_type = models.CharField(max_length=50)
    device_name = models.CharField(max_length=255, blank=True, default='')
    platform = models.CharField(max_length=50, blank=True, default='')
    os_version = models.CharField(max_length=50, blank=True, default='')
    browser = models.CharField(max_length=100, blank=True, default='')
    browser_version = models.CharField(max_length=50, blank=True, default='')
    push_token = models.TextField(blank=True, default='', help_text='Firebase push token')
    is_trusted = models.BooleanField(default=False)
    last_used_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    fcm_token = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'User Device'
        verbose_name_plural = 'User Devices'
        db_table = 'accounts_devices'
        unique_together = [['user', 'device_id']]

    def __str__(self):
        return f"{self.device_name} ({self.device_type}) - {self.user.email}"


class OTPVerification(TimestampMixin):
    """OTP storage and verification. OTPs are stored as salted SHA-256 hashes
    so raw codes are never persisted in plaintext."""

    class OTPPurpose(models.TextChoices):
        LOGIN = 'LOGIN', 'Login'
        REGISTRATION = 'REGISTRATION', 'Registration'
        PASSWORD_RESET = 'PASSWORD_RESET', 'Password Reset'
        EMAIL_VERIFY = 'EMAIL_VERIFY', 'Email Verification'
        PHONE_VERIFY = 'PHONE_VERIFY', 'Phone Verification'
        TWO_FA = 'TWO_FA', 'Two Factor Authentication'

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name='otps'
    )
    email = models.EmailField(blank=True, default='')
    phone = models.CharField(max_length=20, blank=True, default='')
    otp_hash = models.CharField(max_length=64)
    purpose = models.CharField(max_length=20, choices=OTPPurpose.choices)
    is_used = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    expires_at = models.DateTimeField()
    ip_address = models.CharField(max_length=45, blank=True, default='')

    class Meta:
        verbose_name = 'OTP Verification'
        verbose_name_plural = 'OTP Verifications'
        db_table = 'accounts_otp'
        indexes = [
            models.Index(fields=['email', 'purpose', 'is_used']),
            models.Index(fields=['phone', 'purpose']),
        ]

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired and self.attempts < self.max_attempts

    @classmethod
    def generate_and_verify(cls, candidate_otp, email_or_phone, purpose, max_age_minutes=10):
        """Verify an OTP against stored hashed records."""
        from apps.common.encryption import verify_otp
        records = cls.objects.filter(
            models.Q(email=email_or_phone) | models.Q(phone=email_or_phone),
            purpose=purpose,
            is_used=False,
            expires_at__gt=timezone.now(),
        ).order_by('-created_at')

        for record in records:
            if record.attempts >= record.max_attempts:
                continue
            if verify_otp(candidate_otp, email_or_phone, record.otp_hash):
                record.is_used = True
                record.save(update_fields=['is_used'])
                return True, None
            record.attempts = models.F('attempts') + 1
            record.save(update_fields=['attempts'])
        return False, 'No valid OTP found or maximum attempts exceeded.'


class UserActivityLog(BaseModel):
    """Comprehensive audit log for all user actions."""
    class ActivityType(models.TextChoices):
        LOGIN = 'LOGIN', 'Login'
        LOGOUT = 'LOGOUT', 'Logout'
        CREATE = 'CREATE', 'Create'
        UPDATE = 'UPDATE', 'Update'
        DELETE = 'DELETE', 'Delete'
        VIEW = 'VIEW', 'View'
        EXPORT = 'EXPORT', 'Export'
        DOWNLOAD = 'DOWNLOAD', 'Download'
        PAYMENT = 'PAYMENT', 'Payment'
        SETTINGS = 'SETTINGS', 'Settings Change'

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_logs'
    )
    tenant = models.ForeignKey(
        Tenant, on_delete=models.SET_NULL, null=True, blank=True
    )
    activity_type = models.CharField(max_length=20, choices=ActivityType.choices, db_index=True)
    action = models.CharField(max_length=255, db_index=True, help_text='Description of action performed')
    model_name = models.CharField(max_length=100, blank=True, default='')
    object_id = models.CharField(max_length=50, blank=True, default='')
    object_repr = models.CharField(max_length=255, blank=True, default='')
    ip_address = models.CharField(max_length=45, blank=True, default='')
    user_agent = models.TextField(blank=True, default='')
    request_method = models.CharField(max_length=10, blank=True, default='')
    request_path = models.CharField(max_length=500, blank=True, default='')
    data_before = models.JSONField(default=dict, blank=True, null=True)
    data_after = models.JSONField(default=dict, blank=True, null=True)
    is_successful = models.BooleanField(default=True)
    duration_ms = models.IntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'User Activity Log'
        verbose_name_plural = 'User Activity Logs'
        db_table = 'accounts_activity_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['activity_type', 'created_at']),
            models.Index(fields=['tenant', 'activity_type']),
            models.Index(fields=['model_name', 'object_id']),
        ]

    def __str__(self):
        return f"{self.user} - {self.activity_type} - {self.action}"


class UserAddress(models.Model):
    """Additional user addresses (home, work, etc.)."""
    class AddressType(models.TextChoices):
        HOME = 'HOME', 'Home'
        WORK = 'WORK', 'Work'
        OTHER = 'OTHER', 'Other'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=10, choices=AddressType.choices, default=AddressType.HOME)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, default='')
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    district = models.CharField(max_length=100, blank=True, default='')
    pincode = models.CharField(max_length=10)
    country = models.CharField(max_length=100, default='India')
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'User Address'
        verbose_name_plural = 'User Addresses'
        db_table = 'accounts_user_addresses'

    def __str__(self):
        return f"{self.address_type}: {self.city}, {self.state}"


class UserDocument(models.Model):
    """User uploaded documents (ID proofs, certificates)."""
    class DocumentType(models.TextChoices):
        AADHAAR = 'AADHAAR', 'Aadhaar Card'
        PAN = 'PAN', 'PAN Card'
        PASSPORT = 'PASSPORT', 'Passport'
        VOTER_ID = 'VOTER_ID', 'Voter ID'
        DRIVING_LICENSE = 'DRIVING_LICENSE', 'Driving License'
        CERTIFICATE = 'CERTIFICATE', 'Certificate'
        OTHER = 'OTHER', 'Other'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DocumentType.choices)
    document_number = models.CharField(max_length=100, blank=True, default='')
    file = models.FileField(upload_to='users/documents/')
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_documents'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'User Document'
        verbose_name_plural = 'User Documents'
        db_table = 'accounts_user_documents'

    def __str__(self):
        return f"{self.user.email} - {self.get_document_type_display()}"


class OrganizationPlan(TimestampMixin):
    """Commercial SaaS plan used for organizer onboarding and tenant limits."""

    class BillingCycle(models.TextChoices):
        FREE = 'FREE', 'Free'
        MONTHLY = 'MONTHLY', 'Monthly'
        YEARLY = 'YEARLY', 'Yearly'

    name = models.CharField(max_length=120)
    code = models.SlugField(unique=True)
    description = models.TextField(blank=True, default='')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    billing_cycle = models.CharField(
        max_length=20,
        choices=BillingCycle.choices,
        default=BillingCycle.FREE,
        db_index=True,
    )
    max_tournaments = models.PositiveIntegerField(default=1)
    max_teams = models.PositiveIntegerField(default=8)
    max_players = models.PositiveIntegerField(default=120)
    max_venues = models.PositiveIntegerField(default=2)
    max_users = models.PositiveIntegerField(default=5)
    storage_limit_mb = models.PositiveIntegerField(default=500)
    trial_days = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Organization Plan'
        verbose_name_plural = 'Organization Plans'
        ordering = ['sort_order', 'price', 'name']

    def __str__(self):
        return self.name


class OrganizerApplication(TimestampMixin):
    """Public organizer SaaS signup request before tenant provisioning."""

    class Status(models.TextChoices):
        SUBMITTED = 'SUBMITTED', 'Submitted'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        PROVISIONED = 'PROVISIONED', 'Provisioned'
        SUSPENDED = 'SUSPENDED', 'Suspended'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='organizer_applications',
    )
    plan = models.ForeignKey(
        OrganizationPlan,
        on_delete=models.PROTECT,
        related_name='organizer_applications',
    )
    tenant = models.OneToOneField(
        Tenant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='organizer_application',
    )
    organization_name = models.CharField(max_length=180)
    tenant_type = models.CharField(
        max_length=20,
        choices=Tenant.TenantType.choices,
        default=Tenant.TenantType.LEAGUE,
    )
    contact_person = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    city = models.CharField(max_length=100, blank=True, default='')
    state = models.CharField(max_length=100, blank=True, default='')
    expected_teams = models.PositiveIntegerField(default=0)
    expected_players = models.PositiveIntegerField(default=0)
    message = models.TextField(blank=True, default='')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SUBMITTED,
        db_index=True,
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_organizer_applications',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.CharField(max_length=255, blank=True, default='')
    provisioned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Organizer Application'
        verbose_name_plural = 'Organizer Applications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['email', 'status']),
        ]

    def __str__(self):
        return f'{self.organization_name} - {self.get_status_display()}'


class OrganizationSubscription(TimestampMixin):
    """Active commercial subscription attached to a provisioned tenant."""

    class Status(models.TextChoices):
        TRIALING = 'TRIALING', 'Trialing'
        ACTIVE = 'ACTIVE', 'Active'
        PAST_DUE = 'PAST_DUE', 'Past Due'
        SUSPENDED = 'SUSPENDED', 'Suspended'
        CANCELLED = 'CANCELLED', 'Cancelled'

    tenant = models.OneToOneField(
        Tenant,
        on_delete=models.CASCADE,
        related_name='organization_subscription',
    )
    plan = models.ForeignKey(
        OrganizationPlan,
        on_delete=models.PROTECT,
        related_name='subscriptions',
    )
    organizer_application = models.OneToOneField(
        OrganizerApplication,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subscription',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    suspended_at = models.DateTimeField(null=True, blank=True)
    suspension_reason = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        verbose_name = 'Organization Subscription'
        verbose_name_plural = 'Organization Subscriptions'
        ordering = ['-current_period_start']
        indexes = [
            models.Index(fields=['status', 'current_period_end']),
        ]

    def __str__(self):
        return f'{self.tenant.name} - {self.plan.name} ({self.get_status_display()})'


class PaymentLedger(TimestampMixin):
    """Generic payment ledger for organizer plans and player registrations."""

    class Purpose(models.TextChoices):
        PLAYER_REGISTRATION = 'PLAYER_REGISTRATION', 'Player Registration'
        ORGANIZER_PLAN = 'ORGANIZER_PLAN', 'Organizer Plan'

    class Provider(models.TextChoices):
        MANUAL = 'MANUAL', 'Manual'
        RAZORPAY = 'RAZORPAY', 'Razorpay'

    class Status(models.TextChoices):
        CREATED = 'CREATED', 'Created'
        PENDING = 'PENDING', 'Pending'
        PAID = 'PAID', 'Paid'
        FAILED = 'FAILED', 'Failed'
        REFUNDED = 'REFUNDED', 'Refunded'
        CANCELLED = 'CANCELLED', 'Cancelled'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_ledger')
    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_ledger')
    organizer_application = models.ForeignKey(
        OrganizerApplication,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payment_ledger',
    )
    purpose = models.CharField(max_length=30, choices=Purpose.choices, db_index=True)
    provider = models.CharField(max_length=20, choices=Provider.choices, default=Provider.MANUAL, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CREATED, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    reference = models.CharField(max_length=140, unique=True, db_index=True)
    gateway_order_id = models.CharField(max_length=120, blank=True, default='', db_index=True)
    gateway_payment_id = models.CharField(max_length=120, blank=True, default='', db_index=True)
    gateway_payload = models.JSONField(default=dict, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        verbose_name = 'Payment Ledger'
        verbose_name_plural = 'Payment Ledger'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['purpose', 'status']),
            models.Index(fields=['provider', 'gateway_order_id']),
        ]

    def __str__(self):
        return f'{self.reference} - {self.get_status_display()}'


class PaymentReceipt(TimestampMixin):
    """Immutable receipt/invoice-style record generated after confirmed payment."""

    payment = models.OneToOneField(
        PaymentLedger,
        on_delete=models.CASCADE,
        related_name='receipt',
    )
    receipt_number = models.CharField(max_length=40, unique=True, db_index=True)
    issued_at = models.DateTimeField(default=timezone.now)
    billed_to_name = models.CharField(max_length=180)
    billed_to_email = models.EmailField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'Payment Receipt'
        verbose_name_plural = 'Payment Receipts'
        ordering = ['-issued_at']

    def __str__(self):
        return self.receipt_number


class PaymentReconciliation(TimestampMixin):
    """Operational reconciliation/audit state for a payment ledger item."""

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        MATCHED = 'MATCHED', 'Matched'
        MISMATCHED = 'MISMATCHED', 'Mismatched'
        REFUNDED = 'REFUNDED', 'Refunded'
        DISPUTED = 'DISPUTED', 'Disputed'

    payment = models.OneToOneField(
        PaymentLedger,
        on_delete=models.CASCADE,
        related_name='reconciliation',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    gateway_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    gateway_currency = models.CharField(max_length=3, blank=True, default='')
    gateway_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gateway_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reconciled_at = models.DateTimeField(null=True, blank=True)
    reconciled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reconciled_payments',
    )
    notes = models.TextField(blank=True, default='')
    gateway_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'Payment Reconciliation'
        verbose_name_plural = 'Payment Reconciliations'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.payment.reference} - {self.get_status_display()}'


class PaymentWebhookEvent(TimestampMixin):
    """Idempotent payment gateway event log."""

    provider = models.CharField(max_length=20, default=PaymentLedger.Provider.RAZORPAY, db_index=True)
    event_id = models.CharField(max_length=140, unique=True, db_index=True)
    event_type = models.CharField(max_length=120, db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    signature = models.CharField(max_length=255, blank=True, default='')
    is_valid = models.BooleanField(default=False, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processing_error = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'Payment Webhook Event'
        verbose_name_plural = 'Payment Webhook Events'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.provider}:{self.event_type}:{self.event_id}'


class NotificationOutbox(TimestampMixin):
    """Durable outbox for business notifications across email/SMS/WhatsApp."""

    class Channel(models.TextChoices):
        EMAIL = 'EMAIL', 'Email'
        SMS = 'SMS', 'SMS'
        WHATSAPP = 'WHATSAPP', 'WhatsApp'
        IN_APP = 'IN_APP', 'In App'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SENT = 'SENT', 'Sent'
        FAILED = 'FAILED', 'Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    event_type = models.CharField(max_length=80, db_index=True)
    channel = models.CharField(max_length=20, choices=Channel.choices, default=Channel.EMAIL, db_index=True)
    recipient = models.CharField(max_length=255)
    subject = models.CharField(max_length=180, blank=True, default='')
    body = models.TextField(blank=True, default='')
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    next_attempt_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'Notification Outbox'
        verbose_name_plural = 'Notification Outbox'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', 'status']),
            models.Index(fields=['channel', 'status']),
        ]

    def clean(self):
        if not self.recipient:
            raise ValidationError('Notification recipient is required.')

    def __str__(self):
        return f'{self.event_type} -> {self.recipient}'
