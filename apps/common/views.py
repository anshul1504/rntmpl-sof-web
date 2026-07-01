from django.shortcuts import render

from apps.accounts.models import Tenant, User
from apps.players.models import PlayerProfile
from apps.teams.models import Team
from apps.tournaments.models import Tournament, TournamentMatch


def landing_page(request):
    """Public product/demo landing page backed by current platform data."""
    stats = {
        'tenants': Tenant.objects.filter(is_deleted=False).count(),
        'players': PlayerProfile.objects.filter(is_deleted=False).count(),
        'teams': Team.objects.filter(is_deleted=False).count(),
        'tournaments': Tournament.objects.filter(is_deleted=False).count(),
        'matches': TournamentMatch.objects.filter(is_deleted=False).count(),
        'users': User.objects.filter(is_active=True).count(),
    }
    featured_tournaments = (
        Tournament.objects.filter(is_deleted=False)
        .select_related('tenant', 'format')
        .order_by('-is_featured', '-created_at')[:4]
    )
    upcoming_matches = (
        TournamentMatch.objects.filter(is_deleted=False)
        .select_related('tournament', 'home_team__team', 'away_team__team')
        .order_by('match_date', 'match_number')[:4]
    )
    return render(
        request,
        'common/landing.html',
        {
            'stats': stats,
            'featured_tournaments': featured_tournaments,
            'upcoming_matches': upcoming_matches,
            'completion_percent': 18,
        },
    )
