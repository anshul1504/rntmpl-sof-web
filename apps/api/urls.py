from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.api.views import (
    MyTenantMembershipViewSet,
    PlayerProfileViewSet,
    PlayerBattingSkillViewSet,
    PlayerBowlingSkillViewSet,
    PlayerFieldingSkillViewSet,
    PlayerContractViewSet,
    PlayerTransferViewSet,
    PlayerInjuryViewSet,
    PlayerAchievementViewSet,
    PlayerCareerStatsViewSet,
    TeamViewSet,
    TenantViewSet,
    TournamentMatchViewSet,
    TournamentTeamViewSet,
    TournamentViewSet,
    TeamSeasonViewSet,
    TeamSquadViewSet,
    TeamStaffViewSet,
    TeamStatViewSet,
    TeamRankingViewSet,
    TeamSponsorshipViewSet,
    TeamAchievementViewSet,
    TeamDocumentViewSet,
    TournamentStageViewSet,
    TournamentStageInstanceViewSet,
    TournamentGroupViewSet,
    TournamentPlayerViewSet,
    TournamentPointsTableViewSet,
    TournamentOfficialViewSet,
    TournamentSponsorViewSet,
    TournamentAwardViewSet,
    TournamentMediaViewSet,
)
from apps.scoring.views import (
    BallViewSet,
    BatterInningsViewSet,
    BowlerFiguresViewSet,
    CommentaryViewSet,
    FallOfWicketViewSet,
    InningsViewSet,
    MatchStateViewSet,
    OverSummaryViewSet,
    RecordBallViewSet,
    ScorecardViewSet,
)
from apps.accounts.auth_urls import urlpatterns as auth_urlpatterns

app_name = 'api'

router = DefaultRouter()
router.register('tenants', TenantViewSet, basename='tenant')
router.register('my-tenants', MyTenantMembershipViewSet, basename='my-tenant')
router.register('players', PlayerProfileViewSet, basename='player')
router.register('player-batting-skills', PlayerBattingSkillViewSet, basename='player-batting-skill')
router.register('player-bowling-skills', PlayerBowlingSkillViewSet, basename='player-bowling-skill')
router.register('player-fielding-skills', PlayerFieldingSkillViewSet, basename='player-fielding-skill')
router.register('player-contracts', PlayerContractViewSet, basename='player-contract')
router.register('player-transfers', PlayerTransferViewSet, basename='player-transfer')
router.register('player-injuries', PlayerInjuryViewSet, basename='player-injury')
router.register('player-achievements', PlayerAchievementViewSet, basename='player-achievement')
router.register('player-career-stats', PlayerCareerStatsViewSet, basename='player-career-stat')
router.register('teams', TeamViewSet, basename='team')
router.register('team-seasons', TeamSeasonViewSet, basename='team-season')
router.register('team-squads', TeamSquadViewSet, basename='team-squad')
router.register('team-staff', TeamStaffViewSet, basename='team-staff')
router.register('team-stats', TeamStatViewSet, basename='team-stat')
router.register('team-rankings', TeamRankingViewSet, basename='team-ranking')
router.register('team-sponsorships', TeamSponsorshipViewSet, basename='team-sponsorship')
router.register('team-achievements', TeamAchievementViewSet, basename='team-achievement')
router.register('team-documents', TeamDocumentViewSet, basename='team-document')

router.register('tournaments', TournamentViewSet, basename='tournament')
router.register('tournament-stages', TournamentStageViewSet, basename='tournament-stage')
router.register('tournament-stage-instances', TournamentStageInstanceViewSet, basename='tournament-stage-instance')
router.register('tournament-groups', TournamentGroupViewSet, basename='tournament-group')
router.register('tournament-teams', TournamentTeamViewSet, basename='tournament-team')
router.register('tournament-players', TournamentPlayerViewSet, basename='tournament-player')
router.register('tournament-points-tables', TournamentPointsTableViewSet, basename='tournament-points-table')
router.register('tournament-officials', TournamentOfficialViewSet, basename='tournament-official')
router.register('tournament-sponsors', TournamentSponsorViewSet, basename='tournament-sponsor')
router.register('tournament-awards', TournamentAwardViewSet, basename='tournament-award')
router.register('tournament-media', TournamentMediaViewSet, basename='tournament-media')
router.register('matches', TournamentMatchViewSet, basename='match')

# Scoring endpoints
router.register('innings', InningsViewSet, basename='inning')
router.register('balls', BallViewSet, basename='ball')
router.register('batting', BatterInningsViewSet, basename='batter-innings')
router.register('bowling', BowlerFiguresViewSet, basename='bowler-figures')
router.register('fall-of-wickets', FallOfWicketViewSet, basename='fall-of-wicket')
router.register('over-summaries', OverSummaryViewSet, basename='over-summary')
router.register('commentaries', CommentaryViewSet, basename='commentary')
router.register('match-states', MatchStateViewSet, basename='match-state')
router.register('record-ball', RecordBallViewSet, basename='record-ball')
router.register('scorecard', ScorecardViewSet, basename='scorecard')

urlpatterns = [
    path('', include(router.urls)),
    # Auth endpoints
    path('auth/', include('apps.accounts.auth_urls', namespace='auth')),
]
