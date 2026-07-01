from datetime import timedelta

from decimal import Decimal

from django.db import transaction
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from apps.accounts.models import (
    NotificationOutbox,
    OrganizerApplication,
    OrganizationSubscription,
    PaymentLedger,
    PaymentReceipt,
    PaymentReconciliation,
    Role,
    Tenant,
    UserActivityLog,
    UserTenant,
)


def enqueue_notification(*, event_type, recipient, user=None, tenant=None, subject='', body='', payload=None, channel=None):
    return NotificationOutbox.objects.create(
        event_type=event_type,
        recipient=recipient,
        user=user,
        tenant=tenant,
        subject=subject,
        body=body,
        payload=payload or {},
        channel=channel or NotificationOutbox.Channel.EMAIL,
    )


def _next_receipt_number():
    today = timezone.now().strftime('%Y%m%d')
    prefix = f'RNT-{today}-'
    count = PaymentReceipt.objects.filter(receipt_number__startswith=prefix).count() + 1
    return f'{prefix}{count:05d}'


def ensure_payment_receipt(payment):
    if hasattr(payment, 'receipt'):
        return payment.receipt
    application = payment.organizer_application
    billed_to_name = (
        application.organization_name
        if application else payment.user.full_name or payment.user.email
    )
    billed_to_email = application.email if application else payment.user.email
    return PaymentReceipt.objects.create(
        payment=payment,
        receipt_number=_next_receipt_number(),
        billed_to_name=billed_to_name,
        billed_to_email=billed_to_email,
        amount=payment.amount,
        currency=payment.currency,
        tax_amount=0,
        total_amount=payment.amount,
        description=payment.get_purpose_display(),
        metadata={
            'payment_reference': payment.reference,
            'gateway_order_id': payment.gateway_order_id,
            'gateway_payment_id': payment.gateway_payment_id,
        },
    )


def ensure_payment_reconciliation(payment, *, status=None, gateway_amount=None, gateway_currency='', gateway_payload=None, notes=''):
    reconciliation, _ = PaymentReconciliation.objects.get_or_create(payment=payment)
    if status:
        reconciliation.status = status
    if gateway_amount is not None:
        reconciliation.gateway_amount = gateway_amount
    if gateway_currency:
        reconciliation.gateway_currency = gateway_currency
    if gateway_payload is not None:
        reconciliation.gateway_payload = gateway_payload
    if notes:
        reconciliation.notes = notes
    if reconciliation.status in {
        PaymentReconciliation.Status.MATCHED,
        PaymentReconciliation.Status.MISMATCHED,
        PaymentReconciliation.Status.REFUNDED,
    }:
        reconciliation.reconciled_at = timezone.now()
    reconciliation.save()
    return reconciliation


def _unique_subdomain(base):
    candidate = ''.join(ch.lower() for ch in base if ch.isalnum() or ch == '-')[:40].strip('-')
    candidate = candidate or 'organization'
    value = candidate
    index = 2
    while Tenant.objects.filter(subdomain=value).exists():
        value = f'{candidate[:35]}-{index}'
        index += 1
    return value


def _period_end_for_plan(plan, start):
    if plan.billing_cycle == plan.BillingCycle.MONTHLY:
        return start + timedelta(days=30)
    if plan.billing_cycle == plan.BillingCycle.YEARLY:
        return start + timedelta(days=365)
    if plan.trial_days:
        return start + timedelta(days=plan.trial_days)
    return None


def upsert_subscription(*, tenant, application, plan, paid=False):
    now = timezone.now()
    status = (
        OrganizationSubscription.Status.ACTIVE
        if paid or plan.price == 0 or not plan.trial_days
        else OrganizationSubscription.Status.TRIALING
    )
    subscription, _ = OrganizationSubscription.objects.update_or_create(
        tenant=tenant,
        defaults={
            'plan': plan,
            'organizer_application': application,
            'status': status,
            'current_period_start': now,
            'current_period_end': _period_end_for_plan(plan, now),
            'cancel_at_period_end': False,
            'suspended_at': None,
            'suspension_reason': '',
        },
    )
    return subscription


@transaction.atomic
def provision_organizer_application(application, reviewer=None, note=''):
    application = (
        OrganizerApplication.objects.select_for_update()
        .select_related('user', 'plan', 'tenant')
        .get(pk=application.pk)
    )
    if application.tenant_id:
        return application.tenant
    if application.status not in {
        OrganizerApplication.Status.SUBMITTED,
        OrganizerApplication.Status.UNDER_REVIEW,
        OrganizerApplication.Status.APPROVED,
    }:
        raise ValueError('Only submitted, under-review or approved organizer applications can be provisioned.')

    plan = application.plan
    tenant = Tenant.objects.create(
        name=application.organization_name,
        tenant_type=application.tenant_type,
        subdomain=_unique_subdomain(application.organization_name),
        email=application.email,
        phone=application.phone,
        city=application.city,
        state=application.state,
        max_users=plan.max_users,
        max_teams=plan.max_teams,
        storage_limit_mb=plan.storage_limit_mb,
        subscription_plan=plan.code,
        subscription_start=timezone.now(),
        subscription_end=(
            timezone.now() + timedelta(days=plan.trial_days)
            if plan.trial_days else None
        ),
        verified=True,
        metadata={
            'plan_limits': {
                'max_tournaments': plan.max_tournaments,
                'max_players': plan.max_players,
                'max_venues': plan.max_venues,
            },
            'organizer_application_id': application.pk,
        },
    )
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
    UserTenant.objects.update_or_create(
        user=application.user,
        tenant=tenant,
        defaults={'role': admin_role, 'is_primary': True, 'is_active': True},
    )
    application.tenant = tenant
    application.status = OrganizerApplication.Status.PROVISIONED
    application.reviewed_by = reviewer or application.reviewed_by
    application.reviewed_at = timezone.now()
    application.review_note = note or application.review_note
    application.provisioned_at = timezone.now()
    application.save(update_fields=[
        'tenant', 'status', 'reviewed_by', 'reviewed_at',
        'review_note', 'provisioned_at', 'updated_at',
    ])
    upsert_subscription(
        tenant=tenant,
        application=application,
        plan=plan,
        paid=plan.price == 0 or application.payment_ledger.filter(status=PaymentLedger.Status.PAID).exists(),
    )
    enqueue_notification(
        event_type='organizer.provisioned',
        recipient=application.email,
        user=application.user,
        tenant=tenant,
        subject='Your RNT MPL organization is ready',
        body=f'{tenant.name} has been provisioned for your organizer account.',
        payload={'application_id': application.pk, 'tenant_id': str(tenant.pk), 'plan': plan.code},
    )
    UserActivityLog.objects.create(
        user=reviewer or application.user,
        tenant=tenant,
        activity_type=UserActivityLog.ActivityType.CREATE,
        action=f'Provisioned organizer tenant from application {application.pk}',
        model_name='OrganizerApplication',
        object_id=str(application.pk),
        object_repr=str(application),
    )
    return tenant


@transaction.atomic
def review_organizer_application(application, reviewer, approve, note=''):
    application = OrganizerApplication.objects.select_for_update().get(pk=application.pk)
    if approve:
        application.status = OrganizerApplication.Status.APPROVED
        application.reviewed_by = reviewer
        application.reviewed_at = timezone.now()
        application.review_note = note
        application.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'review_note', 'updated_at'])
        return provision_organizer_application(application, reviewer=reviewer, note=note)
    application.status = OrganizerApplication.Status.REJECTED
    application.reviewed_by = reviewer
    application.reviewed_at = timezone.now()
    application.review_note = note
    application.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'review_note', 'updated_at'])
    enqueue_notification(
        event_type='organizer.rejected',
        recipient=application.email,
        user=application.user,
        subject='RNT MPL organizer application update',
        body='Your organizer application has been reviewed. Please contact support for details.',
        payload={'application_id': application.pk, 'note': note},
    )
    return None


def create_organizer_plan_payment(application):
    plan = application.plan
    return PaymentLedger.objects.create(
        user=application.user,
        organizer_application=application,
        purpose=PaymentLedger.Purpose.ORGANIZER_PLAN,
        provider=PaymentLedger.Provider.MANUAL,
        status=PaymentLedger.Status.PENDING,
        amount=plan.price,
        reference=f'ORG-{application.pk}-{timezone.now().strftime("%Y%m%d%H%M%S")}',
    )


@transaction.atomic
def mark_payment_ledger_paid(payment, *, gateway_payment_id='', payload=None):
    payment = (
        PaymentLedger.objects.select_for_update()
        .select_related('organizer_application', 'organizer_application__plan', 'tenant')
        .get(pk=payment.pk)
    )
    if payment.status == PaymentLedger.Status.PAID:
        return payment
    payment.status = PaymentLedger.Status.PAID
    payment.gateway_payment_id = gateway_payment_id or payment.gateway_payment_id
    payment.gateway_payload = payload or payment.gateway_payload
    payment.paid_at = timezone.now()
    payment.failure_reason = ''
    payment.save(update_fields=[
        'status', 'gateway_payment_id', 'gateway_payload',
        'paid_at', 'failure_reason', 'updated_at',
    ])
    ensure_payment_receipt(payment)
    gateway_amount = None
    gateway_currency = ''
    if payload:
        entity = payload.get('payload', {}).get('payment', {}).get('entity', {})
        if entity.get('amount') is not None:
            gateway_amount = Decimal(str(entity['amount'])) / Decimal('100')
        gateway_currency = entity.get('currency') or ''
    reconcile_status = PaymentReconciliation.Status.MATCHED
    if gateway_amount is not None and gateway_amount != payment.amount:
        reconcile_status = PaymentReconciliation.Status.MISMATCHED
    ensure_payment_reconciliation(
        payment,
        status=reconcile_status,
        gateway_amount=gateway_amount,
        gateway_currency=gateway_currency,
        gateway_payload=payload or {},
    )
    application = payment.organizer_application
    if application and not application.tenant_id:
        provision_organizer_application(application, reviewer=None, note='Provisioned after confirmed plan payment.')
    elif application and application.tenant_id:
        upsert_subscription(
            tenant=application.tenant,
            application=application,
            plan=application.plan,
            paid=True,
        )
    enqueue_notification(
        event_type='payment.ledger.paid',
        recipient=payment.user.email,
        user=payment.user,
        tenant=payment.tenant or (application.tenant if application else None),
        subject='Payment confirmed',
        body=f'Payment {payment.reference} has been confirmed.',
        payload={'payment_id': payment.pk, 'purpose': payment.purpose},
    )
    return payment


@transaction.atomic
def mark_payment_refunded(payment, *, reason='', payload=None):
    payment = PaymentLedger.objects.select_for_update().get(pk=payment.pk)
    if payment.status == PaymentLedger.Status.REFUNDED:
        return payment
    payment.status = PaymentLedger.Status.REFUNDED
    payment.failure_reason = reason
    payment.gateway_payload = payload or payment.gateway_payload
    payment.save(update_fields=['status', 'failure_reason', 'gateway_payload', 'updated_at'])
    ensure_payment_reconciliation(
        payment,
        status=PaymentReconciliation.Status.REFUNDED,
        gateway_payload=payload or {},
        notes=reason,
    )
    enqueue_notification(
        event_type='payment.ledger.refunded',
        recipient=payment.user.email,
        user=payment.user,
        tenant=payment.tenant,
        subject='Payment refund recorded',
        body=f'Refund has been recorded for payment {payment.reference}.',
        payload={'payment_id': payment.pk, 'reason': reason},
    )
    return payment


def process_notification_outbox(limit=25):
    processed = []
    now = timezone.now()
    queryset = NotificationOutbox.objects.filter(
        status=NotificationOutbox.Status.PENDING,
    ).filter(
        Q(next_attempt_at__isnull=True) | Q(next_attempt_at__lte=now)
    ).order_by('created_at')[:limit]
    for notification in queryset:
        try:
            if notification.channel == NotificationOutbox.Channel.EMAIL:
                send_mail(
                    notification.subject or notification.event_type,
                    notification.body or notification.event_type,
                    getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                    [notification.recipient],
                    fail_silently=False,
                )
            notification.status = NotificationOutbox.Status.SENT
            notification.sent_at = now
            notification.last_error = ''
            notification.save(update_fields=['status', 'sent_at', 'last_error', 'updated_at'])
        except Exception as exc:
            notification.status = NotificationOutbox.Status.FAILED
            notification.attempts += 1
            notification.next_attempt_at = now + timedelta(minutes=min(60, 5 * notification.attempts))
            notification.last_error = str(exc)
            notification.save(update_fields=[
                'status', 'attempts', 'next_attempt_at', 'last_error', 'updated_at',
            ])
        processed.append(notification)
    return processed


@transaction.atomic
def suspend_subscription(subscription, *, reason=''):
    subscription = OrganizationSubscription.objects.select_for_update().select_related('tenant').get(pk=subscription.pk)
    subscription.status = OrganizationSubscription.Status.SUSPENDED
    subscription.suspended_at = timezone.now()
    subscription.suspension_reason = reason
    subscription.save(update_fields=['status', 'suspended_at', 'suspension_reason', 'updated_at'])
    tenant = subscription.tenant
    tenant.verified = False
    tenant.save(update_fields=['verified', 'updated_at'])
    return subscription


@transaction.atomic
def reactivate_subscription(subscription):
    subscription = OrganizationSubscription.objects.select_for_update().select_related('tenant').get(pk=subscription.pk)
    subscription.status = OrganizationSubscription.Status.ACTIVE
    subscription.suspended_at = None
    subscription.suspension_reason = ''
    subscription.save(update_fields=['status', 'suspended_at', 'suspension_reason', 'updated_at'])
    tenant = subscription.tenant
    tenant.verified = True
    tenant.save(update_fields=['verified', 'updated_at'])
    return subscription


def process_razorpay_payment_captured(payload):
    entity = (
        payload.get('payload', {})
        .get('payment', {})
        .get('entity', {})
    )
    order_id = entity.get('order_id') or ''
    payment_id = entity.get('id') or ''
    if not order_id:
        return None
    payment = PaymentLedger.objects.filter(
        provider=PaymentLedger.Provider.RAZORPAY,
        gateway_order_id=order_id,
    ).first()
    if not payment:
        return None
    return mark_payment_ledger_paid(
        payment,
        gateway_payment_id=payment_id,
        payload=payload,
    )


def tenant_limit_counts(tenant):
    from apps.players.models import PlayerProfile
    from apps.teams.models import Team
    from apps.tournaments.models import Tournament
    from apps.venues.models import Venue

    return {
        'players': PlayerProfile.objects.filter(tenant=tenant, is_deleted=False).count(),
        'teams': Team.objects.filter(tenant=tenant, is_deleted=False).count(),
        'tournaments': Tournament.objects.filter(tenant=tenant, is_deleted=False).count(),
        'venues': Venue.objects.filter(tenant=tenant, is_deleted=False).count(),
        'users': UserTenant.objects.filter(tenant=tenant, is_active=True).count(),
    }


def validate_tenant_plan_limit(tenant, resource):
    limits = (tenant.metadata or {}).get('plan_limits', {})
    field_map = {
        'players': 'max_players',
        'tournaments': 'max_tournaments',
        'venues': 'max_venues',
        'teams': 'max_teams',
        'users': 'max_users',
    }
    limit_field = field_map[resource]
    limit = limits.get(limit_field) or getattr(tenant, limit_field, None)
    if not limit:
        return
    count = tenant_limit_counts(tenant)[resource]
    if count >= int(limit):
        raise ValueError(f'Your current organization plan allows only {limit} {resource}.')
