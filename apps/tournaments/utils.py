from decimal import Decimal
from django.db.models import Q
from apps.tournaments.models import (
    TournamentPointsTable,
    TournamentGroup,
    TournamentStage,
    TournamentStageInstance,
    TournamentMatch,
)

def update_points_table(match):
    """
    Recalculate standing statistics for the home and away teams in a completed match.
    """
    if not match.is_completed:
        return

    # Ensure we have a TournamentGroup
    group = match.group
    if not group:
        # Fallback to finding or creating a default group for the match's stage
        stage_instance = match.stage_instance
        if not stage_instance:
            stage, _ = TournamentStage.objects.get_or_create(
                format=match.tournament.format,
                name='Group Stage',
                defaults={
                    'sequence': 1,
                    'is_group_stage': True,
                    'number_of_groups': 1,
                }
            )
            # If no stage, get or create the first one for the tournament
            stage_instance, _ = TournamentStageInstance.objects.get_or_create(
                tournament=match.tournament,
                stage=stage,
                defaults={'name': 'Group Stage', 'sequence': 1}
            )
        group, _ = TournamentGroup.objects.get_or_create(
            stage_instance=stage_instance,
            defaults={'name': 'Group A', 'code': 'GA'}
        )
        match.group = group
        match.save(update_fields=['group'])

    # Get or create points table entries for both teams
    home_standing, _ = TournamentPointsTable.objects.get_or_create(
        group=group,
        team=match.home_team
    )
    away_standing, _ = TournamentPointsTable.objects.get_or_create(
        group=group,
        team=match.away_team
    )

    # Recalculate all matches for these teams in this group
    for standing, team in [(home_standing, match.home_team), (away_standing, match.away_team)]:
        # Fetch all completed matches for this team in this group
        team_matches = TournamentMatch.objects.filter(
            Q(group=group) & Q(is_completed=True) & (Q(home_team=team) | Q(away_team=team))
        )

        played = team_matches.count()
        won = 0
        lost = 0
        drawn = 0
        points = Decimal('0.00')

        # Simple runs / overs trackers for Net Run Rate (NRR)
        runs_for = 0
        runs_against = 0
        overs_for = Decimal('0.0')
        overs_against = Decimal('0.0')

        # Points configuration from tournament format (fallback to win=2, draw/tie=1)
        fmt = match.tournament.format
        pts_win = Decimal(str(fmt.points_for_win)) if fmt else Decimal('2.00')
        pts_draw = Decimal(str(fmt.points_for_draw)) if fmt else Decimal('1.00')
        pts_loss = Decimal(str(fmt.points_for_loss)) if fmt else Decimal('0.00')

        for m in team_matches:
            # Determine winner/loser
            if m.winner == team:
                won += 1
                points += pts_win
            elif m.loser == team:
                lost += 1
                points += pts_loss
            else:
                drawn += 1
                points += pts_draw

            # NRR calculation helper
            def parse_runs(score_str):
                if not score_str:
                    return 0
                try:
                    return int(score_str.split('/')[0])
                except ValueError:
                    return 0

            h_runs = parse_runs(m.home_team_score)
            a_runs = parse_runs(m.away_team_score)

            if m.home_team == team:
                runs_for += h_runs
                runs_against += a_runs
                if m.home_team_overs:
                    overs_for += m.home_team_overs
                if m.away_team_overs:
                    overs_against += m.away_team_overs
            else:
                runs_for += a_runs
                runs_against += h_runs
                if m.away_team_overs:
                    overs_for += m.away_team_overs
                if m.home_team_overs:
                    overs_against += m.home_team_overs

        standing.matches_played = played
        standing.matches_won = won
        standing.matches_lost = lost
        standing.matches_drawn = drawn
        standing.points = points
        standing.runs_for = runs_for
        standing.runs_against = runs_against
        standing.overs_for = overs_for
        standing.overs_against = overs_against

        # NRR = (Runs Scored / Overs Faced) - (Runs Conceded / Overs Bowled)
        if overs_for > 0 and overs_against > 0:
            standing.net_run_rate = (Decimal(str(runs_for)) / Decimal(str(overs_for))) - (Decimal(str(runs_against)) / Decimal(str(overs_against)))
        else:
            standing.net_run_rate = Decimal('0.0000')

        standing.save()

    # Recalculate standings positions in this group
    all_standings = TournamentPointsTable.objects.filter(group=group).order_by('-points', '-net_run_rate')
    for index, std in enumerate(all_standings):
        std.position = index + 1
        std.save(update_fields=['position'])
