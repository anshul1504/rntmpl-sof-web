"""
Base Models & Mixins for the entire Cricket Ecosystem Platform.
All models in the system inherit from these base classes.
"""
import uuid
import hashlib
import hmac
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.common.managers import ActiveManager, TenantScopedManager


def generate_uuid():
    return uuid.uuid4().hex[:12]


class TimestampMixin(models.Model):
    """Provides created_at and updated_at timestamps for all models."""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
    """Provides soft delete capability."""
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save()

    class Meta:
        abstract = True


class UUIDPrimaryKeyMixin(models.Model):
    """Provides UUID primary key instead of auto-increment."""
    id = models.CharField(
        primary_key=True,
        max_length=12,
        default=generate_uuid,
        editable=False,
    )

    class Meta:
        abstract = True


class AuditLogMixin(models.Model):
    """Tracks who created and last modified a record."""
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_updated",
    )

    class Meta:
        abstract = True


class StatusMixin(models.Model):
    """Provides common status field with choices."""
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'
        PENDING = 'PENDING', 'Pending'
        DRAFT = 'DRAFT', 'Draft'
        ARCHIVED = 'ARCHIVED', 'Archived'
        SUSPENDED = 'SUSPENDED', 'Suspended'
        CANCELLED = 'CANCELLED', 'Cancelled'
        COMPLETED = 'COMPLETED', 'Completed'
        DELETED = 'DELETED', 'Deleted'

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )

    class Meta:
        abstract = True


class IsActiveMixin(models.Model):
    """Simple active/inactive boolean."""
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        abstract = True


class OrderingMixin(models.Model):
    """Provides ordering/sequence field."""
    sequence = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        abstract = True
        ordering = ['sequence']


class EffectiveDateMixin(models.Model):
    """Provides effective date range."""
    effective_from = models.DateTimeField(default=timezone.now)
    effective_to = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True


class NoteMixin(models.Model):
    """Provides notes/description field."""
    notes = models.TextField(blank=True, default='')
    description = models.TextField(blank=True, default='')

    class Meta:
        abstract = True


class SlugMixin(models.Model):
    """Provides unique slug field."""
    slug = models.SlugField(max_length=200, unique=True, db_index=True)

    class Meta:
        abstract = True


class CodeMixin(models.Model):
    """Provides unique code field."""
    code = models.CharField(max_length=50, unique=True, db_index=True)

    class Meta:
        abstract = True


class IconImageMixin(models.Model):
    """Provides icon and image fields."""
    icon = models.CharField(max_length=50, blank=True, default='')
    image = models.ImageField(upload_to='images/', blank=True, null=True)

    class Meta:
        abstract = True


class AddressMixin(models.Model):
    """Provides full address fields."""
    address_line1 = models.CharField(max_length=255, blank=True, default='')
    address_line2 = models.CharField(max_length=255, blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='', db_index=True)
    state = models.CharField(max_length=100, blank=True, default='', db_index=True)
    district = models.CharField(max_length=100, blank=True, default='')
    pincode = models.CharField(max_length=10, blank=True, default='')
    country = models.CharField(max_length=100, default='India', db_index=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        abstract = True


class ContactMixin(models.Model):
    """Provides contact fields."""
    email = models.EmailField(blank=True, default='', db_index=True)
    phone = models.CharField(max_length=20, blank=True, default='', db_index=True)
    alternate_phone = models.CharField(max_length=20, blank=True, default='')
    website = models.URLField(blank=True, default='')

    class Meta:
        abstract = True


class ApprovalMixin(models.Model):
    """Provides approval workflow fields."""
    class ApprovalStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending Approval'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        HOLD = 'HOLD', 'On Hold'

    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
        db_index=True,
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_approvals',
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, default='')

    class Meta:
        abstract = True


class YearMixin(models.Model):
    """Provides year field."""
    year = models.PositiveIntegerField(
        default=timezone.now().year,
        db_index=True,
        validators=[MinValueValidator(2000), MaxValueValidator(2100)]
    )

    class Meta:
        abstract = True


class SeasonMixin(models.Model):
    """Provides season information."""
    class Season(models.TextChoices):
        SUMMER = 'SUMMER', 'Summer'
        WINTER = 'WINTER', 'Winter'
        MONSOON = 'MONSOON', 'Monsoon'
        SPRING = 'SPRING', 'Spring'
        AUTUMN = 'AUTUMN', 'Autumn'
        ALL_YEAR = 'ALL_YEAR', 'All Year'

    season = models.CharField(
        max_length=20,
        choices=Season.choices,
        default=Season.ALL_YEAR,
    )

    class Meta:
        abstract = True


class BaseModel(TimestampMixin, SoftDeleteMixin, UUIDPrimaryKeyMixin, AuditLogMixin, StatusMixin):
    """
    Base model for all models in the system.
    Combines UUID PK, timestamps, soft delete, audit logging, and status.
    """
    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True
        default_manager_name = 'objects'


class TenantOwnedModel(BaseModel):
    """Base class for records that must be scoped to a tenant."""
    tenant = models.ForeignKey(
        'accounts.Tenant',
        on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)s_records',
        db_index=True,
    )

    class Meta:
        abstract = True


class NamedModel(BaseModel, NoteMixin, IconImageMixin):
    """Base model with name."""
    name = models.CharField(max_length=255, db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        abstract = True


class CodedNamedModel(NamedModel, CodeMixin, SlugMixin):
    """Base model with name, code, and slug."""

    class Meta:
        abstract = True


class AddressModel(NamedModel, AddressMixin, ContactMixin):
    """Base model with name, address, and contact info."""

    class Meta:
        abstract = True


# Utility functions
def generate_otp():
    """Generate a 6-digit OTP."""
    import random
    return str(random.randint(100000, 999999))


def generate_invoice_number(prefix='INV'):
    """Generate unique invoice number."""
    import time
    return f"{prefix}-{int(time.time())}-{generate_uuid().upper()}"


def generate_reference_id(prefix='REF'):
    """Generate unique reference ID."""
    return f"{prefix}-{generate_uuid().upper()}"
