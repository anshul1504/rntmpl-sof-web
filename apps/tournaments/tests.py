from django.test import TestCase

from apps.accounts.models import User
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
