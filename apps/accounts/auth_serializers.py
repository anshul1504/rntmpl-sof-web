"""
JWT Authentication Serializers
Register, Login, Token Refresh, OTP, Tenant Onboarding
"""
from django.contrib.auth import get_user_model, authenticate
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
import re

from apps.accounts.models import Tenant, UserTenant, Role, OTPVerification
from apps.common.encryption import hash_otp, verify_otp

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    """User registration with email and password."""
    email = serializers.EmailField(required=True)
    full_name = serializers.CharField(max_length=255, required=True)
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already registered.')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            password=validated_data['password'],
            user_type=User.UserType.FAN,
        )
        return user

    def to_representation(self, instance):
        """Return user with JWT tokens."""
        refresh = RefreshToken.for_user(instance)
        return {
            'user': UserDetailSerializer(instance).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        }


class LoginSerializer(serializers.Serializer):
    """Email/password login with JWT."""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError('Email and password required.')

        request = self.context.get('request')
        user = authenticate(request=request, username=email, password=password)
        if not user:
            raise serializers.ValidationError('Invalid email or password.')

        if not user.is_active:
            raise serializers.ValidationError('Account is deactivated.')

        attrs['user'] = user
        return attrs

    def to_representation(self, instance):
        user = instance.get('user')
        user.record_login(self.context['request'])
        refresh = RefreshToken.for_user(user)
        return {
            'user': UserDetailSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        }


class RefreshTokenSerializer(serializers.Serializer):
    """Refresh JWT access token."""
    refresh = serializers.CharField(required=True)

    def validate_refresh(self, value):
        try:
            RefreshToken(value)
        except TokenError as e:
            raise serializers.ValidationError(str(e))
        return value

    def to_representation(self, instance):
        refresh = RefreshToken(instance['refresh'])
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }


class OTPRequestSerializer(serializers.Serializer):
    """Request OTP via email only."""
    email = serializers.EmailField(required=True)
    purpose = serializers.ChoiceField(
        choices=OTPVerification.OTPPurpose.choices,
        default=OTPVerification.OTPPurpose.LOGIN
    )

    def validate_email(self, value):
        """Validate email format."""
        if not value or '@' not in value:
            raise serializers.ValidationError('Invalid email address.')
        return value

    def create(self, validated_data):
        """Generate OTP and send via email."""
        from apps.accounts.email_otp import EmailOTPService
        
        email = validated_data['email']
        purpose = validated_data['purpose']

        # Generate 6-digit OTP
        import random
        otp = str(random.randint(100000, 999999))

        # Hash for storage
        otp_hash = hash_otp(otp, email)
        
        # Create OTP record
        otp_record = OTPVerification.objects.create(
            email=email,
            otp_hash=otp_hash,
            purpose=purpose,
            expires_at=timezone.now() + timezone.timedelta(minutes=10),
            attempts=0,
        )

        # Send OTP via email
        success, message = EmailOTPService.send_otp(email, otp, purpose)
        
        if not success:
            otp_record.delete()
            raise serializers.ValidationError(f'Failed to send OTP: {message}')

        return {
            'email': email,
            'otp_record': otp_record,
        }

    def to_representation(self, instance):
        """Return success message with masked email."""
        email = instance['email']
        local, domain = email.split('@')
        masked = f"{local[:2]}***@{domain}"
        
        return {
            'message': 'OTP sent successfully to your email',
            'email': masked,
            'expires_in_seconds': 600,
        }


class OTPVerifySerializer(serializers.Serializer):
    """Verify OTP (email only) and create/login user."""
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, max_length=6, min_length=6)
    purpose = serializers.ChoiceField(
        choices=OTPVerification.OTPPurpose.choices,
        default=OTPVerification.OTPPurpose.LOGIN
    )

    def validate(self, attrs):
        email = attrs['email']
        otp = attrs['otp']
        purpose = attrs['purpose']

        # Find OTP record
        try:
            otp_record = OTPVerification.objects.get(
                email=email,
                purpose=purpose,
                expires_at__gt=timezone.now(),
            )
        except OTPVerification.DoesNotExist:
            raise serializers.ValidationError('OTP expired or not found.')

        # Check max attempts
        if otp_record.attempts >= 5:
            otp_record.expires_at = timezone.now()
            otp_record.save()
            raise serializers.ValidationError('Too many failed attempts. Request new OTP.')

        # Verify OTP
        if not verify_otp(otp, email, otp_record.otp_hash):
            otp_record.attempts += 1
            otp_record.save()
            raise serializers.ValidationError('Invalid OTP.')

        attrs['otp_record'] = otp_record
        attrs['email'] = email
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        """Get or create user, verify email."""
        email = validated_data['email']
        otp_record = validated_data['otp_record']

        # Find or create user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Create new user with OTP verification
            import random
            user = User.objects.create_user(
                email=email,
                full_name=email.split('@')[0],  # Use email prefix as name
            )
            user.set_unusable_password()

        # Mark email as verified
        user.email_verified = True
        user.is_verified = True
        user.save(update_fields=['email_verified', 'is_verified'])

        # Mark OTP as used
        otp_record.used_at = timezone.now()
        otp_record.save()

        return user

    def to_representation(self, instance):
        """Return user with JWT tokens."""
        refresh = RefreshToken.for_user(instance)
        return {
            'user': UserDetailSerializer(instance).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        }


class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed user information."""
    tenant_memberships = serializers.SerializerMethodField()
    primary_tenant = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'full_name',
            'user_type',
            'is_verified',
            'email_verified',
            'phone_verified',
            'is_2fa_enabled',
            'photo',
            'date_of_birth',
            'gender',
            'subscription_plan',
            'is_premium',
            'tenant_memberships',
            'primary_tenant',
        )
        read_only_fields = fields

    def get_tenant_memberships(self, obj):
        """Get all active tenants."""
        memberships = UserTenant.objects.filter(
            user=obj, is_active=True, tenant__is_deleted=False
        ).select_related('tenant', 'role')
        return UserTenantDetailSerializer(memberships, many=True).data

    def get_primary_tenant(self, obj):
        """Get primary tenant."""
        try:
            primary = UserTenant.objects.get(
                user=obj, is_primary=True, is_active=True, tenant__is_deleted=False
            )
            return UserTenantDetailSerializer(primary).data
        except UserTenant.DoesNotExist:
            return None


class UserTenantDetailSerializer(serializers.ModelSerializer):
    """User tenant membership with details."""
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    tenant_type = serializers.CharField(source='tenant.get_tenant_type_display', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True, allow_null=True)

    class Meta:
        from apps.accounts.models import UserTenant
        model = UserTenant
        fields = (
            'id',
            'tenant',
            'tenant_name',
            'tenant_type',
            'role_name',
            'is_primary',
            'is_active',
            'joined_at',
        )
        read_only_fields = fields


class TenantOnboardingSerializer(serializers.ModelSerializer):
    """Create organization/tenant during onboarding."""
    admin_role_id = serializers.IntegerField(required=False, write_only=True)

    class Meta:
        model = Tenant
        fields = (
            'name',
            'tenant_type',
            'domain',
            'subdomain',
            'primary_color',
            'secondary_color',
            'admin_role_id',
        )

    def validate_subdomain(self, value):
        if value and Tenant.objects.filter(subdomain=value, is_deleted=False).exists():
            raise serializers.ValidationError('Subdomain already taken.')
        return value

    def validate_domain(self, value):
        if value and Tenant.objects.filter(domain=value, is_deleted=False).exists():
            raise serializers.ValidationError('Domain already taken.')
        return value

    @transaction.atomic
    def create(self, validated_data):
        admin_role_id = validated_data.pop('admin_role_id', None)
        user = self.context['request'].user

        # Create tenant
        tenant = Tenant.objects.create(**validated_data)

        # Get or create TENANT_ADMIN role
        if admin_role_id:
            try:
                role = Role.objects.get(id=admin_role_id, tenant=tenant)
            except Role.DoesNotExist:
                role = Role.objects.create(
                    tenant=tenant,
                    name='Tenant Admin',
                    code='TENANT_ADMIN',
                    category=Role.RoleCategory.TENANT,
                    is_system=True,
                )
        else:
            role, _ = Role.objects.get_or_create(
                tenant=tenant,
                code='TENANT_ADMIN',
                defaults={
                    'name': 'Tenant Admin',
                    'category': Role.RoleCategory.TENANT,
                    'is_system': True,
                }
            )

        # Add creator as primary admin
        UserTenant.objects.create(
            user=user,
            tenant=tenant,
            role=role,
            is_primary=True,
            is_active=True,
        )

        return tenant

    def to_representation(self, instance):
        """Return tenant with membership details."""
        return {
            'tenant': TenantDetailSerializer(instance).data,
            'membership': {
                'role': 'TENANT_ADMIN',
                'is_primary': True,
                'joined_at': timezone.now().isoformat(),
            }
        }


class TenantDetailSerializer(serializers.ModelSerializer):
    """Tenant details for API."""
    tenant_type_display = serializers.CharField(source='get_tenant_type_display', read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = (
            'id',
            'name',
            'tenant_type',
            'tenant_type_display',
            'domain',
            'subdomain',
            'logo',
            'primary_color',
            'secondary_color',
            'is_public',
            'subscription_plan',
            'verified',
            'member_count',
            'created_at',
        )
        read_only_fields = fields

    def get_member_count(self, obj):
        """Count active members."""
        return obj.members.filter(is_active=True).count()
