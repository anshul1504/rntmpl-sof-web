"""
Live Scoring API Serializers.
Provides read/write serializers for match scoring operations.
"""
from rest_framework import serializers

from apps.scoring.models import (
    Innings,
    Ball,
    BallType,
    BatterInnings,
    BowlerFigures,
    DismissalType,
    FallOfWicket,
    Partnership,
    OverSummary,
    Commentary,
    MatchState,
)
from apps.players.models import PlayerProfile
from apps.tournaments.models import TournamentMatch


class PlayerBriefSerializer(serializers.ModelSerializer):
    """Compact player reference for nested use."""
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = PlayerProfile
        fields = ('id', 'full_name', 'jersey_number', 'photo')
        read_only_fields = fields


class InningsSerializer(serializers.ModelSerializer):
    batting_team_name = serializers.CharField(source='batting_team.team.name', read_only=True)
    bowling_team_name = serializers.CharField(source='bowling_team.team.name', read_only=True)

    class Meta:
        model = Innings
        fields = (
            'id', 'match', 'batting_team', 'batting_team_name',
            'bowling_team', 'bowling_team_name', 'innings_number',
            'status', 'total_runs', 'total_wickets', 'total_extras',
            'total_overs_bowled', 'run_rate', 'required_runs',
            'required_overs', 'target_runs', 'is_declared', 'is_all_out',
            'started_at', 'ended_at',
        )
        read_only_fields = ('id', 'run_rate')


class BallSerializer(serializers.ModelSerializer):
    bowler_name = serializers.CharField(source='bowler.full_name', read_only=True)
    striker_name = serializers.CharField(source='striker.full_name', read_only=True)
    display_score = serializers.CharField(read_only=True)

    class Meta:
        model = Ball
        fields = (
            'id', 'innings', 'match', 'over_number', 'ball_number_in_over',
            'ball_number_in_innings', 'bowler', 'bowler_name',
            'striker', 'striker_name', 'non_striker',
            'runs_from_bat', 'runs_extras', 'total_runs_on_ball',
            'ball_type', 'is_legal', 'is_boundary', 'is_six',
            'is_dot_ball', 'is_wicket', 'dismissal_type',
            'dismissed_player', 'bowler_on_dismissal',
            'commentary', 'short_commentary', 'bowled_at',
            'display_score',
        )
        read_only_fields = (
            'id', 'total_runs_on_ball', 'is_legal', 'is_boundary',
            'is_six', 'is_dot_ball', 'is_maiden_ball', 'display_score',
        )


class RecordBallSerializer(serializers.Serializer):
    """Serializer for recording a new ball delivery."""
    innings = serializers.PrimaryKeyRelatedField(queryset=Innings.objects.all())
    match = serializers.PrimaryKeyRelatedField(queryset=TournamentMatch.objects.all())
    bowler = serializers.PrimaryKeyRelatedField(queryset=PlayerProfile.objects.all())
    striker = serializers.PrimaryKeyRelatedField(queryset=PlayerProfile.objects.all())
    non_striker = serializers.PrimaryKeyRelatedField(queryset=PlayerProfile.objects.all())
    runs_from_bat = serializers.IntegerField(default=0, min_value=0, max_value=6)
    ball_type = serializers.ChoiceField(choices=BallType.choices, default=BallType.NORMAL)

    # Extra runs
    extras_wide_runs = serializers.IntegerField(default=0, min_value=0)
    extras_no_ball_runs = serializers.IntegerField(default=0, min_value=0)
    extras_bye_runs = serializers.IntegerField(default=0, min_value=0)
    extras_leg_bye_runs = serializers.IntegerField(default=0, min_value=0)

    # Wicket
    is_wicket = serializers.BooleanField(default=False)
    dismissal_type = serializers.ChoiceField(choices=DismissalType.choices, default='', allow_blank=True)
    dismissed_player = serializers.PrimaryKeyRelatedField(
        queryset=PlayerProfile.objects.all(), required=False, allow_null=True
    )
    bowler_on_dismissal = serializers.PrimaryKeyRelatedField(
        queryset=PlayerProfile.objects.all(), required=False, allow_null=True
    )
    fielder_on_dismissal = serializers.PrimaryKeyRelatedField(
        queryset=PlayerProfile.objects.all(), required=False, allow_null=True
    )

    # Commentary
    commentary = serializers.CharField(default='', allow_blank=True, max_length=500)
    short_commentary = serializers.CharField(default='', allow_blank=True, max_length=200)


class BatterInningsSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source='player.full_name', read_only=True)
    display_score = serializers.CharField(read_only=True)

    class Meta:
        model = BatterInnings
        fields = (
            'id', 'innings', 'player', 'player_name',
            'batting_position', 'is_out', 'dismissal_type',
            'runs', 'balls_faced', 'fours', 'sixes',
            'strike_rate', 'dot_balls',
            'display_score',
        )
        read_only_fields = ('id', 'strike_rate', 'display_score')


class BowlerFiguresSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source='player.full_name', read_only=True)
    display_figures = serializers.CharField(read_only=True)

    class Meta:
        model = BowlerFigures
        fields = (
            'id', 'innings', 'player', 'player_name',
            'overs_bowled', 'maidens', 'runs_conceded',
            'wickets', 'wides', 'no_balls', 'dots',
            'economy_rate', 'display_figures',
        )
        read_only_fields = ('id', 'economy_rate', 'display_figures')


class FallOfWicketSerializer(serializers.ModelSerializer):
    batter_name = serializers.CharField(source='batter.full_name', read_only=True)

    class Meta:
        model = FallOfWicket
        fields = (
            'id', 'innings', 'wicket_number', 'batter', 'batter_name',
            'team_score_at_wicket', 'overs_at_wicket',
            'ball_number_in_innings', 'partnership_runs',
            'partnership_balls', 'dismissal_type', 'dismissed_by',
        )


class OverSummarySerializer(serializers.ModelSerializer):
    bowler_name = serializers.CharField(source='bowler.full_name', read_only=True)

    class Meta:
        model = OverSummary
        fields = (
            'id', 'innings', 'over_number', 'bowler', 'bowler_name',
            'runs_conceded', 'wickets_in_over', 'is_maiden',
            'is_wicket_maiden', 'total_balls', 'dot_balls',
            'cumulative_score', 'cumulative_wickets',
            'is_completed',
        )


class CommentarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Commentary
        fields = (
            'id', 'ball', 'innings', 'match',
            'text', 'summary', 'is_auto_generated',
            'is_highlight', 'created_at',
        )
        read_only_fields = ('id', 'created_at')


class MatchStateSerializer(serializers.ModelSerializer):
    """Live match state for real-time display."""
    batting_team_name = serializers.CharField(source='batting_team.team.name', read_only=True, default='')
    bowling_team_name = serializers.CharField(source='bowling_team.team.name', read_only=True, default='')
    striker_name = serializers.CharField(source='striker.full_name', read_only=True, default='')
    non_striker_name = serializers.CharField(source='non_striker.full_name', read_only=True, default='')
    current_bowler_name = serializers.CharField(source='current_bowler.full_name', read_only=True, default='')

    class Meta:
        model = MatchState
        fields = (
            'id', 'match',
            'batting_team', 'batting_team_name',
            'bowling_team', 'bowling_team_name',
            'striker', 'striker_name',
            'non_striker', 'non_striker_name',
            'current_bowler', 'current_bowler_name',
            'current_over_number', 'current_ball_in_over',
            'runs', 'wickets', 'overs_bowled', 'run_rate',
            'target_runs', 'runs_required', 'required_run_rate',
            'balls_remaining', 'recent_balls',
            'is_live', 'has_started', 'is_completed',
            'last_updated',
        )
        read_only_fields = fields


class ScorecardSerializer(serializers.Serializer):
    """
    Complete scorecard for a match.
    Aggregates innings, batting, bowling, and fall of wickets.
    """
    innings = InningsSerializer(read_only=True)
    batting = BatterInningsSerializer(many=True, read_only=True)
    bowling = BowlerFiguresSerializer(many=True, read_only=True)
    fall_of_wickets = FallOfWicketSerializer(many=True, read_only=True)
    partnerships = serializers.SerializerMethodField()
    extras_summary = serializers.SerializerMethodField()

    def get_partnerships(self, obj):
        partnerships = obj.get('innings', {}).get('partnerships', [])
        return PartnershipSerializer(partnerships, many=True).data if partnerships else []

    def get_extras_summary(self, obj):
        innings = obj.get('innings', None)
        if not innings:
            return {}
        return {
            'total': innings.total_extras,
            'wides': sum(b.extras_wide_runs for b in innings.balls.all()),
            'no_balls': sum(b.extras_no_ball_runs for b in innings.balls.all()),
            'byes': sum(b.extras_bye_runs for b in innings.balls.all()),
            'leg_byes': sum(b.extras_leg_bye_runs for b in innings.balls.all()),
            'penalty': sum(b.extras_penalty_runs for b in innings.balls.all()),
        } if hasattr(innings, 'balls') else {}


class PartnershipSerializer(serializers.ModelSerializer):
    batter_one_name = serializers.CharField(source='batter_one.full_name', read_only=True)
    batter_two_name = serializers.CharField(source='batter_two.full_name', read_only=True)

    class Meta:
        model = Partnership
        fields = (
            'id', 'innings', 'batter_one', 'batter_one_name',
            'batter_two', 'batter_two_name',
            'runs', 'balls_faced', 'fours', 'sixes',
            'is_current', 'run_rate',
        )
