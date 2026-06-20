from constance import config


def platform_settings(request):
    """Provide platform settings from Constance to all templates."""
    context = {
        'platform_name': config.PLATFORM_NAME,
        'platform_logo': config.PLATFORM_LOGO,
        'contact_email': config.CONTACT_EMAIL,
        'contact_phone': config.CONTACT_PHONE,
        'enable_ai_features': config.ENABLE_AI_FEATURES,
        'default_currency': config.DEFAULT_CURRENCY,
        'gst_enabled': config.GST_ENABLED,
        'gst_percentage': config.GST_PERCENTAGE,
        'current_tenant': getattr(request, 'tenant', None),
    }
    if request.user.is_authenticated:
        from apps.accounts.policies import get_active_membership, has_capability
        membership = get_active_membership(request)
        context['active_membership'] = membership
        context['active_role'] = membership.role if membership else None
        context['can_manage_roles'] = has_capability(request, 'roles.manage')
        context['can_manage_tournaments'] = has_capability(request, 'tournaments.manage')
        context['can_manage_teams'] = has_capability(request, 'teams.manage')
        context['can_manage_players'] = has_capability(request, 'players.manage')
        context['can_manage_scoring'] = has_capability(request, 'scoring.manage')
        context['can_manage_auctions'] = has_capability(request, 'auctions.manage')
        context['can_manage_venues'] = has_capability(request, 'venues.manage')
    return context
