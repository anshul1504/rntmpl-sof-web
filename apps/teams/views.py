from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from apps.accounts.models import Tenant
from apps.teams.models import Team, TeamSeason, TeamSquad, TeamStaff
from apps.teams.forms import TeamForm, TeamSeasonForm, TeamSquadForm, TeamStaffForm
from apps.accounts.policies import CapabilityRequiredMixin


def get_active_tenant(request):
    """Retrieve active tenant from session or fallback to request.tenant."""
    tenant_id = request.session.get('active_tenant_id')
    if tenant_id:
        try:
            return Tenant.objects.get(id=tenant_id, is_deleted=False)
        except Tenant.DoesNotExist:
            pass
    return getattr(request, 'tenant', None)


def get_active_tenant_team(request, pk):
    tenant = get_active_tenant(request)
    if not tenant:
        raise Http404('No active organization selected.')
    return get_object_or_404(Team, pk=pk, tenant=tenant, is_deleted=False)


def get_active_tenant_season(request, pk):
    tenant = get_active_tenant(request)
    return get_object_or_404(
        TeamSeason,
        pk=pk,
        team__tenant=tenant,
        is_deleted=False,
    )


def sync_team_season_squad(season):
    """Keep denormalized squad leadership and size consistent."""
    active_members = season.teamsquad_players.filter(
        is_deleted=False, is_active=True
    )
    captain = active_members.filter(is_captain=True).select_related('player').first()
    vice_captain = active_members.filter(
        is_vice_captain=True
    ).select_related('player').first()
    season.squad_size = active_members.count()
    season.captain = captain.player if captain else None
    season.vice_captain = vice_captain.player if vice_captain else None
    season.save(
        update_fields=['squad_size', 'captain', 'vice_captain', 'updated_at']
    )


class TeamListView(LoginRequiredMixin, ListView):
    model = Team
    template_name = 'teams/team_list.html'
    context_object_name = 'teams'
    paginate_by = 12

    def get_queryset(self):
        tenant = get_active_tenant(self.request)
        if not tenant:
            return Team.objects.none()

        queryset = Team.objects.filter(tenant=tenant, is_deleted=False)

        # Search functionality
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(code__icontains=search_query) |
                Q(short_name__icontains=search_query)
            )

        # Active filter
        status_filter = self.request.GET.get('status', '')
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)

        return queryset.select_related('team_category', 'team_type')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_tenant'] = get_active_tenant(self.request)
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        return context


class TeamDetailView(LoginRequiredMixin, DetailView):
    model = Team
    template_name = 'teams/team_detail.html'
    context_object_name = 'team'

    def get_queryset(self):
        tenant = get_active_tenant(self.request)
        if not tenant:
            return Team.objects.none()
        return Team.objects.filter(tenant=tenant, is_deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.object

        # Stats
        context['stats'] = team.teamstat_stats.filter(context='OVERALL').first()

        # Squad & seasons
        context['seasons'] = team.teamseason_seasons.filter(is_deleted=False).order_by('-year', 'season')
        active_season = context['seasons'].filter(is_active=True).first() or context['seasons'].first()
        context['active_season'] = active_season
        context['squad'] = (
            active_season.teamsquad_players.filter(is_deleted=False).select_related('player')
            if active_season else TeamSquad.objects.none()
        )
        context['staff_members'] = (
            active_season.teamstaff_members.filter(is_deleted=False)
            if active_season else TeamStaff.objects.none()
        )
        context['achievements'] = team.teamachievement_achievements.all()[:6]
        context['sponsorships'] = team.teamsponsorship_sponsorships.filter(is_active=True)

        # Player contracts (via PlayerContract model)
        context['active_contracts'] = team.player_contracts.filter(is_active=True).select_related('player')[:10]

        return context


class TeamCreateView(LoginRequiredMixin, CapabilityRequiredMixin, CreateView):
    required_capability = 'teams.manage'
    model = Team
    form_class = TeamForm
    template_name = 'teams/team_form.html'
    success_url = reverse_lazy('teams:team-list')

    def form_valid(self, form):
        tenant = get_active_tenant(self.request)
        if not tenant:
            messages.error(self.request, "No active organization context found.")
            from django.shortcuts import redirect
            return redirect('accounts:dashboard')

        form.instance.tenant = tenant
        messages.success(self.request, "Team registered successfully.")
        return super().form_valid(form)


class TeamUpdateView(LoginRequiredMixin, CapabilityRequiredMixin, UpdateView):
    required_capability = 'teams.manage'
    model = Team
    form_class = TeamForm
    template_name = 'teams/team_form.html'

    def get_queryset(self):
        tenant = get_active_tenant(self.request)
        if not tenant:
            return Team.objects.none()
        return Team.objects.filter(tenant=tenant, is_deleted=False)

    def form_valid(self, form):
        messages.success(self.request, "Team profile updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('teams:team-detail', kwargs={'pk': self.object.pk})


class TeamSeasonCreateView(LoginRequiredMixin, CapabilityRequiredMixin, CreateView):
    required_capability = 'teams.manage'
    model = TeamSeason
    form_class = TeamSeasonForm
    template_name = 'teams/team_season_form.html'

    def get_team(self):
        return get_active_tenant_team(self.request, self.kwargs['team_id'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['team'] = self.get_team()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = self.get_team()
        return context

    def form_valid(self, form):
        form.instance.team = self.get_team()
        messages.success(self.request, 'Team season created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('teams:team-detail', args=[self.kwargs['team_id']])


class TeamSeasonUpdateView(LoginRequiredMixin, CapabilityRequiredMixin, UpdateView):
    required_capability = 'teams.manage'
    model = TeamSeason
    form_class = TeamSeasonForm
    template_name = 'teams/team_season_form.html'

    def get_object(self, queryset=None):
        return get_active_tenant_season(self.request, self.kwargs['pk'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['team'] = self.object.team
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = self.object.team
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Team season updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('teams:team-detail', args=[self.object.team_id])


class TeamSquadCreateView(LoginRequiredMixin, CapabilityRequiredMixin, CreateView):
    required_capability = 'teams.manage'
    model = TeamSquad
    form_class = TeamSquadForm
    template_name = 'teams/team_squad_form.html'

    def get_season(self):
        return get_active_tenant_season(self.request, self.kwargs['season_id'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['team_season'] = self.get_season()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team_season'] = self.get_season()
        return context

    def form_valid(self, form):
        season = self.get_season()
        form.instance.team_season = season
        response = super().form_valid(form)
        self._sync_season(season)
        messages.success(self.request, 'Player added to the team squad.')
        return response

    def _sync_season(self, season):
        member = self.object
        if member.is_captain:
            season.teamsquad_players.exclude(pk=member.pk).update(
                is_captain=False
            )
        if member.is_vice_captain:
            season.teamsquad_players.exclude(pk=member.pk).update(
                is_vice_captain=False
            )
        sync_team_season_squad(season)

    def get_success_url(self):
        return reverse('teams:team-detail', args=[self.get_season().team_id])


class TeamSquadUpdateView(LoginRequiredMixin, CapabilityRequiredMixin, UpdateView):
    required_capability = 'teams.manage'
    model = TeamSquad
    form_class = TeamSquadForm
    template_name = 'teams/team_squad_form.html'

    def get_object(self, queryset=None):
        tenant = get_active_tenant(self.request)
        return get_object_or_404(
            TeamSquad,
            pk=self.kwargs['pk'],
            team_season__team__tenant=tenant,
            is_deleted=False,
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['team_season'] = self.object.team_season
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team_season'] = self.object.team_season
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        season = self.object.team_season
        if self.object.is_captain:
            season.teamsquad_players.exclude(pk=self.object.pk).update(is_captain=False)
        if self.object.is_vice_captain:
            season.teamsquad_players.exclude(pk=self.object.pk).update(is_vice_captain=False)
        sync_team_season_squad(season)
        messages.success(self.request, 'Squad member updated successfully.')
        return response

    def get_success_url(self):
        return reverse('teams:team-detail', args=[self.object.team_season.team_id])


class TeamSquadRemoveView(LoginRequiredMixin, CapabilityRequiredMixin, View):
    required_capability = 'teams.manage'
    def post(self, request, pk):
        tenant = get_active_tenant(request)
        member = get_object_or_404(
            TeamSquad,
            pk=pk,
            team_season__team__tenant=tenant,
            is_deleted=False,
        )
        season = member.team_season
        member.delete()
        sync_team_season_squad(season)
        messages.success(request, 'Player removed from the squad.')
        return redirect('teams:team-detail', pk=season.team_id)


class TeamStaffCreateView(LoginRequiredMixin, CapabilityRequiredMixin, CreateView):
    required_capability = 'teams.manage'
    model = TeamStaff
    form_class = TeamStaffForm
    template_name = 'teams/team_staff_form.html'

    def get_season(self):
        return get_active_tenant_season(self.request, self.kwargs['season_id'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team_season'] = self.get_season()
        return context

    def form_valid(self, form):
        form.instance.team_season = self.get_season()
        messages.success(self.request, 'Staff member added successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('teams:team-detail', args=[self.get_season().team_id])


class TeamStaffUpdateView(LoginRequiredMixin, CapabilityRequiredMixin, UpdateView):
    required_capability = 'teams.manage'
    model = TeamStaff
    form_class = TeamStaffForm
    template_name = 'teams/team_staff_form.html'

    def get_object(self, queryset=None):
        tenant = get_active_tenant(self.request)
        return get_object_or_404(
            TeamStaff,
            pk=self.kwargs['pk'],
            team_season__team__tenant=tenant,
            is_deleted=False,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team_season'] = self.object.team_season
        return context

    def get_success_url(self):
        messages.success(self.request, 'Staff member updated successfully.')
        return reverse('teams:team-detail', args=[self.object.team_season.team_id])


class TeamStaffRemoveView(LoginRequiredMixin, CapabilityRequiredMixin, View):
    required_capability = 'teams.manage'
    def post(self, request, pk):
        tenant = get_active_tenant(request)
        member = get_object_or_404(
            TeamStaff,
            pk=pk,
            team_season__team__tenant=tenant,
            is_deleted=False,
        )
        team_id = member.team_season.team_id
        member.delete()
        messages.success(request, 'Staff member removed successfully.')
        return redirect('teams:team-detail', pk=team_id)
