from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count

from apps.accounts.models import (
    LoginHistory,
    NotificationOutbox,
    OrganizerApplication,
    OrganizationPlan,
    OrganizationSubscription,
    OTPVerification,
    PermissionMatrix,
    PaymentLedger,
    PaymentReceipt,
    PaymentReconciliation,
    PaymentWebhookEvent,
    Role,
    Tenant,
    User,
    UserActivityLog,
    UserAddress,
    UserDevice,
    UserDocument,
    UserSession,
    UserTenant,
)
from apps.accounts.saas import (
    mark_payment_refunded,
    process_notification_outbox,
    reactivate_subscription,
    review_organizer_application,
    suspend_subscription,
)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ('-date_joined',)
    list_display = ('email', 'full_name', 'user_type_badge', 'is_verified', 'is_2fa_enabled', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_verified', 'is_2fa_enabled', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('email', 'full_name', 'phone', 'aadhaar_number_hash', 'pan_number_hash')
    readonly_fields = ('date_joined', 'last_login')
    date_hierarchy = 'date_joined'

    fieldsets = (
        ('Authentication', {'fields': ('email', 'password', 'username')}),
        ('Personal Info', {
            'fields': ('full_name', 'phone', 'date_of_birth', 'gender', 'photo')
        }),
        ('Cricket Platform', {
            'fields': ('user_type', 'is_verified', 'subscription_plan', 'subscription_end')
        }),
        ('Verification', {
            'fields': ('email_verified', 'phone_verified', 'is_2fa_enabled', 'two_factor_method',
                      'aadhaar_verified', 'pan_verified')
        }),
        ('Security', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'login_attempts', 'is_locked',
                      'locked_until', 'last_login_ip', 'last_login_device', 'last_password_change'),
            'classes': ('collapse',)
        }),
        ('Social Auth', {'fields': ('google_id', 'facebook_id'), 'classes': ('collapse',)}),
        ('Timestamps', {'fields': ('date_joined', 'last_login'), 'classes': ('collapse',)}),
        ('Preferences', {'fields': ('metadata', 'preferences'), 'classes': ('collapse',)}),
    )

    def user_type_badge(self, obj):
        """Display user type as colored badge."""
        colors = {
            'SUPER_ADMIN': '#dc2626',
            'PLATFORM_ADMIN': '#f97316',
            'PLAYER': '#3b82f6',
            'FAN': '#8b5cf6',
        }
        color = colors.get(obj.user_type, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px;">{}</span>',
            color, obj.get_user_type_display()
        )
    user_type_badge.short_description = 'Type'


@admin.register(OrganizationPlan)
class OrganizationPlanAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'code', 'price', 'billing_cycle', 'max_tournaments',
        'max_teams', 'max_players', 'max_venues', 'max_users', 'is_active',
    )
    list_editable = ('is_active',)
    list_filter = ('billing_cycle', 'is_active')
    search_fields = ('name', 'code', 'description')
    prepopulated_fields = {'code': ('name',)}


@admin.register(OrganizerApplication)
class OrganizerApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'organization_name', 'plan', 'contact_person', 'email',
        'tenant_type', 'status', 'tenant', 'created_at',
    )
    list_filter = ('status', 'tenant_type', 'plan', 'created_at')
    search_fields = ('organization_name', 'contact_person', 'email', 'phone')
    readonly_fields = (
        'user', 'tenant', 'reviewed_by', 'reviewed_at', 'provisioned_at',
        'created_at', 'updated_at',
    )
    actions = ('approve_and_provision', 'reject_applications')

    @admin.action(description='Approve and provision selected organizer applications')
    def approve_and_provision(self, request, queryset):
        for application in queryset:
            if application.status in {
                OrganizerApplication.Status.SUBMITTED,
                OrganizerApplication.Status.UNDER_REVIEW,
                OrganizerApplication.Status.APPROVED,
            }:
                review_organizer_application(application, request.user, True)

    @admin.action(description='Reject selected organizer applications')
    def reject_applications(self, request, queryset):
        for application in queryset:
            if application.status in {
                OrganizerApplication.Status.SUBMITTED,
                OrganizerApplication.Status.UNDER_REVIEW,
            }:
                review_organizer_application(application, request.user, False)


@admin.register(OrganizationSubscription)
class OrganizationSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'tenant', 'plan', 'status', 'current_period_start',
        'current_period_end', 'cancel_at_period_end',
    )
    list_filter = ('status', 'plan', 'cancel_at_period_end')
    search_fields = ('tenant__name', 'organizer_application__organization_name')
    readonly_fields = ('created_at', 'updated_at', 'suspended_at')
    actions = ('suspend_selected', 'reactivate_selected')

    @admin.action(description='Suspend selected subscriptions')
    def suspend_selected(self, request, queryset):
        for subscription in queryset:
            if subscription.status != OrganizationSubscription.Status.SUSPENDED:
                suspend_subscription(subscription, reason='Suspended by platform admin.')

    @admin.action(description='Reactivate selected subscriptions')
    def reactivate_selected(self, request, queryset):
        for subscription in queryset:
            if subscription.status == OrganizationSubscription.Status.SUSPENDED:
                reactivate_subscription(subscription)


@admin.register(PaymentLedger)
class PaymentLedgerAdmin(admin.ModelAdmin):
    list_display = (
        'reference', 'purpose', 'provider', 'status', 'user',
        'tenant', 'amount', 'created_at',
    )
    list_filter = ('purpose', 'provider', 'status', 'created_at')
    search_fields = (
        'reference', 'gateway_order_id', 'gateway_payment_id',
        'user__email', 'tenant__name',
    )
    readonly_fields = ('created_at', 'updated_at', 'gateway_payload')
    actions = ('mark_refunded',)

    @admin.action(description='Mark selected payments as refunded')
    def mark_refunded(self, request, queryset):
        for payment in queryset:
            if payment.status == PaymentLedger.Status.PAID:
                mark_payment_refunded(payment, reason='Refund recorded by platform admin.')


@admin.register(PaymentReceipt)
class PaymentReceiptAdmin(admin.ModelAdmin):
    list_display = (
        'receipt_number', 'billed_to_name', 'billed_to_email',
        'amount', 'currency', 'issued_at',
    )
    list_filter = ('currency', 'issued_at')
    search_fields = ('receipt_number', 'billed_to_name', 'billed_to_email', 'payment__reference')
    readonly_fields = tuple(field.name for field in PaymentReceipt._meta.fields)


@admin.register(PaymentReconciliation)
class PaymentReconciliationAdmin(admin.ModelAdmin):
    list_display = (
        'payment', 'status', 'gateway_amount', 'gateway_currency',
        'reconciled_at',
    )
    list_filter = ('status', 'gateway_currency', 'reconciled_at')
    search_fields = ('payment__reference', 'payment__gateway_payment_id', 'notes')
    readonly_fields = ('created_at', 'updated_at', 'gateway_payload')


@admin.register(PaymentWebhookEvent)
class PaymentWebhookEventAdmin(admin.ModelAdmin):
    list_display = ('provider', 'event_type', 'event_id', 'is_valid', 'processed_at', 'created_at')
    list_filter = ('provider', 'event_type', 'is_valid', 'processed_at')
    search_fields = ('event_id', 'event_type')
    readonly_fields = ('payload', 'signature', 'processed_at', 'processing_error', 'created_at', 'updated_at')


@admin.register(NotificationOutbox)
class NotificationOutboxAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'channel', 'recipient', 'status', 'attempts', 'created_at')
    list_filter = ('event_type', 'channel', 'status', 'created_at')
    search_fields = ('recipient', 'subject', 'body')
    readonly_fields = ('payload', 'created_at', 'updated_at', 'sent_at')
    actions = ('process_pending_notifications',)

    @admin.action(description='Process pending notification outbox')
    def process_pending_notifications(self, request, queryset):
        process_notification_outbox(limit=queryset.count() or 25)


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'tenant_type', 'domain', 'subdomain', 'members_count', 'subscription_plan', 'verified', 'status', 'created_at')
    list_filter = ('tenant_type', 'subscription_plan', 'verified', 'status', 'created_at')
    search_fields = ('name', 'domain', 'subdomain', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at', 'id', 'members_count_detail')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Basic Info', {'fields': ('name', 'tenant_type', 'id')}),
        ('Domain & Subdomain', {'fields': ('domain', 'subdomain', 'logo', 'favicon')}),
        ('Branding', {'fields': ('primary_color', 'secondary_color', 'custom_css')}),
        ('Visibility', {'fields': ('is_public', 'verified', 'is_featured')}),
        ('Subscription', {
            'fields': ('subscription_plan', 'subscription_start', 'subscription_end')
        }),
        ('Limits', {
            'fields': ('max_users', 'max_teams', 'storage_limit_mb'),
            'classes': ('collapse',)
        }),
        ('Metadata', {'fields': ('metadata',), 'classes': ('collapse',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def members_count(self, obj):
        """Count active members."""
        count = obj.members.filter(is_active=True).count()
        return format_html('<strong>{}</strong>', count)
    members_count.short_description = 'Members'

    def members_count_detail(self, obj):
        """Display member count in readonly field."""
        active = obj.members.filter(is_active=True).count()
        total = obj.members.count()
        return f"{active} active / {total} total"


@admin.register(UserTenant)
class UserTenantAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'tenant_name', 'role_name', 'is_primary_badge', 'is_active_badge', 'joined_at')
    list_filter = ('is_primary', 'is_active', 'tenant__tenant_type', 'joined_at')
    search_fields = ('user__email', 'tenant__name', 'role__name')
    autocomplete_fields = ('user', 'tenant', 'role')
    readonly_fields = ('joined_at',)
    date_hierarchy = 'joined_at'

    def user_email(self, obj):
        """Get user email."""
        return obj.user.email
    user_email.short_description = 'User'

    def tenant_name(self, obj):
        """Get tenant name."""
        return obj.tenant.name
    tenant_name.short_description = 'Tenant'

    def role_name(self, obj):
        """Get role name."""
        return obj.role.name if obj.role else '—'
    role_name.short_description = 'Role'

    def is_primary_badge(self, obj):
        """Display primary status as badge."""
        if obj.is_primary:
            return format_html('<span style="background-color: #10b981; color: white; padding: 3px 8px; border-radius: 4px;">Primary</span>')
        return '—'
    is_primary_badge.short_description = 'Primary'

    def is_active_badge(self, obj):
        """Display active status as badge."""
        color = '#10b981' if obj.is_active else '#ef4444'
        label = 'Active' if obj.is_active else 'Inactive'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px;">{}</span>',
            color, label
        )
    is_active_badge.short_description = 'Status'


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'tenant_scope', 'category', 'is_system_badge')
    list_filter = ('category', 'is_system', 'tenant')
    search_fields = ('name', 'code', 'tenant__name')
    autocomplete_fields = ('tenant',)
    filter_horizontal = ('permissions',)

    fieldsets = (
        ('Basic Info', {'fields': ('name', 'code', 'category')}),
        ('Scope', {'fields': ('tenant',), 'description': 'Leave empty for platform-wide roles'}),
        ('System', {'fields': ('is_system', 'description')}),
        ('Permissions', {'fields': ('permissions',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def tenant_scope(self, obj):
        """Display tenant scope."""
        if obj.tenant:
            return f"{obj.tenant.name} (tenant-scoped)"
        return "Platform-wide"
    tenant_scope.short_description = 'Scope'

    def is_system_badge(self, obj):
        """Display system status."""
        if obj.is_system:
            return format_html('<span style="background-color: #3b82f6; color: white; padding: 3px 8px; border-radius: 4px;">System</span>')
        return 'Custom'
    is_system_badge.short_description = 'Type'


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'status_badge', 'ip_address', 'device_type', 'created_at')
    list_filter = ('status', 'created_at', 'device_type')
    search_fields = ('user__email', 'ip_address', 'device_name')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'

    def status_badge(self, obj):
        colors = {
            'SUCCESS': '#10b981',
            'FAILED': '#ef4444',
            'LOCKED': '#f97316',
            'OTP_REQUIRED': '#3b82f6',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ('target', 'purpose', 'attempts', 'expires_at', 'is_used', 'created_at')
    list_filter = ('purpose', 'expires_at', 'created_at')
    search_fields = ('email', 'phone', 'otp_hash')
    readonly_fields = ('otp_hash', 'created_at')
    date_hierarchy = 'created_at'

    def target(self, obj):
        return obj.email or obj.phone
    target.short_description = 'Email/Phone'

    def is_used(self, obj):
        used = hasattr(obj, 'used_at') and obj.used_at is not None
        color = '#10b981' if used else '#ef4444'
        label = 'Used' if used else 'Unused'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px;">{}</span>',
            color, label
        )
    is_used.short_description = 'Status'


@admin.register(PermissionMatrix)
class PermissionMatrixAdmin(admin.ModelAdmin):
    list_display = ('role', 'content_type_model', 'action', 'is_allowed_badge')
    list_filter = ('role', 'action', 'is_allowed')
    search_fields = ('role__name', 'content_type_model')

    def is_allowed_badge(self, obj):
        color = '#10b981' if obj.is_allowed else '#ef4444'
        label = 'Allowed' if obj.is_allowed else 'Denied'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px;">{}</span>',
            color, label
        )
    is_allowed_badge.short_description = 'Permission'


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'is_active_badge', 'ip_address', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__email', 'ip_address', 'session_key')
    readonly_fields = ('session_key', 'created_at', 'updated_at')

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'

    def is_active_badge(self, obj):
        color = '#10b981' if obj.is_active else '#ef4444'
        label = 'Active' if obj.is_active else 'Inactive'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px;">{}</span>',
            color, label
        )
    is_active_badge.short_description = 'Status'


admin.site.register(UserActivityLog)
admin.site.register(UserAddress)
admin.site.register(UserDocument)
admin.site.register(UserDevice)
