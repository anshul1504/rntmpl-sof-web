from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.accounts.models import Role, Tenant, UserTenant
from apps.teams.models import Team

User = get_user_model()


class TeamFrontendViewsTestCase(TestCase):
    def setUp(self):
        # Create Users
        self.user = User.objects.create_user(email='team_member@example.com', password='password123')
        self.other_user = User.objects.create_user(email='other_team@example.com', password='password123')

        # Create Tenants
        self.tenant = Tenant.objects.create(name='Cricket Academy', subdomain='cricket')
        self.other_tenant = Tenant.objects.create(name='Other Academy', subdomain='other')

        # Create Memberships
        manager_role = Role.objects.create(tenant=self.tenant, name='Team Manager', code='TEAM_MANAGER')
        UserTenant.objects.create(user=self.user, tenant=self.tenant, role=manager_role, is_primary=True, is_active=True)
        other_manager_role = Role.objects.create(tenant=self.other_tenant, name='Team Manager', code='TEAM_MANAGER')
        UserTenant.objects.create(user=self.other_user, tenant=self.other_tenant, role=other_manager_role, is_primary=True, is_active=True)

        # Create Teams
        self.team = Team.objects.create(
            tenant=self.tenant,
            name='Mumbai Lions',
            code='MUM-LIONS',
            short_name='MUM',
            abbreviation='ML',
            is_active=True,
        )

        self.other_team = Team.objects.create(
            tenant=self.other_tenant,
            name='Delhi Eagles',
            code='DEL-EAGLES',
            short_name='DEL',
            abbreviation='DE',
            is_active=True,
        )

    def _login_with_tenant(self, user, tenant):
        """Use force_login to bypass django-axes, set tenant in session."""
        self.client.force_login(user)
        session = self.client.session
        session['active_tenant_id'] = str(tenant.id)
        session.save()

    def test_team_list_view_scoped_to_active_tenant(self):
        self._login_with_tenant(self.user, self.tenant)
        response = self.client.get(reverse('teams:team-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mumbai Lions')
        self.assertNotContains(response, 'Delhi Eagles')

    def test_team_detail_view_scoped_to_active_tenant(self):
        self._login_with_tenant(self.user, self.tenant)

        response = self.client.get(reverse('teams:team-detail', args=[self.team.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mumbai Lions')

        # Other tenant's team should 404
        response_other = self.client.get(reverse('teams:team-detail', args=[self.other_team.pk]))
        self.assertEqual(response_other.status_code, 404)

    def test_team_create_view_links_to_active_tenant(self):
        self._login_with_tenant(self.user, self.tenant)
        post_data = {
            'name': 'Pune Warriors',
            'code': 'PUN-WAR',
            'short_name': 'PUN',
            'abbreviation': 'PW',
            'country': 'India',
        }
        response = self.client.post(reverse('teams:team-create'), data=post_data)
        self.assertEqual(response.status_code, 302)

        new_team = Team.objects.get(code='PUN-WAR')
        self.assertEqual(new_team.tenant, self.tenant)

    def test_unauthenticated_redirect_to_login(self):
        response = self.client.get(reverse('teams:team-list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/', response.url)

    def test_search_functionality(self):
        self._login_with_tenant(self.user, self.tenant)
        response = self.client.get(reverse('teams:team-list'), {'search': 'Mumbai'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mumbai Lions')

    def test_status_filter(self):
        self._login_with_tenant(self.user, self.tenant)
        # Create an inactive team
        Team.objects.create(
            tenant=self.tenant,
            name='Retired XI',
            code='RET-XI',
            is_active=False,
        )
        response = self.client.get(reverse('teams:team-list'), {'status': 'active'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mumbai Lions')
        self.assertNotContains(response, 'Retired XI')


