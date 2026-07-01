from django.test import RequestFactory, TestCase, override_settings

from apps.accounts.middleware import TenantMiddleware
from apps.accounts.models import Role, Tenant, User, UserTenant
from apps.accounts.policies import has_capability


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


class RoleCapabilityPolicyTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name='Policy League', subdomain='policy')
        self.factory = RequestFactory()

    def test_role_capability_matrix(self):
        expected = {
            'TENANT_ADMIN': {'players.manage', 'teams.manage', 'tournaments.manage', 'venues.manage', 'scoring.manage', 'auctions.manage'},
            'TOURNAMENT_MANAGER': {'tournaments.manage'},
            'TEAM_MANAGER': {'players.manage', 'teams.manage'},
            'SCORER': {'scoring.manage'},
            'AUCTION_MANAGER': {'auctions.manage'},
            'VENUE_MANAGER': {'venues.manage'},
            'VIEWER': set(),
        }
        capabilities = {
            'players.manage', 'teams.manage', 'tournaments.manage',
            'venues.manage', 'scoring.manage', 'auctions.manage',
        }
        for index, (role_code, allowed) in enumerate(expected.items()):
            with self.subTest(role=role_code):
                user = User.objects.create_user(
                    email=f'role-{index}@example.com', password='strong-test-password'
                )
                role = Role.objects.create(
                    tenant=self.tenant,
                    name=role_code.replace('_', ' ').title(),
                    code=role_code,
                )
                UserTenant.objects.create(
                    user=user, tenant=self.tenant, role=role, is_active=True
                )
                request = self.factory.get('/')
                request.user = user
                request.tenant = self.tenant
                for capability in capabilities:
                    self.assertEqual(
                        has_capability(request, capability),
                        capability in allowed,
                    )

    def test_missing_role_and_inactive_membership_are_denied(self):
        user = User.objects.create_user(
            email='missing-role@example.com', password='strong-test-password'
        )
        membership = UserTenant.objects.create(
            user=user, tenant=self.tenant, role=None, is_active=True
        )
        request = self.factory.get('/')
        request.user = user
        request.tenant = self.tenant

        self.assertFalse(has_capability(request, 'players.manage'))
        membership.is_active = False
        membership.save(update_fields=['is_active'])
        self.assertFalse(has_capability(request, 'players.manage'))
