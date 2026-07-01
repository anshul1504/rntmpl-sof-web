from django.test import TestCase

from apps.accounts.models import Tenant, User
from apps.players.models import PlayerProfile
from apps.scoring.models import (
    Ball,
    BatterInnings,
    BowlerFigures,
    Innings,
    InningStatus,
    MatchState,
    ScoreCorrection,
)
from apps.scoring.services import rebuild_innings_projections, undo_last_ball
from apps.scoring.frontend_views import complete_current_innings
from apps.teams.models import Team
from apps.tournaments.models import (
    Tournament,
    TournamentFormat,
    TournamentMatch,
    TournamentTeam,
    MatchSetup,
    TournamentPointsTable,
)


class ScoringCorrectionTests(TestCase):
    def setUp(self):
        tenant = Tenant.objects.create(name='Scoring League')
        format_record = TournamentFormat.objects.create(
            name='Scoring T20', code='SCR-T20', slug='scr-t20'
        )
        tournament = Tournament.objects.create(
            tenant=tenant,
            name='Scoring Cup',
            slug='scoring-cup',
            format=format_record,
        )
        self.batting_team = TournamentTeam.objects.create(
            tournament=tournament,
            team=Team.objects.create(
                tenant=tenant, name='Batting Team', code='BAT-TEAM'
            ),
        )
        self.bowling_team = TournamentTeam.objects.create(
            tournament=tournament,
            team=Team.objects.create(
                tenant=tenant, name='Bowling Team', code='BOWL-TEAM'
            ),
        )
        self.match = TournamentMatch.objects.create(
            tournament=tournament,
            home_team=self.batting_team,
            away_team=self.bowling_team,
            match_number=1,
        )
        self.striker = PlayerProfile.objects.create(
            tenant=tenant, first_name='Strike', last_name='Batter'
        )
        self.non_striker = PlayerProfile.objects.create(
            tenant=tenant, first_name='Non', last_name='Striker'
        )
        self.bowler = PlayerProfile.objects.create(
            tenant=tenant, first_name='Main', last_name='Bowler'
        )
        self.innings = Innings.objects.create(
            match=self.match,
            batting_team=self.batting_team,
            bowling_team=self.bowling_team,
            innings_number=1,
            status=InningStatus.IN_PROGRESS,
        )
        self.state = MatchState.objects.create(
            match=self.match,
            current_innings=self.innings,
            batting_team=self.batting_team,
            bowling_team=self.bowling_team,
            striker=self.striker,
            non_striker=self.non_striker,
            current_bowler=self.bowler,
            is_live=True,
        )
        self.user = User.objects.create_user(
            email='scorer@example.com', password='strong-test-password'
        )
        self.setup = MatchSetup.objects.create(
            match=self.match,
            toss_winner=self.batting_team,
            toss_decision=MatchSetup.TossDecision.BAT,
            lifecycle=MatchSetup.Lifecycle.LIVE,
        )

    def _ball(self, number, runs):
        return Ball.objects.create(
            innings=self.innings,
            match=self.match,
            over_number=1,
            ball_number_in_over=number,
            ball_number_in_innings=number,
            bowler=self.bowler,
            striker=self.striker,
            non_striker=self.non_striker,
            runs_from_bat=runs,
        )

    def test_undo_removes_only_last_delivery_and_rebuilds_projections(self):
        first = self._ball(1, 4)
        last = self._ball(2, 2)
        rebuild_innings_projections(self.innings)

        original = undo_last_ball(
            self.match, self.user, 'Second ball was entered incorrectly'
        )

        self.innings.refresh_from_db()
        self.state.refresh_from_db()
        self.assertEqual(original['ball_id'], last.pk)
        self.assertTrue(Ball.objects.filter(pk=first.pk).exists())
        self.assertFalse(Ball.objects.filter(pk=last.pk).exists())
        self.assertEqual(self.innings.total_runs, 4)
        self.assertEqual(self.state.runs, 4)
        self.assertEqual(BatterInnings.objects.get(innings=self.innings).runs, 4)
        self.assertEqual(
            BowlerFigures.objects.get(innings=self.innings).runs_conceded, 4
        )
        self.assertEqual(ScoreCorrection.objects.count(), 1)

    def test_match_completion_sets_result_and_recalculates_standings(self):
        self.innings.total_runs = 120
        self.innings.total_wickets = 6
        self.innings.total_overs_bowled = 20
        self.innings.status = InningStatus.COMPLETED
        self.innings.save()
        chase = Innings.objects.create(
            match=self.match,
            batting_team=self.bowling_team,
            bowling_team=self.batting_team,
            innings_number=2,
            status=InningStatus.IN_PROGRESS,
            total_runs=121,
            total_wickets=4,
            total_overs_bowled=18,
        )
        self.state.current_innings = chase
        self.state.batting_team = self.bowling_team
        self.state.bowling_team = self.batting_team
        self.state.save()

        completed = complete_current_innings(
            self.match, self.state, self.setup
        )

        self.match.refresh_from_db()
        self.setup.refresh_from_db()
        self.assertTrue(completed)
        self.assertTrue(self.match.is_completed)
        self.assertEqual(self.match.winner, self.bowling_team)
        self.assertEqual(self.match.loser, self.batting_team)
        self.assertEqual(self.setup.lifecycle, MatchSetup.Lifecycle.COMPLETED)
        standings = TournamentPointsTable.objects.filter(group=self.match.group)
        self.assertEqual(standings.count(), 2)
        winner_standing = standings.get(team=self.bowling_team)
        self.assertEqual(winner_standing.matches_won, 1)
