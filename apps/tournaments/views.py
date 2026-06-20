from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, FormView
from django.shortcuts import redirect
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
import uuid
from datetime import datetime, timedelta

from apps.accounts.models import Tenant
from apps.accounts.policies import CapabilityRequiredMixin
from apps.tournaments.models import (
    Tournament, TournamentTeam, TournamentPlayer, TournamentMatch,
    TournamentSponsor, TournamentAward, TournamentOfficial,
    TournamentPointsTable, TournamentGroup, TournamentRule, MatchSetup,
    MatchPlayingXI, MatchOfficialAssignment
)
from apps.tournaments.forms import (
    TournamentForm, TournamentTeamForm, TournamentPlayerForm, TournamentMatchForm,
    TournamentSponsorForm, TournamentAwardForm, TournamentOfficialForm,
    TournamentRuleForm, MatchSetupForm, MatchPlayingXIForm, MatchOfficialAssignmentForm
    , FixtureGeneratorForm
)


def get_active_tenant(request):
    """Retrieve active tenant from session or fallback to request.tenant."""
    tenant_id = request.session.get('active_tenant_id')
    if tenant_id:
        try:
            return Tenant.objects.get(id=tenant_id, is_deleted=False)
        except Tenant.DoesNotExist:
            pass
    return getattr(request, 'tenant', None)


def get_active_tenant_tournament(request, pk):
    """Fetch a tournament only inside the active tenant boundary."""
    tenant = get_active_tenant(request)
    if not tenant:
        raise Http404("No active tenant selected.")
    return get_object_or_404(
        Tournament,
        pk=pk,
        tenant=tenant,
        is_deleted=False,
    )


def get_active_tenant_tournament_team(request, pk):
    """Fetch a tournament team only inside the active tenant boundary."""
    tenant = get_active_tenant(request)
    if not tenant:
        raise Http404("No active tenant selected.")
    return get_object_or_404(
        TournamentTeam,
        pk=pk,
        tournament__tenant=tenant,
        is_deleted=False,
    )


class TournamentListView(LoginRequiredMixin, ListView):
    model = Tournament
    template_name = 'tournaments/tournament_list.html'
    context_object_name = 'tournaments'
    paginate_by = 10

    def get_queryset(self):
        tenant = get_active_tenant(self.request)
        if not tenant:
            return Tournament.objects.none()

        queryset = Tournament.objects.filter(tenant=tenant, is_deleted=False)

        # Search
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(venue__icontains=search_query) |
                Q(city__icontains=search_query)
            )

        # Status filter
        status_filter = self.request.GET.get('status', '')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset.select_related('format')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_tenant'] = get_active_tenant(self.request)
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        return context


class TournamentDetailView(LoginRequiredMixin, DetailView):
    model = Tournament
    template_name = 'tournaments/tournament_detail.html'
    context_object_name = 'tournament'

    def get_queryset(self):
        tenant = get_active_tenant(self.request)
        if not tenant:
            return Tournament.objects.none()
        return Tournament.objects.filter(tenant=tenant, is_deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tournament = self.object

        # Add related tournament information
        context['stages'] = tournament.tournaments_stageinstance_stages.all()
        context['teams'] = TournamentTeam.objects.filter(
            tournament=tournament, is_deleted=False
        ).select_related('team')
        context['matches'] = tournament.tournaments_tournamentmatch_matches.select_related('home_team__team', 'away_team__team').order_by('match_date', 'match_number')
        context['officials'] = tournament.tournaments_tournamentofficial_officials.select_related('official')
        context['awards'] = tournament.tournaments_tournamentaward_awards.select_related('winner')
        context['sponsors'] = tournament.tournaments_tournamentsponsor_sponsors.all()

        # Standings: gather all groups in this tournament and their points tables
        groups = TournamentGroup.objects.filter(
            stage_instance__tournament=tournament
        ).prefetch_related(
            'tournamentpointstable_standings__team__team'
        )
        standings_by_group = []
        for grp in groups:
            entries = TournamentPointsTable.objects.filter(
                group=grp
            ).select_related('team__team').order_by('position', '-points', '-net_run_rate')
            standings_by_group.append({
                'group': grp,
                'standings': entries,
            })
        context['standings_by_group'] = standings_by_group

        return context


class TournamentCreateView(LoginRequiredMixin, CapabilityRequiredMixin, CreateView):
    required_capability = 'tournaments.manage'
    model = Tournament
    form_class = TournamentForm
    template_name = 'tournaments/tournament_form.html'
    success_url = reverse_lazy('tournaments:tournament-list')

    def form_valid(self, form):
        tenant = get_active_tenant(self.request)
        if not tenant:
            messages.error(self.request, "No active organization context found.")
            from django.shortcuts import redirect
            return redirect('accounts:dashboard')

        form.instance.tenant = tenant
        
        # Generate slug
        base_slug = slugify(form.instance.name)
        unique_suffix = uuid.uuid4().hex[:6]
        form.instance.slug = f"{base_slug}-{unique_suffix}"

        messages.success(self.request, "Tournament created successfully.")
        return super().form_valid(form)


class TournamentUpdateView(LoginRequiredMixin, CapabilityRequiredMixin, UpdateView):
    required_capability = 'tournaments.manage'
    model = Tournament
    form_class = TournamentForm
    template_name = 'tournaments/tournament_form.html'

    def get_queryset(self):
        tenant = get_active_tenant(self.request)
        if not tenant:
            return Tournament.objects.none()
        return Tournament.objects.filter(tenant=tenant, is_deleted=False)

    def form_valid(self, form):
        messages.success(self.request, "Tournament updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('tournaments:tournament-detail', kwargs={'pk': self.object.pk})


class TournamentTeamCreateView(LoginRequiredMixin, CapabilityRequiredMixin, CreateView):
    required_capability = 'tournaments.manage'
    model = TournamentTeam
    form_class = TournamentTeamForm
    template_name = 'tournaments/tournament_team_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = get_active_tenant(self.request)
        kwargs['tournament'] = get_active_tenant_tournament(self.request, self.kwargs['tournament_id'])
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tournament'] = get_active_tenant_tournament(self.request, self.kwargs['tournament_id'])
        return context

    def form_valid(self, form):
        tournament = get_active_tenant_tournament(self.request, self.kwargs['tournament_id'])
        form.instance.tournament = tournament
        messages.success(self.request, "Team registered successfully to the tournament.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('tournaments:tournament-detail', kwargs={'pk': self.kwargs['tournament_id']})


class TournamentPlayerCreateView(LoginRequiredMixin, CapabilityRequiredMixin, CreateView):
    required_capability = 'tournaments.manage'
    model = TournamentPlayer
    form_class = TournamentPlayerForm
    template_name = 'tournaments/tournament_player_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = get_active_tenant(self.request)
        kwargs['tournament_team'] = get_active_tenant_tournament_team(self.request, self.kwargs['tournament_team_id'])
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tournament_team'] = get_active_tenant_tournament_team(self.request, self.kwargs['tournament_team_id'])
        return context

    def form_valid(self, form):
        t_team = get_active_tenant_tournament_team(self.request, self.kwargs['tournament_team_id'])
        form.instance.tournament_team = t_team
        messages.success(self.request, "Player added to squad successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        t_team = get_active_tenant_tournament_team(self.request, self.kwargs['tournament_team_id'])
        return reverse_lazy('tournaments:tournament-detail', kwargs={'pk': t_team.tournament.pk})


class TournamentMatchCreateView(LoginRequiredMixin, CapabilityRequiredMixin, CreateView):
    required_capability = 'tournaments.manage'
    model = TournamentMatch
    form_class = TournamentMatchForm
    template_name = 'tournaments/tournament_match_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tournament'] = get_active_tenant_tournament(self.request, self.kwargs['tournament_id'])
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tournament'] = get_active_tenant_tournament(self.request, self.kwargs['tournament_id'])
        return context

    def form_valid(self, form):
        tournament = get_active_tenant_tournament(self.request, self.kwargs['tournament_id'])
        form.instance.tournament = tournament
        if form.instance.venue_record:
            form.instance.venue = form.instance.venue_record.name
            form.instance.city = form.instance.venue_record.city
            form.instance.state = form.instance.venue_record.state
        if form.instance.ground_record:
            form.instance.ground = form.instance.ground_record.name
        messages.success(self.request, "Match scheduled successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('tournaments:tournament-detail', kwargs={'pk': self.kwargs['tournament_id']})


class TournamentMatchUpdateView(LoginRequiredMixin, CapabilityRequiredMixin, UpdateView):
    required_capability = 'tournaments.manage'
    model = TournamentMatch
    form_class = TournamentMatchForm
    template_name = 'tournaments/tournament_match_form.html'

    def get_queryset(self):
        tenant = get_active_tenant(self.request)
        return TournamentMatch.objects.filter(tournament__tenant=tenant, is_deleted=False)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tournament'] = self.object.tournament
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tournament'] = self.object.tournament
        context['is_reschedule'] = True
        return context

    def form_valid(self, form):
        if form.instance.venue_record:
            form.instance.venue = form.instance.venue_record.name
            form.instance.city = form.instance.venue_record.city
            form.instance.state = form.instance.venue_record.state
        if form.instance.ground_record:
            form.instance.ground = form.instance.ground_record.name
        messages.success(self.request, 'Fixture rescheduled successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('tournaments:tournament-detail', kwargs={'pk': self.object.tournament_id})


class FixtureGeneratorView(LoginRequiredMixin, CapabilityRequiredMixin, FormView):
    required_capability = 'tournaments.manage'
    form_class = FixtureGeneratorForm
    template_name = 'tournaments/fixture_generator_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.tournament = get_active_tenant_tournament(request, kwargs['tournament_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tournament'] = self.tournament
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tournament'] = self.tournament
        context['team_count'] = TournamentTeam.objects.filter(
            tournament=self.tournament, is_deleted=False
        ).count()
        return context

    def form_valid(self, form):
        teams = list(
            TournamentTeam.objects.filter(
                tournament=self.tournament, is_deleted=False
            ).order_by('seed', 'team__name')
        )
        if len(teams) < 2:
            form.add_error(None, 'Register at least two teams before generating fixtures.')
            return self.form_invalid(form)
        if TournamentMatch.objects.filter(tournament=self.tournament, is_deleted=False).exists():
            form.add_error(None, 'Fixtures already exist. Remove or manage existing fixtures before generating a new schedule.')
            return self.form_invalid(form)

        if len(teams) % 2:
            teams.append(None)
        fixed, rotating = teams[0], teams[1:]
        rounds = []
        for _ in range(len(teams) - 1):
            lineup = [fixed] + rotating
            pairs = []
            for index in range(len(teams) // 2):
                home, away = lineup[index], lineup[-(index + 1)]
                if home and away:
                    pairs.append((home, away))
            rounds.append(pairs)
            rotating = [rotating[-1]] + rotating[:-1]

        start = form.cleaned_data['start_date']
        first_time = form.cleaned_data['first_match_time']
        per_day = form.cleaned_data['matches_per_day']
        round_gap = form.cleaned_data['days_between_rounds']
        slot_gap = form.cleaned_data['slot_gap_minutes']
        venue = form.cleaned_data['venue']
        ground = venue.grounds.filter(is_active=True, is_deleted=False).first()
        fixtures = []
        match_number = 1
        for round_index, pairs in enumerate(rounds):
            for match_index, (home, away) in enumerate(pairs):
                day_offset = round_index * round_gap + (match_index // per_day)
                slot = match_index % per_day
                scheduled = timezone.make_aware(
                    datetime.combine(start + timedelta(days=day_offset), first_time)
                    + timedelta(minutes=slot * slot_gap)
                )
                fixtures.append(TournamentMatch(
                    tournament=self.tournament,
                    home_team=home if round_index % 2 == 0 else away,
                    away_team=away if round_index % 2 == 0 else home,
                    match_date=scheduled,
                    match_number=match_number,
                    venue_record=venue,
                    ground_record=ground,
                    venue=venue.name,
                    ground=ground.name if ground else '',
                    city=venue.city,
                    state=venue.state,
                ))
                match_number += 1
        TournamentMatch.objects.bulk_create(fixtures)
        messages.success(self.request, f'{len(fixtures)} round-robin fixtures generated.')
        return redirect('tournaments:tournament-detail', pk=self.tournament.pk)


class TournamentSponsorCreateView(LoginRequiredMixin, CapabilityRequiredMixin, CreateView):
    required_capability = 'tournaments.manage'
    model = TournamentSponsor
    form_class = TournamentSponsorForm
    template_name = 'tournaments/tournament_sponsor_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tournament'] = get_active_tenant_tournament(self.request, self.kwargs['tournament_id'])
        return context

    def form_valid(self, form):
        tournament = get_active_tenant_tournament(self.request, self.kwargs['tournament_id'])
        form.instance.tournament = tournament
        messages.success(self.request, "Sponsor added successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('tournaments:tournament-detail', kwargs={'pk': self.kwargs['tournament_id']})


class TournamentAwardCreateView(LoginRequiredMixin, CapabilityRequiredMixin, CreateView):
    required_capability = 'tournaments.manage'
    model = TournamentAward
    form_class = TournamentAwardForm
    template_name = 'tournaments/tournament_award_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = get_active_tenant(self.request)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tournament'] = get_active_tenant_tournament(self.request, self.kwargs['tournament_id'])
        return context

    def form_valid(self, form):
        tournament = get_active_tenant_tournament(self.request, self.kwargs['tournament_id'])
        form.instance.tournament = tournament
        messages.success(self.request, "Award added successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('tournaments:tournament-detail', kwargs={'pk': self.kwargs['tournament_id']})


class TournamentOfficialCreateView(LoginRequiredMixin, CapabilityRequiredMixin, CreateView):
    required_capability = 'tournaments.manage'
    model = TournamentOfficial
    form_class = TournamentOfficialForm
    template_name = 'tournaments/tournament_official_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = get_active_tenant(self.request)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tournament'] = get_active_tenant_tournament(self.request, self.kwargs['tournament_id'])
        return context

    def form_valid(self, form):
        tournament = get_active_tenant_tournament(self.request, self.kwargs['tournament_id'])
        form.instance.tournament = tournament
        messages.success(self.request, "Official assigned successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('tournaments:tournament-detail', kwargs={'pk': self.kwargs['tournament_id']})


class TournamentRuleUpdateView(LoginRequiredMixin, CapabilityRequiredMixin, UpdateView):
    required_capability = 'tournaments.manage'
    model = TournamentRule
    form_class = TournamentRuleForm
    template_name = 'tournaments/tournament_rules_form.html'

    def get_object(self, queryset=None):
        tournament = get_active_tenant_tournament(self.request, self.kwargs['tournament_id'])
        rule, _ = TournamentRule.objects.get_or_create(tournament=tournament)
        return rule

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tournament'] = self.object.tournament
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Tournament rules saved.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('tournaments:tournament-detail', kwargs={'pk': self.object.tournament_id})


def get_active_tenant_match(request, pk):
    tenant = get_active_tenant(request)
    if not tenant:
        raise Http404('No active tenant selected.')
    return get_object_or_404(TournamentMatch, pk=pk, tournament__tenant=tenant, is_deleted=False)


class MatchSetupView(LoginRequiredMixin, CapabilityRequiredMixin, FormView):
    required_capability = 'tournaments.manage'
    form_class = MatchSetupForm
    template_name = 'tournaments/match_setup_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.match = get_active_tenant_match(request, kwargs['pk'])
        self.setup, _ = MatchSetup.objects.get_or_create(match=self.match)
        if request.method == 'POST' and self.setup.lifecycle != MatchSetup.Lifecycle.SCHEDULED:
            raise PermissionDenied('Locked or active match setup cannot be changed.')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'match': self.match, 'instance': self.setup})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'match': self.match,
            'setup': self.setup,
            'home_xi': self.setup.playing_xi.filter(tournament_team=self.match.home_team),
            'away_xi': self.setup.playing_xi.filter(tournament_team=self.match.away_team),
            'official_assignments': self.setup.official_assignments.select_related('tournament_official__official'),
        })
        return context

    def form_valid(self, form):
        setup = form.save(commit=False)
        setup.match = self.match
        setup.toss_recorded_at = timezone.now()
        setup.save()
        messages.success(self.request, 'Toss details saved.')
        return redirect('tournaments:match-setup', pk=self.match.pk)


class MatchPlayingXIView(LoginRequiredMixin, CapabilityRequiredMixin, FormView):
    required_capability = 'tournaments.manage'
    form_class = MatchPlayingXIForm
    template_name = 'tournaments/match_playing_xi_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.match = get_active_tenant_match(request, kwargs['pk'])
        self.setup, _ = MatchSetup.objects.get_or_create(match=self.match)
        if request.method == 'POST' and self.setup.lifecycle != MatchSetup.Lifecycle.SCHEDULED:
            raise PermissionDenied('Locked or active playing XIs cannot be changed.')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['match'] = self.match
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['match'] = self.match
        return context

    def form_valid(self, form):
        team = form.cleaned_data['team']
        players = list(form.cleaned_data['players'])
        captain = form.cleaned_data['captain']
        keeper = form.cleaned_data['wicket_keeper']
        with transaction.atomic():
            self.setup.playing_xi.filter(tournament_team=team).delete()
            MatchPlayingXI.objects.bulk_create([
                MatchPlayingXI(
                    setup=self.setup,
                    tournament_team=team,
                    player=player,
                    batting_position=index,
                    is_captain=player == captain,
                    is_wicket_keeper=player == keeper,
                )
                for index, player in enumerate(players, start=1)
            ])
        messages.success(self.request, f'{team.team.name} playing XI saved.')
        return redirect('tournaments:match-setup', pk=self.match.pk)


class MatchOfficialAssignmentCreateView(LoginRequiredMixin, CapabilityRequiredMixin, CreateView):
    required_capability = 'tournaments.manage'
    model = MatchOfficialAssignment
    form_class = MatchOfficialAssignmentForm
    template_name = 'tournaments/match_official_assignment_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.match = get_active_tenant_match(request, kwargs['pk'])
        self.setup, _ = MatchSetup.objects.get_or_create(match=self.match)
        if request.method == 'POST' and self.setup.lifecycle != MatchSetup.Lifecycle.SCHEDULED:
            raise PermissionDenied('Locked or active official assignments cannot be changed.')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['match'] = self.match
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['match'] = self.match
        return context

    def form_valid(self, form):
        form.instance.setup = self.setup
        messages.success(self.request, 'Match official assigned.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('tournaments:match-setup', kwargs={'pk': self.match.pk})


class MatchSetupLockView(LoginRequiredMixin, CapabilityRequiredMixin, DetailView):
    required_capability = 'tournaments.manage'
    model = TournamentMatch

    def post(self, request, pk):
        match = get_active_tenant_match(request, pk)
        setup, _ = MatchSetup.objects.get_or_create(match=match)
        if not setup.is_ready:
            messages.error(request, 'Complete toss and both playing XIs before locking setup.')
        else:
            setup.lifecycle = MatchSetup.Lifecycle.READY
            setup.setup_locked_at = timezone.now()
            setup.setup_locked_by = request.user
            setup.save()
            messages.success(request, 'Match setup locked. Scoring is now enabled.')
        return redirect('tournaments:match-setup', pk=pk)
