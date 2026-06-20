"""
Authentication API URLs
JWT, OTP, Tenant Onboarding endpoints
"""
from django.urls import path

from apps.accounts.auth_views import (
    RegisterView,
    LoginView,
    RefreshTokenView,
    OTPRequestView,
    OTPVerifyView,
    MeView,
    TenantOnboardingView,
    VerifyEmailView,
    LogoutView,
)

app_name = 'auth'

urlpatterns = [
    # Auth endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('refresh/', RefreshTokenView.as_view(), name='refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', MeView.as_view(), name='me'),

    # OTP endpoints
    path('otp/request/', OTPRequestView.as_view(), name='otp-request'),
    path('otp/verify/', OTPVerifyView.as_view(), name='otp-verify'),

    # Email verification
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),

    # Tenant onboarding
    path('onboard-tenant/', TenantOnboardingView.as_view(), name='onboard-tenant'),
]
