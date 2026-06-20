"""
Accounts & Authentication Forms
Login, Registration, OTP, Profile, Tenant management
"""
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.models import User, Tenant, OTPVerification, UserTenant, Role
from apps.accounts.policies import ROLE_PRESETS
from apps.common.encryption import hash_otp


class LoginForm(forms.Form):
    """Email/password login with rate-limit aware validation."""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email',
            'autocomplete': 'email',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
        })
    )
    remember_me = forms.BooleanField(required=False, initial=False)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get('email')
        password = cleaned.get('password')
        if email and password:
            user = authenticate(request=self.request, email=email, password=password)
            if user is None:
                raise ValidationError('Invalid email or password.')
            if not user.is_active:
                raise ValidationError('This account is inactive. Contact support.')
            cleaned['user'] = user
        return cleaned

    def get_user(self):
        """Required by Django's LoginView.form_valid() to get the authenticated user."""
        return self.cleaned_data.get('user')


class RegisterForm(UserCreationForm):
    """User registration with full_name and phone."""
    full_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Full name',
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email address',
            'autocomplete': 'email',
        })
    )
    phone = forms.CharField(
        max_length=20, required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone number (optional)',
        })
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a password (min 8 chars)',
            'autocomplete': 'new-password',
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password',
            'autocomplete': 'new-password',
        })
    )

    class Meta:
        model = User
        fields = ('full_name', 'email', 'phone', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.full_name = self.cleaned_data['full_name']
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data.get('phone', '')
        user.username = self.cleaned_data['email'].split('@')[0]
        if commit:
            user.save()
        return user


class OTPRequestForm(forms.Form):
    """Request an OTP for login/verification."""
    email_or_phone = forms.CharField(
        label='Email or Phone',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email or phone number',
        })
    )
    purpose = forms.ChoiceField(
        choices=OTPVerification.OTPPurpose.choices,
        widget=forms.HiddenInput(),
        initial=OTPVerification.OTPPurpose.LOGIN,
    )


class OTPVerifyForm(forms.Form):
    """Verify an OTP code."""
    email_or_phone = forms.CharField(widget=forms.HiddenInput())
    otp = forms.CharField(
        max_length=6, min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 6-digit OTP',
            'autocomplete': 'one-time-code',
            'inputmode': 'numeric',
            'pattern': '[0-9]{6}',
        })
    )
    purpose = forms.ChoiceField(
        choices=OTPVerification.OTPPurpose.choices,
        widget=forms.HiddenInput(),
    )


class TwoFactorForm(forms.Form):
    """TOTP token verification form."""
    token = forms.CharField(
        max_length=6, min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 6-digit authenticator code',
            'autocomplete': 'one-time-code',
            'inputmode': 'numeric',
        })
    )


class ProfileForm(UserChangeForm):
    """User profile editing form."""
    password = None  # Remove password field from profile editing

    class Meta:
        model = User
        fields = (
            'full_name', 'username', 'phone', 'alternate_phone',
            'date_of_birth', 'gender', 'user_type',
            'photo', 'website',
            'address_line1', 'address_line2',
            'city', 'district', 'state', 'pincode', 'country',
        )
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your full name'}),
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a username'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Primary phone number'}),
            'alternate_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Alternate phone number'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'user_type': forms.Select(attrs={'class': 'form-select'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://yourwebsite.com'}),
            'address_line1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'House no, Street, Locality'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Landmark, Area'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'district': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'District'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PIN Code'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),
        }


class TenantCreateForm(forms.ModelForm):
    """Create a new tenant (association, academy, league, etc.)."""
    class Meta:
        model = Tenant
        fields = (
            'name', 'tenant_type', 'domain', 'subdomain',
            'email', 'phone', 'address_line1', 'address_line2',
            'city', 'state', 'pincode', 'country',
            'primary_color', 'secondary_color',
        )
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Organization name'}),
            'tenant_type': forms.Select(attrs={'class': 'form-select'}),
            'domain': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Custom domain (optional)'}),
            'subdomain': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subdomain (e.g., myleague)'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Contact email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact phone'}),
            'address_line1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pincode'}),
            'primary_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'secondary_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
        }

    def clean_subdomain(self):
        subdomain = self.cleaned_data.get('subdomain')
        if subdomain:
            if Tenant.objects.filter(subdomain__iexact=subdomain).exists():
                raise ValidationError('This subdomain is already taken.')
            if not subdomain.isalnum() and '-' not in subdomain:
                raise ValidationError('Subdomain can only contain letters, numbers, and hyphens.')
        return subdomain.lower() if subdomain else ''


class RoleForm(forms.ModelForm):
    code = forms.ChoiceField(choices=[])

    class Meta:
        model = Role
        fields = ('code', 'name', 'description')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.tenant = tenant
        choices = [(code, name) for code, (name, _) in ROLE_PRESETS.items()]
        if self.instance.pk:
            choices = [(self.instance.code, self.instance.name)]
            self.fields['code'].disabled = True
        self.fields['code'].choices = choices
        self.fields['code'].widget.attrs['class'] = 'form-select'

    def clean_code(self):
        code = self.cleaned_data['code']
        duplicate = Role.objects.filter(tenant=self.tenant, code=code)
        if self.instance.pk:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise ValidationError('This role already exists for the active organization.')
        return code


class MembershipForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control', 'placeholder': 'Registered user email',
    }))
    role = forms.ModelChoiceField(queryset=Role.objects.none(), widget=forms.Select(attrs={
        'class': 'form-select',
    }))
    is_primary = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
        'class': 'form-check-input',
    }))

    def __init__(self, *args, tenant=None, membership=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.tenant = tenant
        self.membership = membership
        self.fields['role'].queryset = Role.objects.filter(tenant=tenant).order_by('name')
        if membership:
            self.fields['email'].initial = membership.user.email
            self.fields['email'].disabled = True
            self.fields['role'].initial = membership.role
            self.fields['is_primary'].initial = membership.is_primary

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if not User.objects.filter(email__iexact=email, is_active=True).exists():
            raise ValidationError('No active registered user exists with this email.')
        existing = UserTenant.objects.filter(user__email__iexact=email, tenant=self.tenant)
        if self.membership:
            existing = existing.exclude(pk=self.membership.pk)
        if existing.exists():
            raise ValidationError('This user is already a member of the organization.')
        return email
