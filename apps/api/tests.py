from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import Tenant, User, UserTenant
from apps.players.models import (
    PlayerProfile,
    PlayerBattingSkill,
    PlayerBowlingSkill,
    PlayerFieldingSkill,
    PlayerContract,
    PlayerTransfer,
    PlayerInjury,
    PlayerAchievement,
    PlayerCareerStats,
)
from apps.teams.models import Team, TeamCategory, TeamType, TeamSeason, TeamSquad
from apps.tournaments.models import Tournament, TournamentFormat, TournamentTeam, TournamentStage, TournamentStageInstance, TournamentGroup, TournamentPointsTable


class ApiAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_players_api_requires_authentication(self):
        response = self.client.get(reverse('api-v1:player-list'))

        self.assertEqual(response.status_code, 401)


class TenantApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='manager@example.com', password='strong-test-password')
        self.tenant = Tenant.objects.create(name='RNT MPL', tenant_type=Tenant.TenantType.LEAGUE)
        self.other_tenant = Tenant.objects.create(name='Other League', tenant_type=Tenant.TenantType.LEAGUE)
        UserTenant.objects.create(user=self.user, tenant=self.tenant, is_primary=True)
        self.client.force_authenticate(self.user)

    def test_tenant_list_is_limited_to_user_memberships(self):
        response = self.client.get(reverse('api-v1:tenant-list'))

        self.assertEqual(response.status_code, 200)
        names = {item['name'] for item in response.json()['results']}
        self.assertEqual(names, {'RNT MPL'})

    def test_my_tenants_returns_membership_context(self):
        response = self.client.get(reverse('api-v1:my-tenant-list'))

        self.assertEqual(response.status_code, 200)
        payload = response.json()['results']
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]['tenant']['name'], 'RNT MPL')
        self.assertTrue(payload[0]['is_primary'])


class CricketDomainApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='viewer@example.com', password='strong-test-password')
        self.tenant = Tenant.objects.create(name='RNT MPL', tenant_type=Tenant.TenantType.LEAGUE)
        self.other_tenant = Tenant.objects.create(name='Other League', tenant_type=Tenant.TenantType.LEAGUE)
        UserTenant.objects.create(user=self.user, tenant=self.tenant, is_primary=True)
        self.client.force_authenticate(self.user)

    def test_player_team_and_tournament_lists_return_data(self):
        player = PlayerProfile.objects.create(tenant=self.tenant, first_name='Virat', last_name='Kohli')
        category = TeamCategory.objects.create(name='Senior')
        team_type = TeamType.objects.create(name='Franchise')
        team = Team.objects.create(
            tenant=self.tenant,
            name='RNT Strikers',
            code='RNT-ST',
            team_category=category,
            team_type=team_type,
        )
        tournament_format = TournamentFormat.objects.create(
            name='Round Robin',
            code='RR',
            slug='round-robin',
        )
        tournament = Tournament.objects.create(
            tenant=self.tenant,
            name='RNT MPL 2026',
            slug='rnt-mpl-2026',
            format=tournament_format,
            year=2026,
        )

        player_response = self.client.get(reverse('api-v1:player-list'))
        team_response = self.client.get(reverse('api-v1:team-list'))
        tournament_response = self.client.get(reverse('api-v1:tournament-list'))

        self.assertEqual(player_response.status_code, 200)
        self.assertEqual(team_response.status_code, 200)
        self.assertEqual(tournament_response.status_code, 200)
        self.assertEqual(player_response.json()['results'][0]['full_name'], player.full_name)
        self.assertEqual(team_response.json()['results'][0]['name'], team.name)
        self.assertEqual(tournament_response.json()['results'][0]['name'], tournament.name)

    def test_domain_lists_are_limited_to_user_tenants(self):
        PlayerProfile.objects.create(tenant=self.tenant, first_name='Allowed', last_name='Player')
        PlayerProfile.objects.create(tenant=self.other_tenant, first_name='Hidden', last_name='Player')
        Team.objects.create(tenant=self.tenant, name='Allowed Team', code='ALLOWED')
        Team.objects.create(tenant=self.other_tenant, name='Hidden Team', code='HIDDEN')
        tournament_format = TournamentFormat.objects.create(name='League', code='LEAGUE', slug='league')
        Tournament.objects.create(
            tenant=self.tenant,
            name='Allowed Tournament',
            slug='allowed-tournament',
            format=tournament_format,
        )
        Tournament.objects.create(
            tenant=self.other_tenant,
            name='Hidden Tournament',
            slug='hidden-tournament',
            format=tournament_format,
        )

        players = self.client.get(reverse('api-v1:player-list')).json()['results']
        teams = self.client.get(reverse('api-v1:team-list')).json()['results']
        tournaments = self.client.get(reverse('api-v1:tournament-list')).json()['results']

        self.assertEqual({item['full_name'] for item in players}, {'Allowed Player'})
        self.assertEqual({item['name'] for item in teams}, {'Allowed Team'})
        self.assertEqual({item['name'] for item in tournaments}, {'Allowed Tournament'})

    def test_user_can_create_records_inside_own_tenant(self):
        category = TeamCategory.objects.create(name='Senior')
        team_type = TeamType.objects.create(name='Franchise')
        tournament_format = TournamentFormat.objects.create(name='League', code='LG', slug='lg')

        player_response = self.client.post(
            reverse('api-v1:player-list'),
            {
                'tenant': self.tenant.id,
                'first_name': 'Allowed',
                'last_name': 'Creator',
                'role': 'BATTER',
            },
            format='json',
        )
        team_response = self.client.post(
            reverse('api-v1:team-list'),
            {
                'tenant': self.tenant.id,
                'name': 'Allowed API Team',
                'code': 'API-ALLOWED',
                'team_category_id': category.id,
                'team_type_id': team_type.id,
            },
            format='json',
        )
        tournament_response = self.client.post(
            reverse('api-v1:tournament-list'),
            {
                'tenant': self.tenant.id,
                'name': 'Allowed API Tournament',
                'slug': 'allowed-api-tournament',
                'format_id': tournament_format.id,
                'year': 2026,
            },
            format='json',
        )

        self.assertEqual(player_response.status_code, 201)
        self.assertEqual(team_response.status_code, 201)
        self.assertEqual(tournament_response.status_code, 201)
        self.assertEqual(PlayerProfile.objects.get(first_name='Allowed').tenant, self.tenant)
        self.assertEqual(Team.objects.get(code='API-ALLOWED').tenant, self.tenant)
        self.assertEqual(Tournament.objects.get(slug='allowed-api-tournament').tenant, self.tenant)

    def test_user_cannot_create_records_inside_another_tenant(self):
        tournament_format = TournamentFormat.objects.create(name='Knockout', code='KO', slug='ko')

        player_response = self.client.post(
            reverse('api-v1:player-list'),
            {'tenant': self.other_tenant.id, 'first_name': 'Blocked'},
            format='json',
        )
        team_response = self.client.post(
            reverse('api-v1:team-list'),
            {'tenant': self.other_tenant.id, 'name': 'Blocked Team', 'code': 'BLOCKED'},
            format='json',
        )
        tournament_response = self.client.post(
            reverse('api-v1:tournament-list'),
            {
                'tenant': self.other_tenant.id,
                'name': 'Blocked Tournament',
                'slug': 'blocked-tournament',
                'format_id': tournament_format.id,
            },
            format='json',
        )

        self.assertEqual(player_response.status_code, 403)
        self.assertEqual(team_response.status_code, 403)
        self.assertEqual(tournament_response.status_code, 403)
        self.assertFalse(PlayerProfile.objects.filter(first_name='Blocked').exists())
        self.assertFalse(Team.objects.filter(code='BLOCKED').exists())
        self.assertFalse(Tournament.objects.filter(slug='blocked-tournament').exists())

    def test_user_cannot_move_existing_record_to_another_tenant(self):
        player = PlayerProfile.objects.create(tenant=self.tenant, first_name='Owned', last_name='Player')

        response = self.client.patch(
            reverse('api-v1:player-detail', args=[player.id]),
            {'tenant': self.other_tenant.id},
            format='json',
        )

        self.assertEqual(response.status_code, 403)
        player.refresh_from_db()
        self.assertEqual(player.tenant, self.tenant)

    def test_user_can_register_team_in_same_tenant_tournament(self):
        tournament_format = TournamentFormat.objects.create(name='League', code='REG-LG', slug='reg-lg')
        tournament = Tournament.objects.create(
            tenant=self.tenant,
            name='Registration League',
            slug='registration-league',
            format=tournament_format,
        )
        team = Team.objects.create(tenant=self.tenant, name='Registration Team', code='REGTEAM')
        captain = PlayerProfile.objects.create(tenant=self.tenant, first_name='Captain', last_name='Player')
        vice_captain = PlayerProfile.objects.create(tenant=self.tenant, first_name='Vice', last_name='Captain')

        response = self.client.post(
            reverse('api-v1:tournament-team-list'),
            {
                'tournament': tournament.id,
                'team_id': team.id,
                'captain_id': captain.id,
                'vice_captain_id': vice_captain.id,
                'seed': 1,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        registration = TournamentTeam.objects.get(tournament=tournament, team=team)
        self.assertEqual(registration.captain, captain)
        self.assertEqual(registration.vice_captain, vice_captain)

    def test_user_cannot_register_cross_tenant_team_in_tournament(self):
        tournament_format = TournamentFormat.objects.create(name='Cup', code='REG-CUP', slug='reg-cup')
        tournament = Tournament.objects.create(
            tenant=self.tenant,
            name='Tenant Cup',
            slug='tenant-cup',
            format=tournament_format,
        )
        other_team = Team.objects.create(tenant=self.other_tenant, name='Other Tenant Team', code='OTHER-REG')

        response = self.client.post(
            reverse('api-v1:tournament-team-list'),
            {'tournament': tournament.id, 'team_id': other_team.id},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(TournamentTeam.objects.filter(tournament=tournament, team=other_team).exists())

    def test_user_cannot_register_team_in_hidden_tenant_tournament(self):
        tournament_format = TournamentFormat.objects.create(name='Shield', code='REG-SH', slug='reg-sh')
        hidden_tournament = Tournament.objects.create(
            tenant=self.other_tenant,
            name='Hidden Shield',
            slug='hidden-shield',
            format=tournament_format,
        )
        hidden_team = Team.objects.create(tenant=self.other_tenant, name='Hidden Team', code='HIDDEN-REG')

        response = self.client.post(
            reverse('api-v1:tournament-team-list'),
            {'tournament': hidden_tournament.id, 'team_id': hidden_team.id},
            format='json',
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(TournamentTeam.objects.filter(tournament=hidden_tournament, team=hidden_team).exists())


class PlayerSubEntityApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='cricket_admin@example.com', password='strong-test-password')
        self.tenant = Tenant.objects.create(name='RNT MPL', tenant_type=Tenant.TenantType.LEAGUE)
        self.other_tenant = Tenant.objects.create(name='Other League', tenant_type=Tenant.TenantType.LEAGUE)
        UserTenant.objects.create(user=self.user, tenant=self.tenant, is_primary=True)
        self.client.force_authenticate(self.user)

        self.player = PlayerProfile.objects.create(tenant=self.tenant, first_name='Allowed', last_name='Player')
        self.other_player = PlayerProfile.objects.create(tenant=self.other_tenant, first_name='Hidden', last_name='Player')

    def test_skills_and_stats_limited_to_tenant(self):
        skill = PlayerBattingSkill.objects.create(player=self.player, technique=75)
        other_skill = PlayerBattingSkill.objects.create(player=self.other_player, technique=90)

        response = self.client.get(reverse('api-v1:player-batting-skill-list'))
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], skill.id)

    def test_user_cannot_create_sub_entity_for_cross_tenant_player(self):
        team = Team.objects.create(tenant=self.tenant, name='My Team', code='MYTEAM')
        response = self.client.post(
            reverse('api-v1:player-contract-list'),
            {
                'player': self.other_player.id,
                'team': team.id,
                'contract_number': 'CON-12345',
            },
            format='json'
        )
        self.assertEqual(response.status_code, 400)


class TeamAndTournamentSubEntityApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='tenant_admin@example.com', password='strong-test-password')
        self.tenant = Tenant.objects.create(name='RNT MPL', tenant_type=Tenant.TenantType.LEAGUE)
        self.other_tenant = Tenant.objects.create(name='Other League', tenant_type=Tenant.TenantType.LEAGUE)
        UserTenant.objects.create(user=self.user, tenant=self.tenant, is_primary=True)
        self.client.force_authenticate(self.user)

        # Tenant-specific team/tournament
        self.team = Team.objects.create(tenant=self.tenant, name='Tenant Team', code='TTEAM')
        self.other_team = Team.objects.create(tenant=self.other_tenant, name='Other Team', code='OTEAM')

        self.format = TournamentFormat.objects.create(name='League', code='LEAGUE', slug='league')
        self.tournament = Tournament.objects.create(tenant=self.tenant, name='Tenant Tourney', slug='tenant-tourney', format=self.format)
        self.other_tournament = Tournament.objects.create(tenant=self.other_tenant, name='Other Tourney', slug='other-tourney', format=self.format)

    def test_team_season_scoping(self):
        # List scoping
        ts1 = TeamSeason.objects.create(team=self.team, year=2026, season='WINTER')
        ts2 = TeamSeason.objects.create(team=self.other_team, year=2026, season='WINTER')

        response = self.client.get(reverse('api-v1:team-season-list'))
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], ts1.id)

        # Read scoping
        detail_response = self.client.get(reverse('api-v1:team-season-detail', args=[ts2.id]))
        self.assertEqual(detail_response.status_code, 404)

        # Write access scoping (try to create/update team season under other team)
        create_response = self.client.post(
            reverse('api-v1:team-season-list'),
            {
                'team': self.other_team.id,
                'year': 2027,
                'season': 'WINTER',
            },
            format='json'
        )
        # Should raise 403 PermissionDenied as it doesn't belong to the user's tenant
        self.assertEqual(create_response.status_code, 403)

    def test_tournament_stage_instance_and_points_table_scoping(self):
        stage = TournamentStage.objects.create(name='Group Stage', format=self.format)
        tsi1 = TournamentStageInstance.objects.create(tournament=self.tournament, stage=stage, name='T1 Group Stage')
        tsi2 = TournamentStageInstance.objects.create(tournament=self.other_tournament, stage=stage, name='T2 Group Stage')

        # Verify Stage Instance scoping
        response = self.client.get(reverse('api-v1:tournament-stage-instance-list'))
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], tsi1.id)

        # Create tournament group for stage instance
        group1 = TournamentGroup.objects.create(stage_instance=tsi1, name='Group A')
        group2 = TournamentGroup.objects.create(stage_instance=tsi2, name='Group B')

        # Verify Group scoping
        response_g = self.client.get(reverse('api-v1:tournament-group-list'))
        self.assertEqual(response_g.status_code, 200)
        results_g = response_g.json()['results']
        self.assertEqual(len(results_g), 1)
        self.assertEqual(results_g[0]['id'], group1.id)


