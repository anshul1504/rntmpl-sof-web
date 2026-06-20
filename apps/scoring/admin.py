from django.contrib import admin

from apps.scoring.models import (
    Innings,
    Ball,
    BatterInnings,
    BowlerFigures,
    FallOfWicket,
    Partnership,
    OverSummary,
    Commentary,
    MatchState,
    ScoreCorrection,
)


@admin.register(Innings)
class InningsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'match', 'batting_team', 'status', 'total_runs', 'total_wickets', 'total_overs_bowled', 'run_rate')
    list_filter = ('status', 'innings_number')
    search_fields = ('match__tournament__name', 'match__home_team__team__name', 'match__away_team__team__name')
    date_hierarchy = 'started_at'
    raw_id_fields = ('match', 'batting_team', 'bowling_team')


@admin.register(Ball)
class BallAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'bowler', 'striker', 'total_runs_on_ball', 'ball_type', 'is_wicket', 'is_boundary', 'is_six')
    list_filter = ('ball_type', 'is_wicket', 'is_boundary', 'is_six', 'over_number')
    search_fields = ('bowler__first_name', 'striker__first_name')
    raw_id_fields = ('innings', 'match', 'bowler', 'striker', 'non_striker', 'dismissed_player', 'fielder_on_dismissal', 'bowler_on_dismissal')


@admin.register(BatterInnings)
class BatterInningsAdmin(admin.ModelAdmin):
    list_display = ('player', 'innings', 'runs', 'balls_faced', 'fours', 'sixes', 'strike_rate', 'is_out')
    list_filter = ('is_out',)
    search_fields = ('player__first_name', 'player__last_name')
    raw_id_fields = ('innings', 'player', 'dismissed_by', 'fielder')


@admin.register(BowlerFigures)
class BowlerFiguresAdmin(admin.ModelAdmin):
    list_display = ('player', 'innings', 'overs_bowled', 'maidens', 'runs_conceded', 'wickets', 'economy_rate', 'display_figures')
    list_filter = ('is_bowling',)
    search_fields = ('player__first_name', 'player__last_name')
    raw_id_fields = ('innings', 'player')


@admin.register(FallOfWicket)
class FallOfWicketAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'wicket_number', 'team_score_at_wicket', 'overs_at_wicket', 'partnership_runs', 'dismissal_type')
    search_fields = ('batter__first_name', 'batter__last_name')
    raw_id_fields = ('innings', 'batter', 'dismissed_by')


@admin.register(Partnership)
class PartnershipAdmin(admin.ModelAdmin):
    list_display = ('batter_one', 'batter_two', 'runs', 'balls_faced', 'is_current')
    list_filter = ('is_current',)
    raw_id_fields = ('innings', 'batter_one', 'batter_two')


@admin.register(OverSummary)
class OverSummaryAdmin(admin.ModelAdmin):
    list_display = ('over_number', 'innings', 'bowler', 'runs_conceded', 'wickets_in_over', 'is_maiden', 'cumulative_score', 'cumulative_wickets')
    list_filter = ('is_maiden', 'is_completed', 'is_wicket_maiden')
    raw_id_fields = ('innings', 'bowler')


@admin.register(Commentary)
class CommentaryAdmin(admin.ModelAdmin):
    list_display = ('summary', 'ball', 'is_auto_generated', 'is_highlight', 'created_at')
    list_filter = ('is_auto_generated', 'is_highlight')
    search_fields = ('text', 'summary')
    raw_id_fields = ('ball', 'innings', 'match')


@admin.register(MatchState)
class MatchStateAdmin(admin.ModelAdmin):
    list_display = ('match', 'runs', 'wickets', 'overs_bowled', 'run_rate', 'is_live', 'has_started', 'is_completed')
    list_filter = ('is_live', 'has_started', 'is_completed')
    raw_id_fields = ('match', 'current_innings', 'batting_team', 'bowling_team', 'striker', 'non_striker', 'current_bowler')


@admin.register(ScoreCorrection)
class ScoreCorrectionAdmin(admin.ModelAdmin):
    list_display = ('match', 'ball_reference', 'reason', 'corrected_by', 'corrected_at')
    list_filter = ('corrected_at',)
    search_fields = ('match__tournament__name', 'reason', 'ball_reference')
    readonly_fields = ('original_data', 'corrected_at')
