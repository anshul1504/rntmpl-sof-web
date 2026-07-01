from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from decimal import Decimal
import hashlib
import hmac
from unittest.mock import patch

from apps.accounts.models import Role, Tenant, UserTenant
from apps.accounts.onboarding import (
    DashboardMode,
    apply_trial_decision,
    resolve_dashboard_mode,
    review_player_payment,
)
from apps.players.models import PlayerProfile, PlayerStatus
from apps.publicsite.models import (
    PlayerPaymentTransaction,
    PlayerRegistrationApplication,
    PlayerTrialEvaluation,
    PlayerTrialEvent,
    PlayerTrialInvitation,
    PublicContentPage,
)


class PublicWebsiteSmokeTests(TestCase):
    def setUp(self):
        for slug, title in (
            ('privacy-policy', 'Privacy Policy'),
            ('terms-conditions', 'Terms & Conditions'),
            ('refund-policy', 'Refund Policy'),
            ('disclaimer', 'Disclaimer'),
        ):
            PublicContentPage.objects.get_or_create(
                page_type=slug,
                defaults={'title': title, 'content': 'Public information.', 'is_published': True},
            )

    def test_primary_public_routes_load(self):
        names = (
            'home', 'about', 'blog-list', 'news-list', 'contact', 'faq',
            'event-list', 'partners', 'sponsors', 'careers', 'team-list',
            'gallery', 'live-scores', 'match-center',
        )
        for name in names:
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(f'publicsite:{name}')).status_code, 200)

    def test_policy_routes_load(self):
        for slug in ('privacy-policy', 'terms-conditions', 'refund-policy', 'disclaimer'):
            response = self.client.get(reverse('publicsite:public-content', kwargs={'page_type': slug}))
            self.assertEqual(response.status_code, 200)

    def test_seo_endpoints_and_metadata(self):
        self.assertEqual(self.client.get(reverse('publicsite:robots')).status_code, 200)
        self.assertEqual(self.client.get(reverse('publicsite:sitemap')).status_code, 200)
        response = self.client.get(reverse('publicsite:home'))
        self.assertContains(response, 'rel="canonical"')
        self.assertContains(response, 'property="og:title"')

    def test_filters_do_not_break(self):
        self.assertEqual(self.client.get(reverse('publicsite:match-center'), {'status': 'live'}).status_code, 200)
        self.assertEqual(self.client.get(reverse('publicsite:event-list'), {'search': 'Mumbai'}).status_code, 200)
        self.assertEqual(self.client.get(reverse('publicsite:team-list'), {'search': 'RNT'}).status_code, 200)

    def test_dedicated_cms_requires_login(self):
        response = self.client.get('/website-admin/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/website-admin/login/', response.url)

    def test_dedicated_cms_only_lists_publicsite_models(self):
        user = get_user_model().objects.create_superuser(
            email='cms@example.com', password='StrongPass123!'
        )
        self.client.force_login(user)
        response = self.client.get('/website-admin/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Website Content Manager')
        self.assertNotContains(response, 'Tournament Matches')

    @override_settings(DEBUG=False, ALLOWED_HOSTS=['testserver'])
    def test_custom_404(self):
        response = self.client.get('/page-that-does-not-exist/')
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'Page Not Found', status_code=404)



class PlayerOnboardingFlowTests(TestCase):
    def test_guest_and_choice_pages_load(self):
        self.assertEqual(self.client.get(reverse('publicsite:guest-welcome')).status_code, 200)
        self.assertEqual(self.client.get(reverse('publicsite:registration-choice')).status_code, 200)

    def test_direct_register_requires_account_type_choice(self):
        response = self.client.get(reverse('accounts:register'))
        self.assertRedirects(response, reverse('publicsite:registration-choice'))
        response = self.client.get(reverse('accounts:register') + '?type=general')
        self.assertEqual(response.status_code, 200)

    def test_player_journey_persists_across_steps(self):
        response = self.client.post(reverse('publicsite:player-journey', kwargs={'step': 1}), {
            'full_name': 'Test Player', 'date_of_birth': '2000-01-01',
            'gender': 'MALE', 'phone': '9876543210', 'city': 'Mumbai', 'state': 'Maharashtra',
        })
        self.assertRedirects(response, reverse('publicsite:player-journey', kwargs={'step': 2}))
        response = self.client.post(reverse('publicsite:player-journey', kwargs={'step': 2}), {
            'role': 'BATTER', 'batting_style': 'RIGHT_HAND', 'bowling_style': '',
            'jersey_number': '18', 'height_cm': '178', 'weight_kg': '72',
        })
        self.assertRedirects(response, reverse('publicsite:player-journey', kwargs={'step': 3}))
        response = self.client.post(reverse('publicsite:player-journey', kwargs={'step': 3}), {
            'playing_experience': '5', 'academy_or_club': 'Test Academy',
            'highest_level': 'ACADEMY', 'achievements': 'Top scorer',
            'emergency_contact_name': 'Parent', 'emergency_contact_phone': '9876500000',
            'consent_accepted': 'on',
        })
        self.assertRedirects(response, reverse('publicsite:player-journey-review'))
        self.assertEqual(self.client.session['player_journey']['role'], 'BATTER')

    def test_review_moves_player_to_account_creation(self):
        session = self.client.session
        session['player_journey'] = {'full_name': 'Test Player', 'phone': '9876543210'}
        session.save()
        response = self.client.post(reverse('publicsite:player-journey-review'))
        self.assertRedirects(response, reverse('accounts:register'))
        self.assertEqual(self.client.session['registration_type'], 'PLAYER')


class PlayerLifecycleTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='candidate@example.com',
            password='StrongPass123!',
            full_name='Candidate Player',
            onboarding_state=get_user_model().OnboardingState.PLAYER_PAYMENT_PENDING,
        )
        self.player = PlayerProfile.objects.create(
            first_name='Candidate',
            last_name='Player',
            email=self.user.email,
            player_status=PlayerStatus.INACTIVE,
        )
        self.application = PlayerRegistrationApplication.objects.create(
            user=self.user,
            player=self.player,
            full_name='Candidate Player',
            email=self.user.email,
            fee_amount=Decimal('1500'),
            status=PlayerRegistrationApplication.Status.PAYMENT_PENDING,
            payment_status=PlayerRegistrationApplication.PaymentStatus.PENDING,
            trial_status=PlayerRegistrationApplication.TrialStatus.LOCKED,
        )
        self.admin_user = get_user_model().objects.create_superuser(
            email='platform@example.com', password='StrongPass123!'
        )

    def test_unpaid_player_returns_to_guest_dashboard_after_login(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('accounts:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['dashboard_mode'], DashboardMode.GUEST)
        self.assertContains(response, 'Guest Dashboard')
        self.assertContains(response, 'Complete Registration Payment')

    def test_payment_submission_does_not_activate_player(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('publicsite:player-payment'),
            {'payment_reference': 'UTR-PLAYER-1001'},
        )

        self.assertRedirects(response, reverse('accounts:dashboard'))
        self.application.refresh_from_db()
        self.user.refresh_from_db()
        self.player.refresh_from_db()
        self.assertEqual(
            self.application.payment_status,
            PlayerRegistrationApplication.PaymentStatus.SUBMITTED,
        )
        self.assertEqual(
            resolve_dashboard_mode(self.user), DashboardMode.GUEST
        )
        self.assertEqual(self.player.player_status, PlayerStatus.INACTIVE)

    def test_verified_payment_unlocks_trial_dashboard(self):
        payment = PlayerPaymentTransaction.objects.create(
            application=self.application,
            user=self.user,
            amount=self.application.fee_amount,
            reference='UTR-VERIFY-1001',
        )

        review_player_payment(payment, self.admin_user, True)
        self.application.refresh_from_db()
        self.user.refresh_from_db()

        self.assertEqual(
            self.application.trial_status,
            PlayerRegistrationApplication.TrialStatus.ELIGIBLE,
        )
        self.assertEqual(
            resolve_dashboard_mode(self.user), DashboardMode.TRIAL
        )

    def test_rejected_payment_keeps_guest_access(self):
        payment = PlayerPaymentTransaction.objects.create(
            application=self.application,
            user=self.user,
            amount=self.application.fee_amount,
            reference='UTR-REJECT-1001',
        )

        review_player_payment(payment, self.admin_user, False, 'Reference not found')
        self.application.refresh_from_db()
        self.user.refresh_from_db()

        self.assertEqual(
            self.application.payment_status,
            PlayerRegistrationApplication.PaymentStatus.REJECTED,
        )
        self.assertEqual(resolve_dashboard_mode(self.user), DashboardMode.GUEST)

    @override_settings(RAZORPAY_KEY_ID='', RAZORPAY_KEY_SECRET='')
    def test_duplicate_payment_reference_is_rejected(self):
        PlayerPaymentTransaction.objects.create(
            application=self.application,
            user=self.user,
            amount=self.application.fee_amount,
            reference='DUPLICATE-UTR',
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('publicsite:player-payment'),
            {'payment_reference': 'duplicate-utr'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already been submitted')

    @override_settings(RAZORPAY_KEY_ID='rzp_test_key', RAZORPAY_KEY_SECRET='secret')
    @patch('apps.publicsite.payments.RazorpayPaymentService.create_order')
    def test_payment_page_creates_razorpay_order(self, create_order):
        create_order.return_value = {
            'id': 'order_player_1001',
            'amount': 150000,
            'currency': 'INR',
            'receipt': 'player-test',
        }
        self.client.force_login(self.user)

        response = self.client.get(reverse('publicsite:player-payment'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pay Securely With Razorpay')
        self.assertContains(response, 'order_player_1001')
        self.assertTrue(
            PlayerPaymentTransaction.objects.filter(
                application=self.application,
                provider=PlayerPaymentTransaction.Provider.RAZORPAY,
                gateway_order_id='order_player_1001',
                status=PlayerPaymentTransaction.Status.CREATED,
            ).exists()
        )

    @override_settings(RAZORPAY_KEY_ID='rzp_test_key', RAZORPAY_KEY_SECRET='secret')
    def test_razorpay_verify_unlocks_trial_dashboard(self):
        payment = PlayerPaymentTransaction.objects.create(
            application=self.application,
            user=self.user,
            amount=self.application.fee_amount,
            reference='order_player_1002',
            provider=PlayerPaymentTransaction.Provider.RAZORPAY,
            gateway_order_id='order_player_1002',
            status=PlayerPaymentTransaction.Status.CREATED,
        )
        payment_id = 'pay_player_1002'
        signature = hmac.new(
            b'secret',
            f'{payment.gateway_order_id}|{payment_id}'.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('publicsite:player-payment-verify'),
            {
                'razorpay_order_id': payment.gateway_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature,
            },
        )

        self.assertRedirects(response, reverse('accounts:dashboard'))
        self.application.refresh_from_db()
        payment.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(payment.status, PlayerPaymentTransaction.Status.VERIFIED)
        self.assertEqual(
            self.application.payment_status,
            PlayerRegistrationApplication.PaymentStatus.VERIFIED,
        )
        self.assertEqual(
            self.application.trial_status,
            PlayerRegistrationApplication.TrialStatus.ELIGIBLE,
        )
        self.assertEqual(resolve_dashboard_mode(self.user), DashboardMode.TRIAL)

    @override_settings(RAZORPAY_KEY_ID='rzp_test_key', RAZORPAY_KEY_SECRET='secret')
    def test_razorpay_bad_signature_keeps_guest_dashboard(self):
        payment = PlayerPaymentTransaction.objects.create(
            application=self.application,
            user=self.user,
            amount=self.application.fee_amount,
            reference='order_player_1003',
            provider=PlayerPaymentTransaction.Provider.RAZORPAY,
            gateway_order_id='order_player_1003',
            status=PlayerPaymentTransaction.Status.CREATED,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('publicsite:player-payment-verify'),
            {
                'razorpay_order_id': payment.gateway_order_id,
                'razorpay_payment_id': 'pay_player_1003',
                'razorpay_signature': 'bad-signature',
            },
        )

        self.assertRedirects(response, reverse('publicsite:player-payment'))
        self.application.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(payment.status, PlayerPaymentTransaction.Status.FAILED)
        self.assertEqual(resolve_dashboard_mode(self.user), DashboardMode.GUEST)

    def test_selection_activates_player_in_organizer_tenant(self):
        payment = PlayerPaymentTransaction.objects.create(
            application=self.application,
            user=self.user,
            amount=self.application.fee_amount,
            reference='UTR-SELECT-1001',
        )
        review_player_payment(payment, self.admin_user, True)
        tenant = Tenant.objects.create(name='Selection Academy')
        trial = PlayerTrialEvent.objects.create(
            tenant=tenant,
            title='Selection Trial',
            venue='Main Ground',
            starts_at='2026-07-01T10:00:00+05:30',
            status=PlayerTrialEvent.Status.OPEN,
            created_by=self.admin_user,
        )
        invitation = PlayerTrialInvitation.objects.create(
            application=self.application,
            trial=trial,
            scheduled_at=trial.starts_at,
        )

        apply_trial_decision(
            invitation,
            self.admin_user,
            {
                'batting_score': 80,
                'bowling_score': 60,
                'fielding_score': 75,
                'fitness_score': 85,
                'notes': 'Selected after assessment.',
                'recommendation': PlayerTrialEvaluation.Recommendation.SELECT,
            },
        )

        self.application.refresh_from_db()
        self.player.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(self.application.trial_status, 'SELECTED')
        self.assertEqual(self.player.tenant, tenant)
        self.assertEqual(self.player.player_status, PlayerStatus.ACTIVE)
        self.assertEqual(resolve_dashboard_mode(self.user), DashboardMode.PLAYER)
        self.client.force_login(self.user)
        own_profile = self.client.get(
            reverse('players:player-detail', args=[self.player.pk])
        )
        self.assertEqual(own_profile.status_code, 200)

        other_player = PlayerProfile.objects.create(
            tenant=tenant,
            first_name='Other',
            last_name='Player',
        )
        hidden_profile = self.client.get(
            reverse('players:player-detail', args=[other_player.pk])
        )
        self.assertEqual(hidden_profile.status_code, 404)


class OrganizerTrialIsolationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='organizer-trial@example.com', password='StrongPass123!'
        )
        self.tenant = Tenant.objects.create(name='Organizer Academy')
        self.other_tenant = Tenant.objects.create(name='Other Academy')
        role = Role.objects.create(
            tenant=self.tenant,
            name='Tournament Manager',
            code='TOURNAMENT_MANAGER',
        )
        UserTenant.objects.create(
            user=self.user, tenant=self.tenant, role=role, is_primary=True
        )
        self.client.force_login(self.user)
        session = self.client.session
        session['active_tenant_id'] = str(self.tenant.pk)
        session.save()

    def test_organizer_cannot_open_other_tenant_trial(self):
        trial = PlayerTrialEvent.objects.create(
            tenant=self.other_tenant,
            title='Hidden Trial',
            venue='Other Ground',
            starts_at='2026-07-02T10:00:00+05:30',
        )

        response = self.client.get(
            reverse('accounts:player-trial-detail', args=[trial.pk])
        )

        self.assertEqual(response.status_code, 404)
