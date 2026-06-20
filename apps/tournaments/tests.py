from datetime import date

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Role, User, UserTenant
from apps.players.models import PlayerProfile
from apps.teams.models import Team
from apps.tournaments.models import (
    MatchOfficialAssignment,
    MatchPlayingXI,
    MatchSetup,
    Tournament,
    TournamentFormat,
    TournamentMatch,
    TournamentOfficial,
    TournamentPlayer,
    TournamentTeam,
)
from apps.accounts.models import Tenant
from apps.venues.models import Venue


class MatchSetupReadinessTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name='Setup League')
        self.format = TournamentFormat.objects.create(
            name='T20', code='SETUP-T20', slug='setup-t20'
        )
        self.tournament = Tournament.objects.create(
            tenant=self.tenant,
            name='Setup Cup',
            slug='setup-cup',
            format=self.format,
        )
        self.home = TournamentTeam.objects.create(
            tournament=self.tournament,
            team=Team.objects.create(
                tenant=self.tenant, name='Home XI', code='HOME-XI'
            ),
        )
        self.away = TournamentTeam.objects.create(
            tournament=self.tournament,
            team=Team.objects.create(
                tenant=self.tenant, name='Away XI', code='AWAY-XI'
            ),
        )
        self.match = TournamentMatch.objects.create(
            tournament=self.tournament,
            home_team=self.home,
            away_team=self.away,
            match_number=1,
        )
        self.setup = MatchSetup.objects.create(
            match=self.match,
            toss_winner=self.home,
            toss_decision=MatchSetup.TossDecision.BAT,
        )

    def _add_team_xi(self, tournament_team, prefix):
        for index in range(11):
            player = PlayerProfile.objects.create(
                tenant=self.tenant,
                first_name=f'{prefix}{index}',
                last_name='Player',
            )
            TournamentPlayer.objects.create(
                tournament_team=tournament_team,
                player=player,
                is_playing=True,
            )
            MatchPlayingXI.objects.create(
                setup=self.setup,
                tournament_team=tournament_team,
                player=player,
                batting_position=index + 1,
                is_captain=index == 0,
                is_wicket_keeper=index == 1,
            )

    def test_setup_requires_both_xis_and_operational_officials(self):
        self._add_team_xi(self.home, 'H')
        self._add_team_xi(self.away, 'A')
        self.assertFalse(self.setup.is_ready)

        umpire = TournamentOfficial.objects.create(
            tournament=self.tournament,
            official=PlayerProfile.objects.create(
                tenant=self.tenant, first_name='Field', last_name='Umpire'
            ),
            role='UMPIRE',
        )
        scorer = TournamentOfficial.objects.create(
            tournament=self.tournament,
            official=PlayerProfile.objects.create(
                tenant=self.tenant, first_name='Match', last_name='Scorer'
            ),
            role='SCORER',
        )
        MatchOfficialAssignment.objects.create(
            setup=self.setup, tournament_official=umpire, duty='UMPIRE'
        )
        MatchOfficialAssignment.objects.create(
            setup=self.setup, tournament_official=scorer, duty='SCORER'
        )

        self.assertTrue(self.setup.is_ready)


class OrganizerFixtureJourneyTests(TestCase):
    def test_organizer_can_generate_round_robin_fixtures(self):
        tenant = Tenant.objects.create(name='Journey League')
        user = User.objects.create_user(
            email='organizer@example.com', password='strong-test-password'
        )
        role = Role.objects.create(
            tenant=tenant,
            name='Tournament Manager',
            code='TOURNAMENT_MANAGER',
        )
        UserTenant.objects.create(
            user=user, tenant=tenant, role=role, is_primary=True
        )
        self.client.force_login(user)
        session = self.client.session
        session['active_tenant_id'] = str(tenant.id)
        session.save()
        format_record = TournamentFormat.objects.create(
            name='Journey League Format',
            code='JOURNEY-RR',
            slug='journey-rr',
        )
        tournament = Tournament.objects.create(
            tenant=tenant,
            name='Journey Cup',
            slug='journey-cup',
            format=format_record,
        )
        for index in range(4):
            team = Team.objects.create(
                tenant=tenant,
                name=f'Journey Team {index + 1}',
                code=f'JOURNEY-{index + 1}',
            )
            TournamentTeam.objects.create(
                tournament=tournament, team=team, seed=index + 1
            )
        venue = Venue.objects.create(
            tenant=tenant, name='Journey Stadium', city='Indore'
        )

        response = self.client.post(
            reverse('tournaments:fixture-generate', args=[tournament.pk]),
            {
                'start_date': date(2026, 7, 1).isoformat(),
                'first_match_time': '10:00',
                'matches_per_day': 2,
                'days_between_rounds': 1,
                'slot_gap_minutes': 240,
                'venue': venue.pk,
            },
        )

        self.assertEqual(response.status_code, 302)
        fixtures = TournamentMatch.objects.filter(tournament=tournament)
        self.assertEqual(fixtures.count(), 6)
        pairings = {
            frozenset((fixture.home_team_id, fixture.away_team_id))
            for fixture in fixtures
        }
        self.assertEqual(len(pairings), 6)
