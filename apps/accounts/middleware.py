from django.utils.deprecation import MiddlewareMixin

from apps.accounts.models import Tenant, UserTenant


class TenantMiddleware(MiddlewareMixin):
    """
    Resolve the current tenant from the request host or the authenticated user's
    primary membership. Public routes may legitimately have no tenant.
    """

    def process_request(self, request):
        request.tenant = self.get_tenant(request)
        if request.tenant and request.user.is_authenticated:
            active_tenant_id = request.session.get('active_tenant_id')
            if active_tenant_id != str(request.tenant.id):
                request.session['active_tenant_id'] = str(request.tenant.id)

    def get_tenant(self, request):
        tenant = self.get_tenant_from_host(request)
        if tenant:
            return tenant

        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return None

        session_tenant_id = request.session.get('active_tenant_id')
        memberships = UserTenant.objects.select_related('tenant').filter(
            user=user,
            is_active=True,
            tenant__is_deleted=False,
        )
        if session_tenant_id:
            selected = memberships.filter(tenant_id=session_tenant_id).first()
            if selected:
                return selected.tenant
            request.session.pop('active_tenant_id', None)

        membership = (
            memberships
            .order_by('-is_primary', 'joined_at')
            .first()
        )
        return membership.tenant if membership else None

    def get_tenant_from_host(self, request):
        host = request.get_host().split(':', 1)[0].lower()
        if not host or host in {'localhost', '127.0.0.1', '0.0.0.0'}:
            return None

        tenant = Tenant.objects.filter(domain__iexact=host).first()
        if tenant:
            return tenant

        subdomain = host.split('.', 1)[0]
        if subdomain and subdomain != 'www':
            return Tenant.objects.filter(subdomain__iexact=subdomain).first()

        return None
