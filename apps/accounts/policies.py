from django.core.exceptions import PermissionDenied

from apps.accounts.models import UserTenant


ROLE_CAPABILITIES = {
    'TENANT_ADMIN': {'*'},
    'TOURNAMENT_MANAGER': {
        'tournaments.read', 'tournaments.manage', 'teams.read', 'players.read',
        'venues.read', 'scoring.read', 'publicsite.manage',
    },
    'TEAM_MANAGER': {
        'teams.read', 'teams.manage', 'players.read', 'players.manage',
        'tournaments.read', 'scoring.read',
    },
    'SCORER': {'scoring.read', 'scoring.manage', 'tournaments.read', 'teams.read', 'players.read'},
    'AUCTION_MANAGER': {
        'auctions.read', 'auctions.manage', 'tournaments.read', 'teams.read', 'players.read',
    },
    'VENUE_MANAGER': {'venues.read', 'venues.manage', 'tournaments.read'},
    'VIEWER': {
        'tournaments.read', 'teams.read', 'players.read', 'venues.read',
        'scoring.read', 'auctions.read',
    },
}

ROLE_PRESETS = {
    'TENANT_ADMIN': ('Tenant Admin', 'Full organization administration.'),
    'TOURNAMENT_MANAGER': ('Tournament Manager', 'Manage tournaments, fixtures and match setup.'),
    'TEAM_MANAGER': ('Team Manager', 'Manage teams, seasons, squads and players.'),
    'SCORER': ('Scorer', 'Operate live scoring and score corrections.'),
    'AUCTION_MANAGER': ('Auction Manager', 'Manage player auctions and bidding operations.'),
    'VENUE_MANAGER': ('Venue Manager', 'Manage venues, grounds and pitches.'),
    'VIEWER': ('Viewer', 'Read-only access to organization cricket data.'),
}


def get_active_membership(request):
    tenant = getattr(request, 'tenant', None)
    if not tenant or not request.user.is_authenticated:
        return None
    return (
        UserTenant.objects.select_related('role', 'tenant')
        .filter(user=request.user, tenant=tenant, is_active=True)
        .first()
    )


def has_capability(request, capability):
    if request.user.is_superuser:
        return True
    membership = get_active_membership(request)
    if not membership or not membership.role:
        return False
    allowed = ROLE_CAPABILITIES.get(membership.role.code, set())
    return '*' in allowed or capability in allowed


def require_capability(request, capability):
    if not has_capability(request, capability):
        raise PermissionDenied('Your assigned organization role does not allow this action.')


class CapabilityRequiredMixin:
    required_capability = None

    def dispatch(self, request, *args, **kwargs):
        require_capability(request, self.required_capability)
        return super().dispatch(request, *args, **kwargs)
