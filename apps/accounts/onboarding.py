from django.db import transaction
from django.utils import timezone

from apps.accounts.models import UserTenant
from apps.players.models import PlayerStatus
from apps.publicsite.models import (
    PlayerPaymentTransaction,
    PlayerRegistrationApplication,
    PlayerTrialEvaluation,
)


class DashboardMode:
    PLATFORM = 'PLATFORM'
    ORGANIZATION = 'ORGANIZATION'
    PLAYER = 'PLAYER'
    TRIAL = 'TRIAL'
    GUEST = 'GUEST'


def resolve_dashboard_mode(user):
    if user.is_superuser or user.user_type == user.UserType.SUPER_ADMIN:
        return DashboardMode.PLATFORM
    if UserTenant.objects.filter(
        user=user, is_active=True, tenant__is_deleted=False
    ).exists():
        return DashboardMode.ORGANIZATION
    application = PlayerRegistrationApplication.objects.filter(user=user).first()
    if (
        application
        and application.trial_status
        == PlayerRegistrationApplication.TrialStatus.SELECTED
        and application.player_id
        and application.player.player_status == PlayerStatus.ACTIVE
    ):
        return DashboardMode.PLAYER
    if (
        application
        and application.payment_status
        == PlayerRegistrationApplication.PaymentStatus.VERIFIED
    ):
        return DashboardMode.TRIAL
    return DashboardMode.GUEST


@transaction.atomic
def review_player_payment(payment, reviewer, approve, note=''):
    payment = PlayerPaymentTransaction.objects.select_for_update().select_related(
        'application', 'user'
    ).get(pk=payment.pk)
    if payment.status != PlayerPaymentTransaction.Status.SUBMITTED:
        raise ValueError('This payment has already been processed.')
    payment.status = (
        PlayerPaymentTransaction.Status.VERIFIED
        if approve else PlayerPaymentTransaction.Status.REJECTED
    )
    payment.reviewed_at = timezone.now()
    payment.reviewed_by = reviewer
    payment.review_note = note
    payment.save(
        update_fields=[
            'status', 'reviewed_at', 'reviewed_by', 'review_note'
        ]
    )
    application = payment.application
    application.payment_status = (
        PlayerRegistrationApplication.PaymentStatus.VERIFIED
        if approve else PlayerRegistrationApplication.PaymentStatus.REJECTED
    )
    application.trial_status = (
        PlayerRegistrationApplication.TrialStatus.ELIGIBLE
        if approve else PlayerRegistrationApplication.TrialStatus.LOCKED
    )
    application.status = (
        PlayerRegistrationApplication.Status.PAYMENT_SUBMITTED
        if approve else PlayerRegistrationApplication.Status.PAYMENT_PENDING
    )
    application.save(
        update_fields=['payment_status', 'trial_status', 'status', 'updated_at']
    )
    payment.user.onboarding_state = (
        payment.user.OnboardingState.PLAYER_TRIAL_ELIGIBLE
        if approve else payment.user.OnboardingState.PLAYER_PAYMENT_PENDING
    )
    payment.user.save(update_fields=['onboarding_state'])
    return payment


@transaction.atomic
def apply_trial_decision(invitation, evaluator, evaluation_data):
    application = invitation.application
    recommendation = evaluation_data['recommendation']
    evaluation, _ = PlayerTrialEvaluation.objects.update_or_create(
        invitation=invitation,
        defaults={
            **evaluation_data,
            'evaluated_by': evaluator,
        },
    )
    status_map = {
        PlayerTrialEvaluation.Recommendation.SELECT:
            PlayerRegistrationApplication.TrialStatus.SELECTED,
        PlayerTrialEvaluation.Recommendation.REJECT:
            PlayerRegistrationApplication.TrialStatus.REJECTED,
        PlayerTrialEvaluation.Recommendation.WAITLIST:
            PlayerRegistrationApplication.TrialStatus.WAITLISTED,
    }
    new_status = status_map[recommendation]
    invitation.status = new_status
    invitation.save(update_fields=['status', 'updated_at'])
    application.trial_status = new_status

    if new_status == PlayerRegistrationApplication.TrialStatus.SELECTED:
        player = application.player
        player.tenant = invitation.trial.tenant
        player.player_status = PlayerStatus.ACTIVE
        player.save(update_fields=['tenant', 'player_status', 'updated_at'])
        application.status = PlayerRegistrationApplication.Status.COMPLETED
        application.user.onboarding_state = (
            application.user.OnboardingState.PLAYER_SELECTED
        )
        application.user.user_type = application.user.UserType.PLAYER
        application.user.save(update_fields=['onboarding_state', 'user_type'])

    application.save(update_fields=['trial_status', 'status', 'updated_at'])
    return evaluation
