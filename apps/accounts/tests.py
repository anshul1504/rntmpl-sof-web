from django.test import TestCase, override_settings

from apps.accounts.middleware import TenantMiddleware
from apps.accounts.models import Tenant, User, UserTenant


class StartupSmokeTests(TestCase):
    def test_root_endpoint_renders_demo_landing_page(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'RNTMPL')


class AccountFoundationTests(TestCase):
    def test_user_can_join_tenant(self):
        user = User.objects.create_user(email='owner@example.com', password='strong-test-password')
        tenant = Tenant.objects.create(name='RNT MPL', tenant_type=Tenant.TenantType.LEAGUE)

        membership = UserTenant.objects.create(user=user, tenant=tenant, is_primary=True)

        self.assertEqual(membership.user, user)
        self.assertEqual(membership.tenant, tenant)
        self.assertTrue(membership.is_primary)


class TenantMiddlewareTests(TestCase):
    def setUp(self):
        self.middleware = TenantMiddleware(lambda request: None)

    @override_settings(ALLOWED_HOSTS=['testserver', 'rntmpl.test'])
    def test_resolves_tenant_by_custom_domain(self):
        tenant = Tenant.objects.create(
            name='RNT MPL',
            tenant_type=Tenant.TenantType.LEAGUE,
            domain='rntmpl.test',
        )
        request = self.client.request().wsgi_request
        request.META['HTTP_HOST'] = 'rntmpl.test'

        resolved = self.middleware.get_tenant(request)

        self.assertEqual(resolved, tenant)

    def test_resolves_authenticated_users_primary_tenant(self):
        primary = Tenant.objects.create(name='Primary League', tenant_type=Tenant.TenantType.LEAGUE)
        secondary = Tenant.objects.create(name='Secondary League', tenant_type=Tenant.TenantType.LEAGUE)
        user = User.objects.create_user(email='manager@example.com', password='strong-test-password')
        UserTenant.objects.create(user=user, tenant=secondary, is_primary=False)
        UserTenant.objects.create(user=user, tenant=primary, is_primary=True)

        request = self.client.request().wsgi_request
        request.META['HTTP_HOST'] = 'localhost'
        request.user = user

        resolved = self.middleware.get_tenant(request)

        self.assertEqual(resolved, primary)
