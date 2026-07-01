"""
Live Scoring API Viewsets.
Provides match scoring endpoints with tenant-scoped access.
"""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.views import scoped_to_user_tenants

from apps.scoring.models import (
    Innings,
    Ball,
    BatterInnings,
    BowlerFigures,
    FallOfWicket,
    OverSummary,
    Commentary,
    MatchState,
    Partnership,
)
from apps.scoring.serializers import (
    InningsSerializer,
    BallSerializer,
    BatterInningsSerializer,
    BowlerFiguresSerializer,
    FallOfWicketSerializer,
    OverSummarySerializer,
    CommentarySerializer,
    MatchStateSerializer,
    PartnershipSerializer,
    RecordBallSerializer,
)


class InningsViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only view of innings within a match."""
    serializer_class = InningsSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ('match', 'batting_team', 'status', 'innings_number')
    ordering_fields = ('match', 'innings_number')
    ordering = ('match', 'innings_number')

    def get_queryset(self):
        qs = Innings.objects.select_related(
            'match__tournament',
            'batting_team__team',
            'bowling_team__team',
        )
        return scoped_to_user_tenants(qs, self.request.user, tenant_field='match__tournament__tenant_id')


class BallViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only view of ball-by-ball deliveries."""
    serializer_class = BallSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ('innings', 'match', 'bowler', 'striker', 'over_number', 'is_wicket', 'ball_type')
    ordering_fields = ('ball_number_in_innings', 'bowled_at')
    ordering = ('ball_number_in_innings',)

    def get_queryset(self):
        qs = Ball.objects.select_related(
            'bowler', 'striker', 'non_striker',
        )
        return scoped_to_user_tenants(qs, self.request.user, tenant_field='match__tournament__tenant_id')


class RecordBallViewSet(viewsets.GenericViewSet):
    """Record a single ball delivery. Create-only endpoint."""
    serializer_class = RecordBallSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        innings = data['innings']

        # Calculate ball numbering
        last_ball = Ball.objects.filter(innings=innings).order_by('-ball_number_in_innings').first()
        ball_number_in_innings = (last_ball.ball_number_in_innings + 1) if last_ball else 1

        # Determine over and ball within over
        if last_ball:
            if last_ball.is_legal:
                over_number = last_ball.over_number
                ball_in_over = last_ball.ball_number_in_over + 1
                if ball_in_over > 6:
                    over_number += 1
                    ball_in_over = 1
            else:
                over_number = last_ball.over_number
                ball_in_over = last_ball.ball_number_in_over
        else:
            over_number = 1
            ball_in_over = 1

        ball = Ball.objects.create(
            innings=innings,
            match=data['match'],
            over_number=over_number,
            ball_number_in_over=ball_in_over,
            ball_number_in_innings=ball_number_in_innings,
            bowler=data['bowler'],
            striker=data['striker'],
            non_striker=data['non_striker'],
            runs_from_bat=data['runs_from_bat'],
            ball_type=data['ball_type'],
            extras_wide_runs=data.get('extras_wide_runs', 0),
            extras_no_ball_runs=data.get('extras_no_ball_runs', 0),
            extras_bye_runs=data.get('extras_bye_runs', 0),
            extras_leg_bye_runs=data.get('extras_leg_bye_runs', 0),
            is_wicket=data['is_wicket'],
            dismissal_type=data.get('dismissal_type', ''),
            dismissed_player=data.get('dismissed_player'),
            bowler_on_dismissal=data.get('bowler_on_dismissal'),
            fielder_on_dismissal=data.get('fielder_on_dismissal'),
            commentary=data.get('commentary', ''),
            short_commentary=data.get('short_commentary', ''),
        )

        return Response(
            BallSerializer(ball, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class BatterInningsViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only view of batter innings records."""
    serializer_class = BatterInningsSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ('innings', 'player', 'is_out')
    ordering_fields = ('innings', 'batting_position', 'runs')
    ordering = ('innings', 'batting_position')

    def get_queryset(self):
        qs = BatterInnings.objects.select_related('player')
        return scoped_to_user_tenants(qs, self.request.user, tenant_field='innings__match__tournament__tenant_id')


class BowlerFiguresViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only view of bowler figures."""
    serializer_class = BowlerFiguresSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ('innings', 'player', 'is_bowling')
    ordering_fields = ('innings', 'bowling_order', 'wickets', 'economy_rate')
    ordering = ('innings', 'bowling_order')

    def get_queryset(self):
        qs = BowlerFigures.objects.select_related('player')
        return scoped_to_user_tenants(qs, self.request.user, tenant_field='innings__match__tournament__tenant_id')


class FallOfWicketViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only view of fall of wickets."""
    serializer_class = FallOfWicketSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ('innings', 'batter')
    ordering_fields = ('innings', 'wicket_number')
    ordering = ('innings', 'wicket_number')

    def get_queryset(self):
        qs = FallOfWicket.objects.select_related('batter', 'dismissed_by')
        return scoped_to_user_tenants(qs, self.request.user, tenant_field='innings__match__tournament__tenant_id')


class OverSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only view of over summaries."""
    serializer_class = OverSummarySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ('innings', 'bowler', 'is_completed', 'is_maiden')
    ordering_fields = ('innings', 'over_number')
    ordering = ('innings', 'over_number')

    def get_queryset(self):
        qs = OverSummary.objects.select_related('bowler')
        return scoped_to_user_tenants(qs, self.request.user, tenant_field='innings__match__tournament__tenant_id')


class CommentaryViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only view of ball-by-ball commentary."""
    serializer_class = CommentarySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ('innings', 'match', 'is_highlight', 'is_auto_generated')
    ordering_fields = ('-created_at',)
    ordering = ('-created_at',)

    def get_queryset(self):
        qs = Commentary.objects.select_related('ball')
        return scoped_to_user_tenants(qs, self.request.user, tenant_field='match__tournament__tenant_id')


class MatchStateViewSet(viewsets.ReadOnlyModelViewSet):
    """Live match state for real-time scoring displays."""
    serializer_class = MatchStateSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ('match', 'is_live', 'has_started', 'is_completed')
    ordering_fields = ('-last_updated',)

    def get_queryset(self):
        qs = MatchState.objects.select_related(
            'match', 'batting_team__team', 'bowling_team__team',
            'striker', 'non_striker', 'current_bowler',
        )
        return scoped_to_user_tenants(qs, self.request.user, tenant_field='match__tournament__tenant_id')


class ScorecardViewSet(viewsets.GenericViewSet):
    """
    Aggregated scorecard for a match.
    Returns full innings detail with batting, bowling, partnerships, etc.
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        match_id = request.query_params.get('match')
        innings_number = request.query_params.get('innings', 1)

        if not match_id:
            return Response({'error': 'match query parameter is required'}, status=400)

        try:
            innings = Innings.objects.select_related(
                'match__tournament', 'batting_team__team', 'bowling_team__team',
            ).get(match_id=match_id, innings_number=innings_number)
        except Innings.DoesNotExist:
            return Response({'error': 'Innings not found'}, status=404)

        batting = BatterInnings.objects.filter(innings=innings).select_related('player').order_by('batting_position')
        bowling = BowlerFigures.objects.filter(innings=innings).select_related('player').order_by('bowling_order')
        fow = FallOfWicket.objects.filter(innings=innings).select_related('batter').order_by('wicket_number')
        partnerships = Partnership.objects.filter(innings=innings).select_related('batter_one', 'batter_two').order_by('-runs')

        data = {
            'innings': InningsSerializer(innings, context={'request': request}).data,
            'batting': BatterInningsSerializer(batting, many=True, context={'request': request}).data,
            'bowling': BowlerFiguresSerializer(bowling, many=True, context={'request': request}).data,
            'fall_of_wickets': FallOfWicketSerializer(fow, many=True, context={'request': request}).data,
            'partnerships': PartnershipSerializer(partnerships, many=True, context={'request': request}).data,
        }
        return Response(data)
