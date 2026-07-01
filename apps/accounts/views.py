"""
Accounts & Authentication Views
Login, Registration, OTP, 2FA, Dashboard, Profile, Tenant management
"""
import random
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView
from django.contrib.auth.forms import PasswordResetForm
from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView, DetailView, FormView, ListView, TemplateView, UpdateView, View,
)

from apps.accounts.forms import (
    LoginForm, RegisterForm, OTPRequestForm, OTPVerifyForm,
    TwoFactorForm, ProfileForm, TenantCreateForm, RoleForm, MembershipForm,
    PlayerTrialEventForm, PlayerTrialEvaluationForm,
)
from apps.accounts.models import (
    OTPVerification, Role, Tenant, UserActivityLog, UserTenant,
)
from apps.accounts.policies import CapabilityRequiredMixin, ROLE_PRESETS
from apps.accounts.onboarding import (
    DashboardMode,
    apply_trial_decision,
    resolve_dashboard_mode,
)
from apps.common.encryption import hash_otp
from apps.players.models import PlayerProfile
from apps.publicsite.models import (
    PlayerRegistrationApplication,
    PlayerTrialEvent,
    PlayerTrialInvitation,
    WebsiteSettings,
)
from apps.teams.models import Team
from apps.tournaments.models import Tournament

User = get_user_model()


# ── Mixins ──────────────────────────────────────────────────────────────

class LogActivityMixin:
    """Mixin to log user activity after successful operations."""

    def log_activity(self, user, activity_type, action, **kwargs):
        UserActivityLog.objects.create(
            user=user,
            activity_type=activity_type,
            action=action,
            ip_address=self.request.META.get('REMOTE_ADDR', ''),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:500],
            request_method=self.request.method,
            request_path=self.request.path,
            **kwargs,
        )


# ── Authentication ──────────────────────────────────────────────────────

class CustomLoginView(LoginView):
    """Email-based login with remember-me support."""
    form_class = LoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass request to the form so Axes authenticate() works correctly
        kwargs['request'] = self.request
        return kwargs

    def get_success_url(self):
        return self.request.GET.get('next', reverse_lazy('accounts:dashboard'))

    def form_valid(self, form):
        user = form.get_user()
        # Let Django's LoginView.form_valid() handle the actual login call
        response = super().form_valid(form)
        if form.cleaned_data.get('remember_me'):
            self.request.session.set_expiry(60 * 60 * 24 * 30)
        else:
            self.request.session.set_expiry(60 * 60 * 24)
        primary_membership = (
            UserTenant.objects.filter(
                user=user,
                is_active=True,
                tenant__is_deleted=False,
            )
            .order_by('-is_primary', 'joined_at')
            .first()
        )
        if primary_membership and not self.request.session.get('active_tenant_id'):
            self.request.session['active_tenant_id'] = str(primary_membership.tenant_id)
        self.request.session.modified = True

        # Log activity and show welcome message after login
        user.record_login(self.request)
        UserActivityLog.objects.create(
            user=user,
            activity_type=UserActivityLog.ActivityType.LOGIN,
            action='User logged in successfully',
            ip_address=self.request.META.get('REMOTE_ADDR', ''),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:500],
            request_method='POST',
            request_path=self.request.path,
        )
        messages.success(self.request, f'Welcome back, {user.full_name}!')
        return response


class CustomLogoutView(View):
    """Log out confirmation (GET) and action (POST)."""
    template_name = 'accounts/logout.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            UserActivityLog.objects.create(
                user=request.user,
                activity_type=UserActivityLog.ActivityType.LOGOUT,
                action='User logged out',
                ip_address=request.META.get('REMOTE_ADDR', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                request_method='POST',
                request_path=request.path,
            )
            logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('accounts:login')


class RegisterView(FormView):
    """User registration with OTP verification before database creation."""
    form_class = RegisterForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:verify-otp')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        requested_type = request.GET.get('type')
        if requested_type == 'general':
            request.session['registration_type'] = 'GENERAL'
        elif requested_type == 'player':
            request.session['registration_type'] = 'PLAYER'
        if not request.session.get('registration_type'):
            return redirect('publicsite:registration-choice')
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        journey = self.request.session.get('player_journey', {})
        if journey:
            initial.update({
                'full_name': journey.get('full_name', ''),
                'phone': journey.get('phone', ''),
            })
        return initial

    def form_valid(self, form):
        # Store registration data in session
        registration_data = form.cleaned_data.copy()
        # Keep sensitive passwords but remove csrf token
        registration_data.pop('csrfmiddlewaretoken', None)
        registration_data['registration_type'] = self.request.session.get('registration_type', self.request.POST.get('registration_type', 'GENERAL'))
        self.request.session['registration_data'] = registration_data

        email = registration_data['email']

        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))
        stored_hash = hash_otp(otp, email)

        # Save OTP in database
        OTPVerification.objects.filter(email=email, purpose=OTPVerification.OTPPurpose.REGISTRATION).delete()
        OTPVerification.objects.create(
            email=email,
            otp_hash=stored_hash,
            purpose=OTPVerification.OTPPurpose.REGISTRATION,
            expires_at=timezone.now() + timezone.timedelta(minutes=10)
        )

        # Send OTP email
        from apps.accounts.email_otp import EmailOTPService
        success, msg = EmailOTPService.send_otp(email, otp, 'REGISTRATION')
        if not success:
            messages.warning(self.request, f"Email delivery failed: {msg}. Check console.")
        else:
            messages.success(self.request, 'Verification OTP sent to your email!')

        # Set OTP targets in session
        self.request.session['otp_target'] = email
        self.request.session['otp_purpose'] = OTPVerification.OTPPurpose.REGISTRATION

        return super().form_valid(form)


# ── OTP ─────────────────────────────────────────────────────────────────

class SendOTPView(FormView):
    """Send OTP to email or phone for verification."""
    form_class = OTPRequestForm
    template_name = 'accounts/otp_send.html'
    success_url = reverse_lazy('accounts:verify-otp')

    def form_valid(self, form):
        email_or_phone = form.cleaned_data['email_or_phone']
        purpose = form.cleaned_data['purpose']

        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))
        target = email_or_phone
        stored_hash = hash_otp(otp, target)

        # Determine if email or phone
        is_email = '@' in email_or_phone
        kwargs = {'otp_hash': stored_hash, 'purpose': purpose, 'expires_at': timezone.now() + timezone.timedelta(minutes=10)}
        if is_email:
            kwargs['email'] = email_or_phone
        else:
            kwargs['phone'] = email_or_phone

        OTPVerification.objects.create(**kwargs)

        if is_email:
            from apps.accounts.email_otp import EmailOTPService
            success, msg = EmailOTPService.send_otp(email_or_phone, otp, purpose)
            if not success:
                messages.warning(self.request, f"Could not send email: {msg}")
            else:
                messages.success(self.request, 'OTP sent successfully to your email!')
        else:
            print(f"[DEV] SMS OTP for {email_or_phone}: {otp}")
            messages.success(self.request, 'OTP sent successfully!')

        self.request.session['otp_target'] = email_or_phone
        self.request.session['otp_purpose'] = purpose
        return super().form_valid(form)


class VerifyOTPView(FormView):
    """Verify OTP code against stored hash."""
    form_class = OTPVerifyForm
    template_name = 'accounts/otp_verify.html'
    success_url = reverse_lazy('accounts:dashboard')

    def get_initial(self):
        return {
            'email_or_phone': self.request.session.get('otp_target', ''),
            'purpose': self.request.session.get('otp_purpose', OTPVerification.OTPPurpose.LOGIN),
        }

    def form_valid(self, form):
        email_or_phone = form.cleaned_data['email_or_phone']
        otp = form.cleaned_data['otp']
        purpose = form.cleaned_data['purpose']

        success, error = OTPVerification.generate_and_verify(otp, email_or_phone, purpose)
        if not success:
            messages.error(self.request, error or 'Invalid OTP.')
            return self.form_invalid(form)

        # Case 1: Registration verification
        if purpose == OTPVerification.OTPPurpose.REGISTRATION:
            registration_data = self.request.session.get('registration_data')
            if not registration_data:
                messages.error(self.request, 'Registration session expired. Please register again.')
                return redirect('accounts:register')

            email = registration_data.get('email')
            password = registration_data.get('password1')
            full_name = registration_data.get('full_name', '')
            phone = registration_data.get('phone', '')

            journey = self.request.session.get('player_journey', {})
            registration_type = registration_data.get('registration_type', 'GENERAL')
            with transaction.atomic():
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    full_name=full_name,
                    phone=phone,
                    user_type=User.UserType.FAN,
                    onboarding_state=(
                        User.OnboardingState.PLAYER_PAYMENT_PENDING
                        if registration_type == 'PLAYER'
                        else User.OnboardingState.GUEST
                    ),
                    is_active=True,
                    email_verified=True,
                    is_verified=True,
                )
                if registration_type == 'PLAYER' and journey:
                    names = full_name.strip().split(maxsplit=1)
                    player = PlayerProfile.objects.create(
                        first_name=names[0],
                        last_name=names[1] if len(names) > 1 else '',
                        date_of_birth=journey.get('date_of_birth') or None,
                        gender=journey.get('gender') or 'MALE',
                        phone=phone,
                        city=journey.get('city', ''),
                        state=journey.get('state', ''),
                        role=journey.get('role') or 'BATTER',
                        batting_style=journey.get('batting_style') or 'RIGHT_HAND',
                        bowling_style=journey.get('bowling_style', ''),
                        is_bowler=bool(journey.get('bowling_style')),
                        is_wicket_keeper=journey.get('is_wicket_keeper') == 'True',
                        jersey_number=journey.get('jersey_number') or None,
                        height_cm=journey.get('height_cm') or None,
                        weight_kg=journey.get('weight_kg') or None,
                        email=email,
                        biography=journey.get('achievements', ''),
                        player_status='INACTIVE',
                    )
                    site = WebsiteSettings.objects.first()
                    PlayerRegistrationApplication.objects.create(
                        user=user, player=player, full_name=full_name, email=email, phone=phone,
                        date_of_birth=journey.get('date_of_birth') or None,
                        gender=journey.get('gender', ''), city=journey.get('city', ''),
                        state=journey.get('state', ''), role=journey.get('role', ''),
                        batting_style=journey.get('batting_style', ''),
                        bowling_style=journey.get('bowling_style', ''),
                        is_wicket_keeper=journey.get('is_wicket_keeper') == 'True',
                        jersey_number=journey.get('jersey_number') or None,
                        height_cm=journey.get('height_cm') or None,
                        weight_kg=journey.get('weight_kg') or None,
                        playing_experience=journey.get('playing_experience') or 0,
                        academy_or_club=journey.get('academy_or_club', ''),
                        highest_level=journey.get('highest_level', ''),
                        achievements=journey.get('achievements', ''),
                        emergency_contact_name=journey.get('emergency_contact_name', ''),
                        emergency_contact_phone=journey.get('emergency_contact_phone', ''),
                        consent_accepted=journey.get('consent_accepted') == 'True',
                        fee_amount=site.registration_fee if site else 0,
                        status=PlayerRegistrationApplication.Status.PAYMENT_PENDING,
                        payment_status=PlayerRegistrationApplication.PaymentStatus.PENDING,
                        trial_status=PlayerRegistrationApplication.TrialStatus.LOCKED,
                    )

            # Send welcome email
            from apps.accounts.email_otp import EmailOTPService
            EmailOTPService.send_welcome_email(user.email, user.full_name)

            # Log activity
            UserActivityLog.objects.create(
                user=user,
                activity_type=UserActivityLog.ActivityType.CREATE,
                action='User registered a new account via OTP verification',
                ip_address=self.request.META.get('REMOTE_ADDR', ''),
                request_method='POST',
                request_path=self.request.path,
            )

            # Clean session
            self.request.session.pop('registration_data', None)
            self.request.session.pop('otp_target', None)
            self.request.session.pop('otp_purpose', None)
            self.request.session.pop('registration_type', None)
            self.request.session.pop('player_journey', None)

            # Auto-login
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(self.request, user)
            messages.success(self.request, 'Email verified! Your account has been created.')
            if registration_type == 'PLAYER':
                return redirect('publicsite:player-payment')
            return super().form_valid(form)

        # Case 2: Login or other verification purposes
        is_email = '@' in email_or_phone
        try:
            if is_email:
                user = User.objects.get(email=email_or_phone)
            else:
                user = User.objects.get(phone=email_or_phone)
        except User.DoesNotExist:
            messages.error(self.request, 'No registered account found with this email/phone.')
            return redirect('accounts:register')

        if is_email:
            user.email_verified = True
        else:
            user.phone_verified = True
        user.save(update_fields=['email_verified', 'phone_verified'])

        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(self.request, user)
        messages.success(self.request, 'OTP verified! You are now logged in.')
        return super().form_valid(form)


# ── Two-Factor ──────────────────────────────────────────────────────────

class TwoFactorSetupView(LoginRequiredMixin, TemplateView):
    """Set up TOTP 2FA using django-otp."""
    template_name = 'accounts/2fa_setup.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django_otp.plugins.otp_totp.models import TOTPDevice
        device, created = TOTPDevice.objects.get_or_create(
            user=self.request.user,
            name='default',
            defaults={'confirmed': False},
        )
        if not device.confirmed:
            context['secret_key'] = device.bin_key
            context['provisioning_uri'] = device.config_url
        context['device'] = device
        return context


class TwoFactorVerifyView(LoginRequiredMixin, FormView):
    """Verify a TOTP token to confirm 2FA setup or authenticate."""
    form_class = TwoFactorForm
    template_name = 'accounts/2fa_verify.html'
    success_url = reverse_lazy('accounts:dashboard')

    def form_valid(self, form):
        from django_otp import devices_for_user
        token = form.cleaned_data['token']
        for device in devices_for_user(self.request.user):
            if device.verify_token(token):
                self.request.user.is_2fa_enabled = True
                self.request.user.save(update_fields=['is_2fa_enabled'])
                messages.success(self.request, 'Two-factor authentication enabled.')
                return super().form_valid(form)
        messages.error(self.request, 'Invalid token. Please try again.')
        return self.form_invalid(form)


# ── Dashboard ───────────────────────────────────────────────────────────

class DashboardView(LoginRequiredMixin, TemplateView):
    """Main user dashboard showing summary stats across the ecosystem."""
    template_name = 'accounts/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        application = PlayerRegistrationApplication.objects.filter(
            user=self.request.user
        ).select_related('player').first()
        context['player_registration_application'] = application
        user = self.request.user
        context['dashboard_mode'] = resolve_dashboard_mode(user)
        context['is_guest_dashboard'] = context['dashboard_mode'] == DashboardMode.GUEST
        context['is_trial_dashboard'] = context['dashboard_mode'] == DashboardMode.TRIAL
        context['is_player_dashboard'] = context['dashboard_mode'] == DashboardMode.PLAYER
        context['is_organization_dashboard'] = context['dashboard_mode'] in {
            DashboardMode.ORGANIZATION, DashboardMode.PLATFORM,
        }
        context['trial_invitations'] = (
            application.trial_invitations.select_related('trial', 'trial__tenant')
            if application else []
        )
        
        tenant_id = self.request.session.get('active_tenant_id')
        tenant = None
        if tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id, is_deleted=False)
            except Tenant.DoesNotExist:
                pass
        if not tenant:
            tenant = getattr(self.request, 'tenant', None)

        context['my_tenants'] = UserTenant.objects.filter(
            user=user, is_active=True
        ).select_related('tenant', 'role')
        context['current_tenant'] = tenant
        context['total_tenants'] = context['my_tenants'].count()

        context['total_players'] = PlayerProfile.objects.filter(
            is_deleted=False, tenant=tenant
        ).count() if tenant else 0

        context['total_teams'] = Team.objects.filter(
            is_deleted=False, tenant=tenant
        ).count() if tenant else 0

        context['total_tournaments'] = Tournament.objects.filter(
            is_deleted=False, tenant=tenant
        ).count() if tenant else 0

        context['recent_activity'] = UserActivityLog.objects.filter(
            user=user
        ).order_by('-created_at')[:10]

        # Enhanced dashboard data
        if tenant:
            from apps.tournaments.models import TournamentMatch
            context['total_matches'] = TournamentMatch.objects.filter(
                tournament__tenant=tenant, is_deleted=False
            ).count()
            context['live_matches'] = TournamentMatch.objects.filter(
                tournament__tenant=tenant, is_deleted=False,
                is_completed=False
            ).select_related('home_team__team', 'away_team__team', 'tournament').order_by('-match_date')[:3]
            context['recent_tournaments'] = Tournament.objects.filter(
                is_deleted=False, tenant=tenant
            ).order_by('-created_at')[:5]
            context['recent_players'] = PlayerProfile.objects.filter(
                is_deleted=False, tenant=tenant
            ).order_by('-created_at')[:6]
            context['active_players'] = PlayerProfile.objects.filter(
                is_deleted=False, tenant=tenant, player_status='ACTIVE'
            ).count()
        else:
            context['total_matches'] = 0
            context['live_matches'] = []
            context['recent_tournaments'] = []
            context['recent_players'] = []
            context['active_players'] = 0

        return context


class RoleWorkspaceView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/role_workspace.html'
    workspace_config = {
        'tenant-admin': ('TENANT_ADMIN', 'Tenant Admin Workspace', 'roles.manage'),
        'scorer': ('SCORER', 'Scorer Workspace', 'scoring.manage'),
        'team-manager': ('TEAM_MANAGER', 'Team Manager Workspace', 'teams.manage'),
        'auction-manager': ('AUCTION_MANAGER', 'Auction Manager Workspace', 'auctions.manage'),
        'venue-manager': ('VENUE_MANAGER', 'Venue Manager Workspace', 'venues.manage'),
        'viewer': ('VIEWER', 'Viewer Workspace', 'tournaments.read'),
    }

    def dispatch(self, request, *args, **kwargs):
        self.workspace_key = kwargs['workspace']
        if self.workspace_key not in self.workspace_config:
            raise Http404('Workspace not found.')
        _, _, capability = self.workspace_config[self.workspace_key]
        from apps.accounts.policies import require_capability
        require_capability(request, capability)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        role_code, title, capability = self.workspace_config[self.workspace_key]
        tenant = self.request.tenant
        context.update({
            'workspace_key': self.workspace_key,
            'role_code': role_code,
            'workspace_title': title,
            'required_capability': capability,
            'current_tenant': tenant,
            'memberships': UserTenant.objects.filter(
                tenant=tenant, is_active=True
            ).select_related('user', 'role') if tenant else [],
        })
        if tenant:
            from apps.auctions.models import AuctionEvent
            from apps.tournaments.models import TournamentMatch
            from apps.venues.models import Venue
            context['workspace_stats'] = {
                'players': PlayerProfile.objects.filter(tenant=tenant, is_deleted=False).count(),
                'teams': Team.objects.filter(tenant=tenant, is_deleted=False).count(),
                'tournaments': Tournament.objects.filter(tenant=tenant, is_deleted=False).count(),
                'matches': TournamentMatch.objects.filter(tournament__tenant=tenant, is_deleted=False).count(),
                'venues': Venue.objects.filter(tenant=tenant, is_deleted=False).count(),
                'auctions': AuctionEvent.objects.filter(tournament__tenant=tenant, is_deleted=False).count(),
            }
        else:
            context['workspace_stats'] = {}
        return context


class PlayerTrialListView(
    LoginRequiredMixin, CapabilityRequiredMixin, ListView
):
    required_capability = 'tournaments.manage'
    model = PlayerTrialEvent
    template_name = 'accounts/player_trial_list.html'
    context_object_name = 'trials'

    def get_queryset(self):
        return PlayerTrialEvent.objects.filter(
            tenant=self.request.tenant
        ).prefetch_related('invitations')


class PlayerTrialCreateView(
    LoginRequiredMixin, CapabilityRequiredMixin, CreateView
):
    required_capability = 'tournaments.manage'
    model = PlayerTrialEvent
    form_class = PlayerTrialEventForm
    template_name = 'accounts/player_trial_form.html'

    def form_valid(self, form):
        form.instance.tenant = self.request.tenant
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Player trial created.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('accounts:player-trial-list')


class PlayerTrialDetailView(
    LoginRequiredMixin, CapabilityRequiredMixin, DetailView
):
    required_capability = 'tournaments.manage'
    model = PlayerTrialEvent
    template_name = 'accounts/player_trial_detail.html'
    context_object_name = 'trial'

    def get_queryset(self):
        return PlayerTrialEvent.objects.filter(tenant=self.request.tenant)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invitations'] = self.object.invitations.select_related(
            'application', 'application__user', 'application__player'
        )
        context['eligible_applications'] = PlayerRegistrationApplication.objects.filter(
            payment_status=PlayerRegistrationApplication.PaymentStatus.VERIFIED,
        ).exclude(trial_invitations__trial=self.object)
        return context


class PlayerTrialInviteView(
    LoginRequiredMixin, CapabilityRequiredMixin, View
):
    required_capability = 'tournaments.manage'

    def post(self, request, pk):
        trial = get_object_or_404(
            PlayerTrialEvent, pk=pk, tenant=request.tenant
        )
        application = get_object_or_404(
            PlayerRegistrationApplication,
            pk=request.POST.get('application'),
            payment_status=PlayerRegistrationApplication.PaymentStatus.VERIFIED,
        )
        invitation, created = PlayerTrialInvitation.objects.get_or_create(
            application=application,
            trial=trial,
            defaults={
                'status': PlayerRegistrationApplication.TrialStatus.INVITED,
                'scheduled_at': trial.starts_at,
            },
        )
        if created:
            application.trial_status = (
                PlayerRegistrationApplication.TrialStatus.INVITED
            )
            application.save(update_fields=['trial_status', 'updated_at'])
            messages.success(request, 'Player invited to the trial.')
        else:
            messages.info(request, 'Player is already invited to this trial.')
        return redirect('accounts:player-trial-detail', pk=trial.pk)


class PlayerTrialEvaluationView(
    LoginRequiredMixin, CapabilityRequiredMixin, FormView
):
    required_capability = 'tournaments.manage'
    form_class = PlayerTrialEvaluationForm
    template_name = 'accounts/player_trial_evaluation.html'

    def dispatch(self, request, *args, **kwargs):
        self.invitation = get_object_or_404(
            PlayerTrialInvitation.objects.select_related(
                'trial', 'application', 'application__player', 'application__user'
            ),
            pk=kwargs['pk'],
            trial__tenant=request.tenant,
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invitation'] = self.invitation
        return context

    def form_valid(self, form):
        apply_trial_decision(
            self.invitation, self.request.user, form.cleaned_data
        )
        messages.success(self.request, 'Trial evaluation saved.')
        return redirect(
            'accounts:player-trial-detail', pk=self.invitation.trial_id
        )


class PlayerTrialStatusView(
    LoginRequiredMixin, CapabilityRequiredMixin, View
):
    required_capability = 'tournaments.manage'
    allowed_statuses = {
        PlayerRegistrationApplication.TrialStatus.SCHEDULED,
        PlayerRegistrationApplication.TrialStatus.ATTENDED,
    }

    def post(self, request, pk, status):
        invitation = get_object_or_404(
            PlayerTrialInvitation.objects.select_related('trial', 'application'),
            pk=pk,
            trial__tenant=request.tenant,
        )
        if status not in self.allowed_statuses:
            messages.error(request, 'Invalid trial status transition.')
            return redirect(
                'accounts:player-trial-detail', pk=invitation.trial_id
            )
        invitation.status = status
        if status == PlayerRegistrationApplication.TrialStatus.SCHEDULED:
            invitation.scheduled_at = invitation.scheduled_at or invitation.trial.starts_at
        else:
            invitation.attended_at = timezone.now()
        invitation.save(
            update_fields=['status', 'scheduled_at', 'attended_at', 'updated_at']
        )
        invitation.application.trial_status = status
        invitation.application.save(
            update_fields=['trial_status', 'updated_at']
        )
        messages.success(request, 'Candidate trial status updated.')
        return redirect(
            'accounts:player-trial-detail', pk=invitation.trial_id
        )


# ── Profile ─────────────────────────────────────────────────────────────

class ProfileView(LoginRequiredMixin, DetailView):
    """View own user profile."""
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'profile_user'

    def get_object(self):
        return self.request.user


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Edit own user profile."""
    model = User
    form_class = ProfileForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)


# ── Tenant Management ───────────────────────────────────────────────────

class UserTenantListView(LoginRequiredMixin, ListView):
    """List all tenants the current user belongs to."""
    model = UserTenant
    template_name = 'accounts/tenant_list.html'
    context_object_name = 'memberships'

    def get_queryset(self):
        return UserTenant.objects.filter(
            user=self.request.user, is_active=True
        ).select_related('tenant', 'role').order_by('-is_primary', 'joined_at')


class TenantCreateView(LoginRequiredMixin, CreateView):
    """Create a new tenant organization."""
    model = Tenant
    form_class = TenantCreateForm
    template_name = 'accounts/tenant_create.html'
    success_url = reverse_lazy('accounts:tenant-list')

    def form_valid(self, form):
        with transaction.atomic():
            tenant = form.save()
            admin_role, _ = Role.objects.get_or_create(
                tenant=tenant,
                code='TENANT_ADMIN',
                defaults={
                    'name': 'Tenant Admin',
                    'category': Role.RoleCategory.TENANT,
                    'description': 'Full administrative access for this organization.',
                    'is_system': True,
                },
            )
            # Make creator the primary admin
            membership = UserTenant(
                user=self.request.user,
                tenant=tenant,
                role=admin_role,
                is_primary=True,
                is_active=True,
            )
            membership.save()
            self.request.session['active_tenant_id'] = str(tenant.id)

            UserActivityLog.objects.create(
                user=self.request.user,
                tenant=tenant,
                activity_type=UserActivityLog.ActivityType.CREATE,
                action=f'Created new tenant: {tenant.name} ({tenant.get_tenant_type_display()})',
                request_method='POST',
                request_path=self.request.path,
            )

        messages.success(self.request, f'Tenant "{tenant.name}" created and selected.')
        return redirect('accounts:dashboard')


class TenantDetailView(LoginRequiredMixin, DetailView):
    """View tenant details and stats."""
    model = Tenant
    template_name = 'accounts/tenant_detail.html'
    context_object_name = 'tenant'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.object
        context['members'] = UserTenant.objects.filter(
            tenant=tenant, is_active=True
        ).select_related('user', 'role')
        context['player_count'] = PlayerProfile.objects.filter(
            is_deleted=False, tenant=tenant
        ).count()
        context['team_count'] = Team.objects.filter(
            is_deleted=False, tenant=tenant
        ).count()
        context['tournament_count'] = Tournament.objects.filter(
            is_deleted=False, tenant=tenant
        ).count()
        return context


class SwitchTenantView(LoginRequiredMixin, View):
    """Switch the current active tenant context (stores in session)."""

    def post(self, request, pk):
        membership = get_object_or_404(
            UserTenant, user=request.user, tenant_id=pk, is_active=True
        )
        request.session['active_tenant_id'] = str(membership.tenant_id)
        messages.success(request, f'Switched to {membership.tenant.name}.')
        return redirect('accounts:dashboard')


class RoleStaffView(LoginRequiredMixin, CapabilityRequiredMixin, TemplateView):
    required_capability = 'roles.manage'
    template_name = 'accounts/role_staff.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.tenant
        for code, (name, description) in ROLE_PRESETS.items():
            Role.objects.get_or_create(
                tenant=tenant,
                code=code,
                defaults={
                    'name': name,
                    'description': description,
                    'category': Role.RoleCategory.TENANT,
                    'is_system': True,
                },
            )
        context['current_tenant'] = tenant
        context['roles'] = Role.objects.filter(tenant=tenant).order_by('name')
        context['members'] = UserTenant.objects.filter(
            tenant=tenant
        ).select_related('user', 'role').order_by('-is_active', 'user__full_name')
        return context


class RoleCreateView(LoginRequiredMixin, CapabilityRequiredMixin, CreateView):
    required_capability = 'roles.manage'
    model = Role
    form_class = RoleForm
    template_name = 'accounts/role_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.tenant
        return kwargs

    def form_valid(self, form):
        form.instance.tenant = self.request.tenant
        form.instance.category = Role.RoleCategory.TENANT
        preset = ROLE_PRESETS.get(form.cleaned_data['code'])
        if preset and not form.cleaned_data.get('description'):
            form.instance.description = preset[1]
        messages.success(self.request, 'Organization role created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('accounts:role-staff')


class MembershipCreateView(LoginRequiredMixin, CapabilityRequiredMixin, FormView):
    required_capability = 'roles.manage'
    form_class = MembershipForm
    template_name = 'accounts/membership_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.tenant
        return kwargs

    def form_valid(self, form):
        user = User.objects.get(email__iexact=form.cleaned_data['email'])
        UserTenant.objects.create(
            user=user,
            tenant=self.request.tenant,
            role=form.cleaned_data['role'],
            is_primary=form.cleaned_data['is_primary'],
            is_active=True,
        )
        messages.success(self.request, f'{user.full_name} added to the organization.')
        return redirect('accounts:role-staff')


class MembershipUpdateView(LoginRequiredMixin, CapabilityRequiredMixin, FormView):
    required_capability = 'roles.manage'
    form_class = MembershipForm
    template_name = 'accounts/membership_form.html'

    def get_membership(self):
        return get_object_or_404(UserTenant, pk=self.kwargs['pk'], tenant=self.request.tenant)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.tenant
        kwargs['membership'] = self.get_membership()
        return kwargs

    def form_valid(self, form):
        membership = self.get_membership()
        membership.role = form.cleaned_data['role']
        membership.is_primary = form.cleaned_data['is_primary']
        membership.save(update_fields=['role', 'is_primary'])
        messages.success(self.request, 'Member role updated successfully.')
        return redirect('accounts:role-staff')


class MembershipToggleView(LoginRequiredMixin, CapabilityRequiredMixin, View):
    required_capability = 'roles.manage'

    def post(self, request, pk):
        membership = get_object_or_404(UserTenant, pk=pk, tenant=request.tenant)
        if membership.user_id == request.user.id:
            messages.error(request, 'You cannot disable your own active membership.')
        else:
            membership.is_active = not membership.is_active
            membership.save(update_fields=['is_active'])
            messages.success(request, 'Member access updated.')
        return redirect('accounts:role-staff')


class CustomPasswordResetForm(PasswordResetForm):
    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        """
        Sends the password reset email with the inline logo attached.
        """
        from django.contrib.staticfiles import finders
        from django.template import loader
        from django.core.mail import EmailMultiAlternatives
        from email.mime.image import MIMEImage
        import os

        subject = loader.render_to_string(subject_template_name, context)
        subject = ''.join(subject.splitlines())
        
        html_message = loader.render_to_string(html_email_template_name, context) if html_email_template_name else None
        text_message = loader.render_to_string(email_template_name, context)
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=from_email,
            to=[to_email]
        )
        
        if html_message:
            msg.attach_alternative(html_message, "text/html")
            
            # Find and attach logo
            logo_path = finders.find('images/logo.png')
            if logo_path and os.path.exists(logo_path):
                with open(logo_path, 'rb') as f:
                    msg_img = MIMEImage(f.read())
                    msg_img.add_header('Content-ID', '<logo>')
                    msg_img.add_header('Content-Disposition', 'inline', filename='logo.png')
                    msg.attach(msg_img)
                    
        msg.send(fail_silently=False)


class CustomPasswordResetView(PasswordResetView):
    """Custom PasswordResetView utilizing the CustomPasswordResetForm to send premium emails."""
    form_class = CustomPasswordResetForm

