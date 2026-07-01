"""
Accounts & Authentication URL Configuration
Login, Registration, OTP, Password Reset, Profile, Dashboard
"""
from django.urls import path
from django.contrib.auth import views as auth_views

from apps.accounts import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),

    # OTP Verification
    path('otp/send/', views.SendOTPView.as_view(), name='send-otp'),
    path('otp/verify/', views.VerifyOTPView.as_view(), name='verify-otp'),

    # Password Reset
    path('password-reset/', views.CustomPasswordResetView.as_view(
        template_name='accounts/password_reset.html',
        email_template_name='emails/password_reset_email.txt',
        html_email_template_name='emails/password_reset_email.html',
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html',
    ), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
    ), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html',
    ), name='password_reset_complete'),

    # 2FA
    path('2fa/setup/', views.TwoFactorSetupView.as_view(), name='2fa-setup'),
    path('2fa/verify/', views.TwoFactorVerifyView.as_view(), name='2fa-verify'),

    # Dashboard & Profile
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('workspaces/<slug:workspace>/', views.RoleWorkspaceView.as_view(), name='role-workspace'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile-edit'),

    # Tenant
    path('tenants/', views.UserTenantListView.as_view(), name='tenant-list'),
    path('tenants/create/', views.TenantCreateView.as_view(), name='tenant-create'),
    path('tenants/<pk>/', views.TenantDetailView.as_view(), name='tenant-detail'),
    path('tenants/<pk>/switch/', views.SwitchTenantView.as_view(), name='tenant-switch'),
    path('roles-staff/', views.RoleStaffView.as_view(), name='role-staff'),
    path('roles/create/', views.RoleCreateView.as_view(), name='role-create'),
    path('members/add/', views.MembershipCreateView.as_view(), name='membership-create'),
    path('members/<int:pk>/edit/', views.MembershipUpdateView.as_view(), name='membership-edit'),
    path('members/<int:pk>/toggle/', views.MembershipToggleView.as_view(), name='membership-toggle'),
    path('player-trials/', views.PlayerTrialListView.as_view(), name='player-trial-list'),
    path('player-trials/create/', views.PlayerTrialCreateView.as_view(), name='player-trial-create'),
    path('player-trials/<int:pk>/', views.PlayerTrialDetailView.as_view(), name='player-trial-detail'),
    path('player-trials/<int:pk>/invite/', views.PlayerTrialInviteView.as_view(), name='player-trial-invite'),
    path('player-trial-invitations/<int:pk>/evaluate/', views.PlayerTrialEvaluationView.as_view(), name='player-trial-evaluate'),
    path('player-trial-invitations/<int:pk>/status/<str:status>/', views.PlayerTrialStatusView.as_view(), name='player-trial-status'),
]
