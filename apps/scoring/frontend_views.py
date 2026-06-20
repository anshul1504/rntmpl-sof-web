"""
Frontend Views for Live Scoring in the Cricket Ecosystem Platform.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.db import transaction
from django.urls import reverse
from django.db.models import Q
from decimal import Decimal
from django.utils import timezone

from apps.tournaments.views import get_active_tenant
from apps.tournaments.models import (
    TournamentMatch, TournamentTeam, TournamentPlayer, Tournament,
    MatchSetup, MatchPlayingXI,
)
from apps.tournaments.utils import update_points_table
from apps.players.models import PlayerProfile
from apps.scoring.models import (
    Innings, Ball, BatterInnings, BowlerFigures,
    FallOfWicket, Partnership, OverSummary, Commentary, MatchState,
    InningStatus, BallType, DismissalType, ExtrasType
)
from apps.scoring.services import undo_last_ball
from apps.accounts.policies import CapabilityRequiredMixin


def complete_current_innings(match, state, setup):
    """Complete the active innings and either start the chase or finish the match."""
    current_innings = state.current_innings
    current_innings.status = InningStatus.COMPLETED
    current_innings.ended_at = timezone.now()
    current_innings.save()

    if current_innings.innings_number == 1:
        next_innings = Innings.objects.create(
            match=match,
            batting_team=current_innings.bowling_team,
            bowling_team=current_innings.batting_team,
            innings_number=2,
            status=InningStatus.IN_PROGRESS,
            started_at=timezone.now(),
            target_runs=current_innings.total_runs + 1,
        )
        state.current_innings = next_innings
        state.batting_team = next_innings.batting_team
        state.bowling_team = next_innings.bowling_team
        state.striker = None
        state.non_striker = None
        state.current_bowler = None
        state.runs = 0
        state.wickets = 0
        state.overs_bowled = Decimal('0.0')
        state.run_rate = Decimal('0.00')
        state.target_runs = next_innings.target_runs
        state.runs_required = next_innings.target_runs
        rules = getattr(match.tournament, 'rules', None)
        state.balls_remaining = (rules.overs_per_innings if rules else 20) * 6
        state.recent_balls = []
        state.save()
        setup.lifecycle = MatchSetup.Lifecycle.INNINGS_BREAK
        setup.save(update_fields=['lifecycle', 'updated_at'])
        return False

    innings1 = Innings.objects.get(match=match, innings_number=1)
    innings2 = current_innings
    state.is_live = False
    state.is_completed = True
    state.balls_remaining = max(state.balls_remaining or 0, 0)
    state.save()
    match.is_completed = True
    match.home_team_score = f"{innings1.total_runs}/{innings1.total_wickets}"
    match.away_team_score = f"{innings2.total_runs}/{innings2.total_wickets}"
    match.home_team_overs = innings1.total_overs_bowled
    match.away_team_overs = innings2.total_overs_bowled
    if innings2.total_runs > innings1.total_runs:
        match.winner, match.loser = innings2.batting_team, innings1.batting_team
    elif innings2.total_runs < innings1.total_runs:
        match.winner, match.loser = innings1.batting_team, innings2.batting_team
    else:
        match.winner = match.loser = None
        match.is_draw = True
        match.result_type = TournamentMatch.ResultType.TIE
    match.save()
    setup.lifecycle = MatchSetup.Lifecycle.COMPLETED
    setup.save(update_fields=['lifecycle', 'updated_at'])
    update_points_table(match)
    return True

def update_scorecard_stats(ball):
    """
    Given a new Ball instance, update innings and player stats.
    """
    innings = ball.innings
    striker = ball.striker
    bowler = ball.bowler
    
    # 1. Update Batter Innings
    batter_record, _ = BatterInnings.objects.get_or_create(
        innings=innings,
        player=striker,
        defaults={'batting_position': BatterInnings.objects.filter(innings=innings).count() + 1}
    )
    if ball.ball_type != BallType.WIDE:
        batter_record.balls_faced += 1
    
    batter_record.runs += ball.runs_from_bat
    if ball.runs_from_bat == 4:
        batter_record.fours += 1
    elif ball.runs_from_bat == 6:
        batter_record.sixes += 1
    elif ball.total_runs_on_ball == 0 and not ball.is_wicket:
        batter_record.dot_balls += 1
        
    if ball.is_wicket and ball.dismissed_player == striker:
        batter_record.is_out = True
        batter_record.dismissal_type = ball.dismissal_type
        batter_record.dismissed_by = ball.bowler_on_dismissal
        batter_record.fielder = ball.fielder_on_dismissal
        batter_record.dismissed_at = ball.ball_number_in_innings
        
        # Description
        desc = ""
        if ball.dismissal_type == DismissalType.BOWLED:
            desc = f"b {ball.bowler.full_name}"
        elif ball.dismissal_type == DismissalType.LBW:
            desc = f"lbw b {ball.bowler.full_name}"
        elif ball.dismissal_type == DismissalType.CAUGHT:
            fielder_name = ball.fielder_on_dismissal.full_name if ball.fielder_on_dismissal else "fielder"
            desc = f"c {fielder_name} b {ball.bowler.full_name}"
        elif ball.dismissal_type == DismissalType.STUMPED:
            fielder_name = ball.fielder_on_dismissal.full_name if ball.fielder_on_dismissal else "keeper"
            desc = f"st {fielder_name} b {ball.bowler.full_name}"
        elif ball.dismissal_type == DismissalType.RUN_OUT:
            fielder_name = ball.fielder_on_dismissal.full_name if ball.fielder_on_dismissal else "fielder"
            desc = f"run out ({fielder_name})"
        else:
            desc = ball.get_dismissal_type_display() or "out"
        batter_record.how_out_description = desc
    batter_record.calculate_strike_rate()
    batter_record.save()

    # Non-striker out (e.g. Run Out at non-striker end)
    if ball.is_wicket and ball.dismissed_player and ball.dismissed_player != striker:
        non_striker_record, _ = BatterInnings.objects.get_or_create(
            innings=innings,
            player=ball.dismissed_player,
            defaults={'batting_position': BatterInnings.objects.filter(innings=innings).count() + 1}
        )
        non_striker_record.is_out = True
        non_striker_record.dismissal_type = ball.dismissal_type
        non_striker_record.fielder = ball.fielder_on_dismissal
        non_striker_record.dismissed_at = ball.ball_number_in_innings
        non_striker_record.how_out_description = f"run out ({ball.fielder_on_dismissal.full_name if ball.fielder_on_dismissal else 'fielder'})"
        non_striker_record.save()

    # 2. Update Bowler Figures
    bowler_record, _ = BowlerFigures.objects.get_or_create(
        innings=innings,
        player=bowler,
        defaults={'bowling_order': BowlerFigures.objects.filter(innings=innings).count() + 1}
    )
    if ball.is_legal:
        bowler_record.legal_deliveries += 1
    bowler_record.balls_bowled += 1
    
    completed_overs = bowler_record.legal_deliveries // 6
    remaining_balls = bowler_record.legal_deliveries % 6
    bowler_record.overs_bowled = Decimal(f"{completed_overs}.{remaining_balls}")
    
    runs_to_add = ball.runs_from_bat
    if ball.ball_type == BallType.WIDE:
        runs_to_add += ball.extras_wide_runs
        bowler_record.wides += ball.extras_wide_runs
    elif ball.ball_type == BallType.NO_BALL:
        runs_to_add += ball.extras_no_ball_runs
        bowler_record.no_balls += 1
        
    bowler_record.runs_conceded += runs_to_add
    
    if ball.is_wicket and ball.dismissal_type in [
        DismissalType.BOWLED, DismissalType.CAUGHT, DismissalType.LBW,
        DismissalType.STUMPED, DismissalType.HIT_WICKET
    ]:
        bowler_record.wickets += 1
        
    if ball.total_runs_on_ball == 0 and not ball.is_wicket:
        bowler_record.dots += 1
        
    bowler_record.calculate_economy()
    bowler_record.save()

    # 3. Update Innings
    innings.total_runs += ball.total_runs_on_ball
    if ball.is_wicket:
        innings.total_wickets += 1
    innings.total_extras += ball.runs_extras
    
    legal_balls_in_innings = Ball.objects.filter(innings=innings, is_legal=True).count()
    innings.total_legal_balls = legal_balls_in_innings
    innings.total_balls_bowled = Ball.objects.filter(innings=innings).count()
    
    innings_completed_overs = legal_balls_in_innings // 6
    innings_remaining_balls = legal_balls_in_innings % 6
    innings.total_overs_bowled = Decimal(f"{innings_completed_overs}.{innings_remaining_balls}")
    innings.calculate_run_rate()
    innings.save()

    # 4. Fall of Wickets
    if ball.is_wicket and ball.dismissed_player:
        FallOfWicket.objects.create(
            innings=innings,
            wicket_number=innings.total_wickets,
            batter=ball.dismissed_player,
            team_score_at_wicket=innings.total_runs,
            overs_at_wicket=innings.total_overs_bowled,
            ball_number_in_innings=ball.ball_number_in_innings,
            partnership_runs=ball.runs_from_bat,
            partnership_balls=1,
            dismissal_type=ball.dismissal_type,
            dismissed_by=ball.bowler_on_dismissal
        )


def get_active_tenant_match(request, pk):
    tenant = get_active_tenant(request)
    if not tenant:
        raise Http404("No active tenant selected.")
    return get_object_or_404(TournamentMatch, pk=pk, tournament__tenant=tenant, is_deleted=False)


def get_team_players(tournament_team):
    return PlayerProfile.objects.filter(
        tournaments_tournamentplayer_registrations__tournament_team=tournament_team,
        tournaments_tournamentplayer_registrations__is_deleted=False,
        is_deleted=False,
    ).distinct()


def get_match_team_players(match, tournament_team):
    setup = MatchSetup.objects.filter(match=match).first()
    if setup and setup.lifecycle in {
        MatchSetup.Lifecycle.READY,
        MatchSetup.Lifecycle.LIVE,
        MatchSetup.Lifecycle.INNINGS_BREAK,
    }:
        return PlayerProfile.objects.filter(
            match_selections__setup=setup,
            match_selections__tournament_team=tournament_team,
            match_selections__is_substitute=False,
            is_deleted=False,
        ).distinct()
    return PlayerProfile.objects.none()


class MatchListView(LoginRequiredMixin, ListView):
    model = TournamentMatch
    template_name = 'scoring/match_list.html'
    context_object_name = 'matches'
    paginate_by = 10

    def get_queryset(self):
        tenant = get_active_tenant(self.request)
        if not tenant:
            return TournamentMatch.objects.none()
        
        queryset = TournamentMatch.objects.filter(tournament__tenant=tenant, is_deleted=False)
        
        # Filter by tournament
        tournament_filter = self.request.GET.get('tournament', '')
        if tournament_filter:
            queryset = queryset.filter(tournament_id=tournament_filter)

        # Filter by status
        status_filter = self.request.GET.get('status', '')
        if status_filter == 'live':
            queryset = queryset.filter(is_completed=False, live_state__is_live=True)
        elif status_filter == 'completed':
            queryset = queryset.filter(is_completed=True)
        elif status_filter == 'upcoming':
            queryset = queryset.filter(is_completed=False).exclude(live_state__is_live=True)

        # Search
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(home_team__team__name__icontains=search_query) |
                Q(away_team__team__name__icontains=search_query) |
                Q(venue__icontains=search_query)
            )

        return queryset.select_related('home_team__team', 'away_team__team', 'tournament')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_active_tenant(self.request)
        context['tournaments'] = (
            Tournament.objects.filter(tenant=tenant, is_deleted=False)
            if tenant else Tournament.objects.none()
        )
        context['current_tenant'] = tenant
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['selected_tournament'] = self.request.GET.get('tournament', '')
        return context


class MatchScorecardView(LoginRequiredMixin, DetailView):
    model = TournamentMatch
    template_name = 'scoring/scorecard.html'
    context_object_name = 'match'

    def get_queryset(self):
        tenant = get_active_tenant(self.request)
        if not tenant:
            return TournamentMatch.objects.none()
        return TournamentMatch.objects.filter(tournament__tenant=tenant, is_deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        match = self.object
        
        # Get innings details
        innings_list = Innings.objects.filter(match=match).order_by('innings_number')
        
        scorecards_data = []
        for innings in innings_list:
            batting = BatterInnings.objects.filter(innings=innings).select_related('player').order_by('batting_position')
            bowling = BowlerFigures.objects.filter(innings=innings).select_related('player').order_by('bowling_order')
            fow = FallOfWicket.objects.filter(innings=innings).select_related('batter').order_by('wicket_number')
            
            scorecards_data.append({
                'innings': innings,
                'batting': batting,
                'bowling': bowling,
                'fall_of_wickets': fow,
            })
            
        context['scorecards'] = scorecards_data
        context['commentaries'] = Commentary.objects.filter(match=match).select_related('ball').order_by('-ball__ball_number_in_innings')[:30]
        context['live_state'] = MatchState.objects.filter(match=match).first()
        return context


class LiveScoringView(LoginRequiredMixin, CapabilityRequiredMixin, View):
    required_capability = 'scoring.manage'
    def get(self, request, pk):
        match = get_active_tenant_match(request, pk)
        setup = MatchSetup.objects.filter(match=match).first()
        if not setup or setup.lifecycle not in {
            MatchSetup.Lifecycle.READY,
            MatchSetup.Lifecycle.LIVE,
            MatchSetup.Lifecycle.INNINGS_BREAK,
        }:
            messages.error(request, "Complete and lock the match setup before starting scoring.")
            return redirect('tournaments:match-setup', pk=match.pk)
        
        # Get or create MatchState
        state, _ = MatchState.objects.get_or_create(
            match=match,
            defaults={
                'is_live': True,
                'has_started': True,
            }
        )
        
        # If no active innings, initialize first innings
        current_innings = state.current_innings
        if not current_innings:
            current_innings = Innings.objects.filter(match=match, innings_number=1).first()
            if not current_innings:
                current_innings = Innings.objects.create(
                    match=match,
                    batting_team=(
                        setup.toss_winner
                        if setup.toss_decision == MatchSetup.TossDecision.BAT
                        else (match.away_team if setup.toss_winner == match.home_team else match.home_team)
                    ),
                    bowling_team=(
                        match.away_team
                        if setup.toss_winner == match.home_team and setup.toss_decision == MatchSetup.TossDecision.BAT
                        else match.home_team
                        if setup.toss_winner == match.away_team and setup.toss_decision == MatchSetup.TossDecision.BAT
                        else setup.toss_winner
                    ),
                    innings_number=1,
                    status=InningStatus.IN_PROGRESS,
                    started_at=timezone.now()
                )
            state.current_innings = current_innings
            state.batting_team = current_innings.batting_team
            state.bowling_team = current_innings.bowling_team
            state.save()
            setup.lifecycle = MatchSetup.Lifecycle.LIVE
            setup.save(update_fields=['lifecycle', 'updated_at'])

        # Get available players for striker, non-striker and bowler selection
        batting_players = get_match_team_players(match, current_innings.batting_team)
        bowling_players = get_match_team_players(match, current_innings.bowling_team)

        recent_balls = Ball.objects.filter(innings=current_innings).order_by('-ball_number_in_innings')[:12]

        context = {
            'match': match,
            'state': state,
            'current_innings': current_innings,
            'batting_players': batting_players,
            'bowling_players': bowling_players,
            'recent_balls': recent_balls,
            'ball_types': BallType.choices,
            'dismissal_types': DismissalType.choices,
        }
        return render(request, 'scoring/live_score.html', context)

    def post(self, request, pk):
        match = get_active_tenant_match(request, pk)
        setup = MatchSetup.objects.filter(match=match).first()
        if not setup or setup.lifecycle not in {
            MatchSetup.Lifecycle.READY,
            MatchSetup.Lifecycle.LIVE,
            MatchSetup.Lifecycle.INNINGS_BREAK,
        }:
            messages.error(request, "Complete and lock the match setup before starting scoring.")
            return redirect('tournaments:match-setup', pk=match.pk)
        state = get_object_or_404(MatchState, match=match)
        current_innings = state.current_innings

        action = request.POST.get('action')

        if action == 'setup_players':
            striker_id = request.POST.get('striker')
            non_striker_id = request.POST.get('non_striker')
            bowler_id = request.POST.get('bowler')

            batting_players = get_match_team_players(match, current_innings.batting_team)
            bowling_players = get_match_team_players(match, current_innings.bowling_team)

            if striker_id:
                state.striker = get_object_or_404(batting_players, id=striker_id)
            if non_striker_id:
                state.non_striker = get_object_or_404(batting_players, id=non_striker_id)
            if bowler_id:
                state.current_bowler = get_object_or_404(bowling_players, id=bowler_id)

            if state.striker and state.non_striker and state.striker_id == state.non_striker_id:
                messages.error(request, "Striker and non-striker must be different players.")
                return redirect('scoring:live-score', pk=pk)

            state.is_live = True
            state.has_started = True
            state.save()
            messages.success(request, "Scoring setup updated.")

        elif action == 'record_ball':
            if not state.striker or not state.non_striker or not state.current_bowler:
                messages.error(request, "Please set up striker, non-striker, and bowler first.")
                return redirect('scoring:live-score', pk=pk)

            runs_from_bat = int(request.POST.get('runs_from_bat', 0))
            ball_type = request.POST.get('ball_type', BallType.NORMAL)
            is_wicket = request.POST.get('is_wicket') == 'true'
            dismissal_type = request.POST.get('dismissal_type', '')
            dismissed_player_id = request.POST.get('dismissed_player')
            fielder_id = request.POST.get('fielder_on_dismissal')

            extras_wide_runs = int(request.POST.get('extras_wide_runs', 0)) if ball_type == BallType.WIDE else 0
            extras_no_ball_runs = int(request.POST.get('extras_no_ball_runs', 0)) if ball_type == BallType.NO_BALL else 0
            extras_bye_runs = int(request.POST.get('extras_bye_runs', 0)) if ball_type == BallType.BYE else 0
            extras_leg_bye_runs = int(request.POST.get('extras_leg_bye_runs', 0)) if ball_type == BallType.LEG_BYE else 0
            rules = getattr(match.tournament, 'rules', None)
            max_overs = rules.overs_per_innings if rules else 20
            max_bowler_overs = rules.max_overs_per_bowler if rules else max(1, max_overs // 5)
            bowler_legal_balls = Ball.objects.filter(
                innings=current_innings,
                bowler=state.current_bowler,
                is_legal=True,
            ).count()
            if bowler_legal_balls >= max_bowler_overs * 6:
                messages.error(request, f"This bowler has completed the {max_bowler_overs}-over limit.")
                return redirect('scoring:live-score', pk=pk)

            with transaction.atomic():
                last_ball = Ball.objects.filter(innings=current_innings).order_by('-ball_number_in_innings').first()
                ball_number_in_innings = (last_ball.ball_number_in_innings + 1) if last_ball else 1
                legal_balls_before = Ball.objects.filter(innings=current_innings, is_legal=True).count()
                over_number = (legal_balls_before // 6) + 1
                balls_already_recorded_in_over = Ball.objects.filter(
                    innings=current_innings,
                    over_number=over_number,
                ).count()
                ball_in_over = balls_already_recorded_in_over + 1

                dismissed_player = None
                if is_wicket and dismissed_player_id:
                    if dismissed_player_id not in {str(state.striker_id), str(state.non_striker_id)}:
                        messages.error(request, "Dismissed player must be one of the batters at the crease.")
                        return redirect('scoring:live-score', pk=pk)
                    dismissed_player = PlayerProfile.objects.get(id=dismissed_player_id)

                fielder = None
                if fielder_id:
                    fielder = get_object_or_404(get_match_team_players(match, current_innings.bowling_team), id=fielder_id)

                ball = Ball.objects.create(
                    innings=current_innings,
                    match=match,
                    over_number=over_number,
                    ball_number_in_over=ball_in_over,
                    ball_number_in_innings=ball_number_in_innings,
                    bowler=state.current_bowler,
                    striker=state.striker,
                    non_striker=state.non_striker,
                    runs_from_bat=runs_from_bat,
                    ball_type=ball_type,
                    extras_wide_runs=extras_wide_runs,
                    extras_no_ball_runs=extras_no_ball_runs,
                    extras_bye_runs=extras_bye_runs,
                    extras_leg_bye_runs=extras_leg_bye_runs,
                    is_wicket=is_wicket,
                    dismissal_type=dismissal_type,
                    dismissed_player=dismissed_player,
                    fielder_on_dismissal=fielder,
                    bowler_on_dismissal=state.current_bowler if is_wicket else None,
                    commentary=f"Delivery from {state.current_bowler.full_name} to {state.striker.full_name}."
                )

                # Generate Commentary details
                Commentary.objects.create(
                    ball=ball,
                    innings=current_innings,
                    match=match,
                    text=f"{over_number}.{ball_in_over} {state.current_bowler.full_name} to {state.striker.full_name}, "
                         f"{ball.display_score} runs."
                )

                # Process scorecard statistics updates
                update_scorecard_stats(ball)

                # Manage batter strike rotation
                total_runs_on_ball = runs_from_bat + ball.runs_extras
                # If odd runs scored (excluding extras rotation rules like wide/no-ball which don't rotate strikers unless run is run)
                # We rotate strikers on 1 or 3 runs
                runs_for_rotation = runs_from_bat
                if ball_type in [BallType.BYE, BallType.LEG_BYE]:
                    runs_for_rotation = total_runs_on_ball
                
                if runs_for_rotation % 2 != 0:
                    state.striker, state.non_striker = state.non_striker, state.striker

                # Wicket handling (striker dismissed vs non-striker dismissed)
                if is_wicket and dismissed_player:
                    if dismissed_player == state.striker:
                        state.striker = None
                    else:
                        state.non_striker = None

                # Check if over is completed (6 legal deliveries)
                legal_balls_in_over = Ball.objects.filter(
                    innings=current_innings,
                    over_number=over_number,
                    is_legal=True
                ).count()

                if legal_balls_in_over >= 6:
                    # Over completed: rotate strikers and clear bowler for next over selection
                    state.striker, state.non_striker = state.non_striker, state.striker
                    state.current_bowler = None
                    messages.info(request, f"Over {over_number} completed. Select next bowler.")

                # Sync match state metrics
                state.runs = current_innings.total_runs
                state.wickets = current_innings.total_wickets
                state.overs_bowled = current_innings.total_overs_bowled
                state.run_rate = current_innings.run_rate
                state.current_over_number = over_number
                state.current_ball_in_over = ball_in_over
                state.balls_in_current_over = legal_balls_in_over
                if state.target_runs:
                    state.runs_required = max(state.target_runs - state.runs, 0)
                    state.balls_remaining = max((max_overs * 6) - current_innings.total_legal_balls, 0)
                    if state.balls_remaining:
                        state.required_run_rate = (
                            Decimal(state.runs_required * 6) / Decimal(state.balls_remaining)
                        )
                
                # Fetch recent deliveries list
                recent_deliveries = Ball.objects.filter(innings=current_innings).order_by('-ball_number_in_innings')[:6]
                state.recent_balls = [d.display_score for d in reversed(recent_deliveries)]
                state.save()

                innings_limit_reached = current_innings.total_legal_balls >= max_overs * 6
                all_out = current_innings.total_wickets >= 10
                chase_completed = bool(state.target_runs and current_innings.total_runs >= state.target_runs)
                if innings_limit_reached or all_out or chase_completed:
                    match_completed = complete_current_innings(match, state, setup)
                    if match_completed:
                        messages.success(request, "Match completed automatically.")
                        return redirect('scoring:scorecard', pk=pk)
                    messages.success(request, "Innings completed automatically. Chase is ready.")
                else:
                    messages.success(request, "Ball recorded successfully.")

        elif action == 'change_strike':
            state.striker, state.non_striker = state.non_striker, state.striker
            state.save()
            messages.success(request, "Strike changed.")

        elif action == 'undo_last_ball':
            reason = request.POST.get('reason', '').strip()
            if not reason:
                messages.error(request, "Correction reason is required.")
                return redirect('scoring:live-score', pk=pk)
            try:
                undone = undo_last_ball(match, request.user, reason)
                messages.success(
                    request,
                    f"Delivery {undone['over_number']}.{undone['ball_number_in_over']} was undone and scorecard recalculated.",
                )
            except ValueError as exc:
                messages.error(request, str(exc))

        elif action == 'complete_innings':
            with transaction.atomic():
                match_completed = complete_current_innings(match, state, setup)
                if match_completed:
                    messages.success(request, "Match completed.")
                    return redirect('scoring:scorecard', pk=pk)
                messages.success(request, "1st innings completed. Chase is ready.")

        return redirect('scoring:live-score', pk=pk)
