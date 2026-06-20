from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.accounts.models import Role, Tenant, UserTenant
from apps.players.models import PlayerProfile, PlayerRole

User = get_user_model()


class PlayerFrontendViewsTestCase(TestCase):
    def setUp(self):
        # Create Users
        self.user = User.objects.create_user(email='tenant_member@example.com', password='password123')
        self.other_user = User.objects.create_user(email='other_member@example.com', password='password123')
        
        # Create Tenants
        self.tenant = Tenant.objects.create(name='Tenant Academy', subdomain='tenant')
        self.other_tenant = Tenant.objects.create(name='Other Academy', subdomain='other')
        
        # Create Memberships
        manager_role = Role.objects.create(tenant=self.tenant, name='Team Manager', code='TEAM_MANAGER')
        UserTenant.objects.create(user=self.user, tenant=self.tenant, role=manager_role, is_primary=True, is_active=True)
        other_manager_role = Role.objects.create(tenant=self.other_tenant, name='Team Manager', code='TEAM_MANAGER')
        UserTenant.objects.create(user=self.other_user, tenant=self.other_tenant, role=other_manager_role, is_primary=True, is_active=True)
        
        # Create Players
        self.player = PlayerProfile.objects.create(
            tenant=self.tenant,
            first_name='Virat',
            last_name='Kohli',
            role=PlayerRole.BATTER,
            jersey_number=18
        )
        
        self.other_player = PlayerProfile.objects.create(
            tenant=self.other_tenant,
            first_name='Steve',
            last_name='Smith',
            role=PlayerRole.BATTER,
            jersey_number=49
        )

    def _login_with_tenant(self, user, tenant):
        """
        Use force_login to bypass django-axes authentication backend,
        and set the active_tenant_id in the session.
        """
        self.client.force_login(user)
        session = self.client.session
        session['active_tenant_id'] = str(tenant.id)
        session.save()

    def test_player_list_view_scoped_to_active_tenant(self):
        self._login_with_tenant(self.user, self.tenant)
        response = self.client.get(reverse('players:player-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Virat')
        self.assertNotContains(response, 'Steve Smith')

    def test_player_detail_view_scoped_to_active_tenant(self):
        self._login_with_tenant(self.user, self.tenant)
        
        # Detail view of owned player profile should work
        response = self.client.get(reverse('players:player-detail', args=[self.player.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Virat')
        
        # Detail view of player profile belonging to other tenant should return 404
        response_other = self.client.get(reverse('players:player-detail', args=[self.other_player.pk]))
        self.assertEqual(response_other.status_code, 404)

    def test_player_create_view_links_to_active_tenant(self):
        self._login_with_tenant(self.user, self.tenant)
        post_data = {
            'first_name': 'Rohit',
            'last_name': 'Sharma',
            'role': PlayerRole.BATTER,
            'batting_style': 'RIGHT_HAND',
            'jersey_number': 45,
            'gender': 'MALE',
            'nationality': 'India',
            'player_status': 'ACTIVE',
            'country': 'India',
        }
        response = self.client.post(reverse('players:player-create'), data=post_data)
        # Should redirect to list view on success
        self.assertEqual(response.status_code, 302)
        
        # Verify Rohit Sharma was created under self.tenant
        new_player = PlayerProfile.objects.get(first_name='Rohit')
        self.assertEqual(new_player.tenant, self.tenant)

    def test_unauthenticated_redirect_to_login(self):
        """Anonymous users should be redirected to login."""
        response = self.client.get(reverse('players:player-list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/', response.url)

    def test_search_functionality(self):
        """Search should filter players by name."""
        self._login_with_tenant(self.user, self.tenant)
        response = self.client.get(reverse('players:player-list'), {'search': 'Virat'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Virat')

    def test_role_filter_functionality(self):
        """Role filter should filter players by role."""
        self._login_with_tenant(self.user, self.tenant)
        # Add a bowler to test filter distinction
        PlayerProfile.objects.create(
            tenant=self.tenant,
            first_name='Jasprit',
            last_name='Bumrah',
            role=PlayerRole.BOWLER,
            jersey_number=93
        )
        response = self.client.get(reverse('players:player-list'), {'role': 'BOWLER'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Jasprit')
        self.assertNotContains(response, 'Virat')


