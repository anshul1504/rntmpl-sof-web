from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from apps.accounts.models import Tenant
from apps.players.models import PlayerProfile
from apps.players.forms import PlayerProfileForm
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

class PlayerListView(LoginRequiredMixin, ListView):
    model = PlayerProfile
    template_name = 'players/player_list.html'
    context_object_name = 'players'
    paginate_by = 10

    def get_queryset(self):
        tenant = get_active_tenant(self.request)
        if not tenant:
            return PlayerProfile.objects.none()
            
        queryset = PlayerProfile.objects.filter(tenant=tenant, is_deleted=False)
        
        # Search functionality
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(jersey_number__icontains=search_query)
            )
            
        # Role filter
        role_filter = self.request.GET.get('role', '')
        if role_filter:
            queryset = queryset.filter(role=role_filter)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_tenant'] = get_active_tenant(self.request)
        context['search_query'] = self.request.GET.get('search', '')
        context['role_filter'] = self.request.GET.get('role', '')
        # Import choices for template
        from apps.players.models import PlayerRole
        context['roles'] = PlayerRole.choices
        return context

class PlayerDetailView(LoginRequiredMixin, DetailView):
    model = PlayerProfile
    template_name = 'players/player_detail.html'
    context_object_name = 'player'

    def get_queryset(self):
        tenant = get_active_tenant(self.request)
        if not tenant:
            return PlayerProfile.objects.none()
        return PlayerProfile.objects.filter(tenant=tenant, is_deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        player = self.object
        
        # Add ratings, contracts, career stats to context
        context['batting_skills'] = player.batting_skills.first()
        context['bowling_skills'] = player.bowling_skills.first()
        context['fielding_skills'] = player.fielding_skills.first()
        context['active_contract'] = player.contracts.filter(is_active=True).first()
        context['contracts'] = player.contracts.all()
        context['injuries'] = player.injuries.all()
        context['achievements'] = player.achievements.all()
        
        # Get career stats formatted
        try:
            context['career_stats'] = player.career_stats
        except AttributeError:
            context['career_stats'] = None
            
        return context

class PlayerCreateView(LoginRequiredMixin, CapabilityRequiredMixin, CreateView):
    required_capability = 'players.manage'
    model = PlayerProfile
    form_class = PlayerProfileForm
    template_name = 'players/player_form.html'
    success_url = reverse_lazy('players:player-list')

    def form_valid(self, form):
        tenant = get_active_tenant(self.request)
        if not tenant:
            messages.error(self.request, "No active organization context found.")
            return redirect('accounts:dashboard')
        
        form.instance.tenant = tenant
        messages.success(self.request, "Player profile created successfully.")
        return super().form_valid(form)

class PlayerUpdateView(LoginRequiredMixin, CapabilityRequiredMixin, UpdateView):
    required_capability = 'players.manage'
    model = PlayerProfile
    form_class = PlayerProfileForm
    template_name = 'players/player_form.html'

    def get_queryset(self):
        tenant = get_active_tenant(self.request)
        if not tenant:
            return PlayerProfile.objects.none()
        return PlayerProfile.objects.filter(tenant=tenant, is_deleted=False)

    def form_valid(self, form):
        messages.success(self.request, "Player profile updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('players:player-detail', kwargs={'pk': self.object.pk})
