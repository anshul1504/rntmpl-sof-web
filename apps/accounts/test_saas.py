import hashlib
import hmac
import json

from django.test import TestCase, override_settings
from django.urls import reverse

from apps.accounts.models import (
    NotificationOutbox,
    OrganizerApplication,
    OrganizationPlan,
    OrganizationSubscription,
    PaymentLedger,
    PaymentReceipt,
    PaymentReconciliation,
    PaymentWebhookEvent,
    Role,
    Tenant,
    User,
    UserTenant,
)
from apps.accounts.saas import (
    create_organizer_plan_payment,
    mark_payment_ledger_paid,
    mark_payment_refunded,
    process_notification_outbox,
    provision_organizer_application,
    reactivate_subscription,
    suspend_subscription,
)
from apps.players.models import PlayerProfile


class OrganizerSaasTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='organizer@example.com',
            password='StrongPass123',
            full_name='Organizer User',
            phone='9999999999',
        )
        self.plan = OrganizationPlan.objects.create(
            name='Launch Plan',
            code='launch',
            price=0,
            max_tournaments=2,
            max_teams=2,
            max_players=1,
            max_venues=1,
            max_users=2,
            storage_limit_mb=250,
            is_active=True,
        )

    def test_public_organizer_application_creates_notification(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('publicsite:organizer-signup'), {
            'plan': self.plan.pk,
            'organization_name': 'City Premier League',
            'tenant_type': Tenant.TenantType.LEAGUE,
            'contact_person': 'Organizer User',
            'email': 'organizer@example.com',
            'phone': '9999999999',
            'city': 'Bhopal',
            'state': 'MP',
            'expected_teams': 2,
            'expected_players': 1,
            'message': 'Need tournament operations.',
        })

        self.assertEqual(response.status_code, 302)
        application = OrganizerApplication.objects.get()
        self.assertEqual(application.status, OrganizerApplication.Status.SUBMITTED)
        self.assertEqual(application.user, self.user)
        self.assertTrue(
            NotificationOutbox.objects.filter(
                event_type='organizer.application.submitted',
                recipient='organizer@example.com',
            ).exists()
        )

    def test_approval_provisions_tenant_and_admin_membership(self):
        application = OrganizerApplication.objects.create(
            user=self.user,
            plan=self.plan,
            organization_name='City Premier League',
            tenant_type=Tenant.TenantType.LEAGUE,
            contact_person='Organizer User',
            email='organizer@example.com',
            phone='9999999999',
        )

        tenant = provision_organizer_application(application, reviewer=self.user)
        application.refresh_from_db()

        self.assertEqual(application.status, OrganizerApplication.Status.PROVISIONED)
        self.assertEqual(application.tenant, tenant)
        self.assertEqual(tenant.subscription_plan, self.plan.code)
        self.assertEqual(tenant.max_users, self.plan.max_users)
        self.assertEqual(tenant.max_teams, self.plan.max_teams)
        self.assertEqual(tenant.metadata['plan_limits']['max_players'], self.plan.max_players)
        membership = UserTenant.objects.get(user=self.user, tenant=tenant)
        self.assertEqual(membership.role.code, 'TENANT_ADMIN')
        self.assertTrue(membership.is_primary)
        subscription = OrganizationSubscription.objects.get(tenant=tenant)
        self.assertEqual(subscription.plan, self.plan)
        self.assertEqual(subscription.status, OrganizationSubscription.Status.ACTIVE)

    def test_organizer_application_status_page_is_user_scoped(self):
        other = User.objects.create_user(email='other@example.com', password='StrongPass123')
        OrganizerApplication.objects.create(
            user=self.user,
            plan=self.plan,
            organization_name='Visible League',
            tenant_type=Tenant.TenantType.LEAGUE,
            contact_person='Organizer User',
            email='organizer@example.com',
            phone='9999999999',
        )
        OrganizerApplication.objects.create(
            user=other,
            plan=self.plan,
            organization_name='Hidden League',
            tenant_type=Tenant.TenantType.LEAGUE,
            contact_person='Other User',
            email='other@example.com',
            phone='8888888888',
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('publicsite:organizer-application-status'))

        self.assertContains(response, 'Visible League')
        self.assertNotContains(response, 'Hidden League')

    def test_subscription_suspend_and_reactivate_updates_tenant_verified_state(self):
        application = OrganizerApplication.objects.create(
            user=self.user,
            plan=self.plan,
            organization_name='Subscription League',
            tenant_type=Tenant.TenantType.LEAGUE,
            contact_person='Organizer User',
            email='organizer@example.com',
            phone='9999999999',
        )
        tenant = provision_organizer_application(application, reviewer=self.user)
        subscription = tenant.organization_subscription

        suspend_subscription(subscription, reason='Past due')
        subscription.refresh_from_db()
        tenant.refresh_from_db()
        self.assertEqual(subscription.status, OrganizationSubscription.Status.SUSPENDED)
        self.assertFalse(tenant.verified)

        reactivate_subscription(subscription)
        subscription.refresh_from_db()
        tenant.refresh_from_db()
        self.assertEqual(subscription.status, OrganizationSubscription.Status.ACTIVE)
        self.assertTrue(tenant.verified)

    def test_plan_limit_blocks_extra_player_create(self):
        tenant = Tenant.objects.create(
            name='Limited League',
            tenant_type=Tenant.TenantType.LEAGUE,
            max_teams=2,
            max_users=2,
            metadata={'plan_limits': {'max_players': 1}},
        )
        role = Role.objects.create(tenant=tenant, name='Team Manager', code='TEAM_MANAGER')
        UserTenant.objects.create(user=self.user, tenant=tenant, role=role, is_primary=True)
        PlayerProfile.objects.create(tenant=tenant, first_name='Existing', last_name='Player')
        self.client.force_login(self.user)
        session = self.client.session
        session['active_tenant_id'] = str(tenant.pk)
        session.save()

        response = self.client.post('/api/v1/players/', {
            'tenant': str(tenant.pk),
            'first_name': 'Blocked',
            'last_name': 'Player',
            'date_of_birth': '2000-01-01',
            'gender': 'MALE',
            'role': 'BATTER',
            'batting_style': 'RIGHT_HAND',
            'bowling_style': '',
            'player_status': 'ACTIVE',
        }, content_type='application/json')

        self.assertEqual(response.status_code, 400)
        self.assertFalse(PlayerProfile.objects.filter(first_name='Blocked').exists())


class RazorpayWebhookTests(TestCase):
    @override_settings(RAZORPAY_KEY_ID='rzp_test', RAZORPAY_KEY_SECRET='secret')
    def test_webhook_requires_valid_signature_and_is_idempotent(self):
        payload = {
            'id': 'evt_123',
            'event': 'payment.captured',
            'created_at': 123456,
            'payload': {'payment': {'entity': {'id': 'pay_123'}}},
        }
        raw = json.dumps(payload).encode('utf-8')
        signature = hmac.new(b'secret', raw, hashlib.sha256).hexdigest()

        response = self.client.post(
            reverse('publicsite:razorpay-webhook'),
            raw,
            content_type='application/json',
            HTTP_X_RAZORPAY_SIGNATURE=signature,
        )
        self.assertEqual(response.status_code, 200)
        event = PaymentWebhookEvent.objects.get(event_id='evt_123')
        self.assertTrue(event.is_valid)

        duplicate = self.client.post(
            reverse('publicsite:razorpay-webhook'),
            raw,
            content_type='application/json',
            HTTP_X_RAZORPAY_SIGNATURE=signature,
        )
        self.assertEqual(duplicate.status_code, 200)
        self.assertEqual(PaymentWebhookEvent.objects.count(), 1)

        bad = self.client.post(
            reverse('publicsite:razorpay-webhook'),
            raw,
            content_type='application/json',
            HTTP_X_RAZORPAY_SIGNATURE='bad',
        )
        self.assertEqual(bad.status_code, 400)

    @override_settings(RAZORPAY_KEY_ID='rzp_test', RAZORPAY_KEY_SECRET='secret')
    def test_webhook_payment_capture_marks_organizer_payment_paid_and_provisions(self):
        user = User.objects.create_user(email='paid-organizer@example.com', password='StrongPass123')
        plan = OrganizationPlan.objects.create(
            name='Paid Plan',
            code='paid-plan',
            price=4999,
            billing_cycle=OrganizationPlan.BillingCycle.MONTHLY,
            max_tournaments=3,
            max_teams=16,
            max_players=240,
            max_venues=4,
            max_users=10,
            is_active=True,
        )
        application = OrganizerApplication.objects.create(
            user=user,
            plan=plan,
            organization_name='Paid League',
            tenant_type=Tenant.TenantType.LEAGUE,
            contact_person='Paid Organizer',
            email=user.email,
            phone='7777777777',
        )
        payment = create_organizer_plan_payment(application)
        payment.provider = PaymentLedger.Provider.RAZORPAY
        payment.gateway_order_id = 'order_123'
        payment.save(update_fields=['provider', 'gateway_order_id'])

        payload = {
            'id': 'evt_paid',
            'event': 'payment.captured',
            'created_at': 123456,
            'payload': {
                'payment': {
                    'entity': {
                        'id': 'pay_123',
                        'order_id': 'order_123',
                    }
                }
            },
        }
        raw = json.dumps(payload).encode('utf-8')
        signature = hmac.new(b'secret', raw, hashlib.sha256).hexdigest()

        response = self.client.post(
            reverse('publicsite:razorpay-webhook'),
            raw,
            content_type='application/json',
            HTTP_X_RAZORPAY_SIGNATURE=signature,
        )

        self.assertEqual(response.status_code, 200)
        payment.refresh_from_db()
        application.refresh_from_db()
        self.assertEqual(payment.status, PaymentLedger.Status.PAID)
        self.assertEqual(payment.gateway_payment_id, 'pay_123')
        self.assertEqual(application.status, OrganizerApplication.Status.PROVISIONED)
        subscription = OrganizationSubscription.objects.get(tenant=application.tenant)
        self.assertEqual(subscription.status, OrganizationSubscription.Status.ACTIVE)
        receipt = PaymentReceipt.objects.get(payment=payment)
        self.assertTrue(receipt.receipt_number.startswith('RNT-'))
        reconciliation = PaymentReconciliation.objects.get(payment=payment)
        self.assertEqual(reconciliation.status, PaymentReconciliation.Status.MATCHED)

    def test_paid_payment_creates_receipt_and_matched_reconciliation(self):
        user = User.objects.create_user(email='receipt@example.com', password='StrongPass123')
        payment = PaymentLedger.objects.create(
            user=user,
            purpose=PaymentLedger.Purpose.ORGANIZER_PLAN,
            provider=PaymentLedger.Provider.RAZORPAY,
            status=PaymentLedger.Status.PENDING,
            amount=4999,
            reference='receipt-test',
            gateway_order_id='order_receipt',
        )
        payload = {
            'payload': {
                'payment': {
                    'entity': {
                        'id': 'pay_receipt',
                        'order_id': 'order_receipt',
                        'amount': 499900,
                        'currency': 'INR',
                    }
                }
            }
        }

        mark_payment_ledger_paid(payment, gateway_payment_id='pay_receipt', payload=payload)
        payment.refresh_from_db()

        self.assertEqual(payment.status, PaymentLedger.Status.PAID)
        receipt = PaymentReceipt.objects.get(payment=payment)
        self.assertEqual(receipt.total_amount, payment.amount)
        reconciliation = PaymentReconciliation.objects.get(payment=payment)
        self.assertEqual(reconciliation.status, PaymentReconciliation.Status.MATCHED)
        self.assertEqual(reconciliation.gateway_amount, payment.amount)

    def test_refund_updates_reconciliation_and_queues_notification(self):
        user = User.objects.create_user(email='refund@example.com', password='StrongPass123')
        payment = PaymentLedger.objects.create(
            user=user,
            purpose=PaymentLedger.Purpose.ORGANIZER_PLAN,
            provider=PaymentLedger.Provider.MANUAL,
            status=PaymentLedger.Status.PAID,
            amount=1000,
            reference='refund-test',
        )

        mark_payment_refunded(payment, reason='Customer request')
        payment.refresh_from_db()

        self.assertEqual(payment.status, PaymentLedger.Status.REFUNDED)
        reconciliation = PaymentReconciliation.objects.get(payment=payment)
        self.assertEqual(reconciliation.status, PaymentReconciliation.Status.REFUNDED)
        self.assertTrue(
            NotificationOutbox.objects.filter(
                event_type='payment.ledger.refunded',
                recipient='refund@example.com',
            ).exists()
        )


class NotificationOutboxTests(TestCase):
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_process_notification_outbox_sends_email(self):
        notification = NotificationOutbox.objects.create(
            event_type='test.email',
            channel=NotificationOutbox.Channel.EMAIL,
            recipient='notify@example.com',
            subject='Test notification',
            body='Notification body',
        )

        processed = process_notification_outbox(limit=10)
        notification.refresh_from_db()

        self.assertEqual(len(processed), 1)
        self.assertEqual(notification.status, NotificationOutbox.Status.SENT)
        self.assertIsNotNone(notification.sent_at)


class RoleWorkspaceTests(TestCase):
    def test_role_workspace_requires_matching_capability(self):
        tenant = Tenant.objects.create(name='Role League', tenant_type=Tenant.TenantType.LEAGUE)
        user = User.objects.create_user(email='viewer@example.com', password='StrongPass123')
        viewer_role = Role.objects.create(tenant=tenant, name='Viewer', code='VIEWER')
        UserTenant.objects.create(user=user, tenant=tenant, role=viewer_role, is_primary=True)
        self.client.force_login(user)
        session = self.client.session
        session['active_tenant_id'] = str(tenant.pk)
        session.save()

        viewer_response = self.client.get(reverse('accounts:role-workspace', kwargs={'workspace': 'viewer'}))
        self.assertEqual(viewer_response.status_code, 200)

        scorer_response = self.client.get(reverse('accounts:role-workspace', kwargs={'workspace': 'scorer'}))
        self.assertEqual(scorer_response.status_code, 403)
