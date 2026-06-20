from decimal import Decimal

from django.db import transaction

from apps.scoring.models import (
    Ball,
    BallType,
    BatterInnings,
    BowlerFigures,
    Commentary,
    DismissalType,
    FallOfWicket,
    Innings,
    MatchState,
    OverSummary,
    Partnership,
    ScoreCorrection,
)


BOWLER_WICKETS = {
    DismissalType.BOWLED,
    DismissalType.CAUGHT,
    DismissalType.LBW,
    DismissalType.STUMPED,
    DismissalType.HIT_WICKET,
}


def overs_from_balls(legal_balls):
    return Decimal(f'{legal_balls // 6}.{legal_balls % 6}')


def rebuild_innings_projections(innings):
    """Rebuild mutable scorecard projections from the surviving ball ledger."""
    balls = list(
        Ball.objects.filter(innings=innings)
        .select_related('striker', 'non_striker', 'bowler', 'dismissed_player', 'fielder_on_dismissal')
        .order_by('ball_number_in_innings')
    )

    BatterInnings.objects.filter(innings=innings).delete()
    BowlerFigures.objects.filter(innings=innings).delete()
    FallOfWicket.objects.filter(innings=innings).delete()
    OverSummary.objects.filter(innings=innings).delete()
    Partnership.objects.filter(innings=innings).delete()

    batter_order = {}
    bowler_order = {}
    total_runs = total_wickets = total_extras = legal_balls = 0

    for ball in balls:
        if ball.striker_id not in batter_order:
            batter_order[ball.striker_id] = len(batter_order) + 1
        batter, _ = BatterInnings.objects.get_or_create(
            innings=innings,
            player=ball.striker,
            defaults={'batting_position': batter_order[ball.striker_id]},
        )
        if ball.ball_type != BallType.WIDE:
            batter.balls_faced += 1
        batter.runs += ball.runs_from_bat
        batter.fours += int(ball.runs_from_bat == 4)
        batter.sixes += int(ball.runs_from_bat == 6)
        batter.dot_balls += int(ball.total_runs_on_ball == 0 and not ball.is_wicket)

        if ball.is_wicket and ball.dismissed_player_id == ball.striker_id:
            batter.is_out = True
            batter.dismissal_type = ball.dismissal_type
            batter.dismissed_by = ball.bowler_on_dismissal
            batter.fielder = ball.fielder_on_dismissal
            batter.dismissed_at = ball.ball_number_in_innings
            batter.how_out_description = ball.get_dismissal_type_display()
        batter.calculate_strike_rate()
        batter.save()

        if ball.is_wicket and ball.dismissed_player_id and ball.dismissed_player_id != ball.striker_id:
            if ball.dismissed_player_id not in batter_order:
                batter_order[ball.dismissed_player_id] = len(batter_order) + 1
            dismissed, _ = BatterInnings.objects.get_or_create(
                innings=innings,
                player=ball.dismissed_player,
                defaults={'batting_position': batter_order[ball.dismissed_player_id]},
            )
            dismissed.is_out = True
            dismissed.dismissal_type = ball.dismissal_type
            dismissed.fielder = ball.fielder_on_dismissal
            dismissed.dismissed_at = ball.ball_number_in_innings
            dismissed.how_out_description = ball.get_dismissal_type_display()
            dismissed.save()

        if ball.bowler_id not in bowler_order:
            bowler_order[ball.bowler_id] = len(bowler_order) + 1
        bowler, _ = BowlerFigures.objects.get_or_create(
            innings=innings,
            player=ball.bowler,
            defaults={'bowling_order': bowler_order[ball.bowler_id]},
        )
        bowler.balls_bowled += 1
        bowler.legal_deliveries += int(ball.is_legal)
        bowler.overs_bowled = overs_from_balls(bowler.legal_deliveries)
        bowler.runs_conceded += ball.runs_from_bat + ball.extras_wide_runs + ball.extras_no_ball_runs
        bowler.wides += ball.extras_wide_runs
        bowler.no_balls += ball.extras_no_ball_runs
        bowler.wickets += int(ball.is_wicket and ball.dismissal_type in BOWLER_WICKETS)
        bowler.dots += int(ball.total_runs_on_ball == 0 and not ball.is_wicket)
        bowler.fours_conceded += int(ball.runs_from_bat == 4)
        bowler.sixes_conceded += int(ball.runs_from_bat == 6)
        bowler.calculate_economy()
        bowler.save()

        total_runs += ball.total_runs_on_ball
        total_extras += ball.runs_extras
        legal_balls += int(ball.is_legal)
        if ball.is_wicket and ball.dismissed_player_id:
            total_wickets += 1
            FallOfWicket.objects.create(
                innings=innings,
                wicket_number=total_wickets,
                batter=ball.dismissed_player,
                team_score_at_wicket=total_runs,
                overs_at_wicket=overs_from_balls(legal_balls),
                ball_number_in_innings=ball.ball_number_in_innings,
                dismissal_type=ball.dismissal_type,
                dismissed_by=ball.bowler_on_dismissal,
            )

    innings.total_runs = total_runs
    innings.total_wickets = total_wickets
    innings.total_extras = total_extras
    innings.total_legal_balls = legal_balls
    innings.total_balls_bowled = len(balls)
    innings.total_overs_bowled = overs_from_balls(legal_balls)
    innings.run_rate = (
        Decimal(total_runs * 6) / Decimal(legal_balls)
        if legal_balls else Decimal('0.00')
    )
    innings.save()
    return balls


@transaction.atomic
def undo_last_ball(match, user, reason):
    state = MatchState.objects.select_for_update().get(match=match)
    innings = Innings.objects.select_for_update().get(pk=state.current_innings_id)
    ball = (
        Ball.objects.select_for_update()
        .filter(innings=innings)
        .order_by('-ball_number_in_innings')
        .first()
    )
    if not ball:
        raise ValueError('No delivery is available to undo.')

    original_data = {
        'ball_id': ball.pk,
        'over_number': ball.over_number,
        'ball_number_in_over': ball.ball_number_in_over,
        'ball_number_in_innings': ball.ball_number_in_innings,
        'bowler_id': ball.bowler_id,
        'striker_id': ball.striker_id,
        'non_striker_id': ball.non_striker_id,
        'runs_from_bat': ball.runs_from_bat,
        'runs_extras': ball.runs_extras,
        'ball_type': ball.ball_type,
        'is_wicket': ball.is_wicket,
        'dismissal_type': ball.dismissal_type,
        'dismissed_player_id': ball.dismissed_player_id,
    }
    ScoreCorrection.objects.create(
        match=match,
        innings=innings,
        ball_reference=f'{ball.over_number}.{ball.ball_number_in_over}',
        reason=reason,
        original_data=original_data,
        corrected_by=user,
    )

    striker = ball.striker
    non_striker = ball.non_striker
    bowler = ball.bowler
    ball.delete()
    remaining = rebuild_innings_projections(innings)

    state.striker = striker
    state.non_striker = non_striker
    state.current_bowler = bowler
    state.runs = innings.total_runs
    state.wickets = innings.total_wickets
    state.overs_bowled = innings.total_overs_bowled
    state.run_rate = innings.run_rate
    last = remaining[-1] if remaining else None
    state.current_over_number = last.over_number if last else 0
    state.current_ball_in_over = last.ball_number_in_over if last else 0
    state.balls_in_current_over = (
        sum(1 for item in remaining if last and item.over_number == last.over_number and item.is_legal)
        if last else 0
    )
    state.recent_balls = [item.display_score for item in remaining[-6:]]
    if state.target_runs:
        state.runs_required = max(state.target_runs - state.runs, 0)
    state.save()
    return original_data
