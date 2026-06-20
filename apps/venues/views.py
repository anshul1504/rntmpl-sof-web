from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView

from apps.accounts.models import Tenant
from apps.venues.forms import VenueForm, GroundForm, PitchForm
from apps.accounts.policies import CapabilityRequiredMixin
from apps.venues.models import Venue, Ground, Pitch


def active_tenant(request):
    tenant_id = request.session.get('active_tenant_id')
    if tenant_id:
        return Tenant.objects.filter(pk=tenant_id, is_deleted=False).first()
    return getattr(request, 'tenant', None)


class VenueListView(LoginRequiredMixin, ListView):
    model = Venue
    template_name = 'venues/venue_list.html'
    context_object_name = 'venues'

    def get_queryset(self):
        tenant = active_tenant(self.request)
        return Venue.objects.filter(tenant=tenant, is_deleted=False).prefetch_related('grounds') if tenant else Venue.objects.none()


class VenueDetailView(LoginRequiredMixin, DetailView):
    model = Venue
    template_name = 'venues/venue_detail.html'
    context_object_name = 'venue'

    def get_queryset(self):
        tenant = active_tenant(self.request)
        return Venue.objects.filter(tenant=tenant, is_deleted=False) if tenant else Venue.objects.none()


class VenueCreateView(LoginRequiredMixin, CapabilityRequiredMixin, CreateView):
    required_capability = 'venues.manage'
    model = Venue
    form_class = VenueForm
    template_name = 'venues/venue_form.html'
    success_url = reverse_lazy('venues:venue-list')

    def form_valid(self, form):
        tenant = active_tenant(self.request)
        if not tenant:
            raise Http404('No active organization selected.')
        form.instance.tenant = tenant
        messages.success(self.request, 'Venue created.')
        return super().form_valid(form)


class GroundCreateView(LoginRequiredMixin, CapabilityRequiredMixin, CreateView):
    required_capability = 'venues.manage'
    model = Ground
    form_class = GroundForm
    template_name = 'venues/ground_form.html'

    def dispatch(self, request, *args, **kwargs):
        tenant = active_tenant(request)
        self.venue = get_object_or_404(Venue, pk=kwargs['venue_id'], tenant=tenant, is_deleted=False)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.venue = self.venue
        messages.success(self.request, 'Ground added.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('venues:venue-detail', kwargs={'pk': self.venue.pk})


class PitchCreateView(LoginRequiredMixin, CapabilityRequiredMixin, CreateView):
    required_capability = 'venues.manage'
    model = Pitch
    form_class = PitchForm
    template_name = 'venues/pitch_form.html'

    def dispatch(self, request, *args, **kwargs):
        tenant = active_tenant(request)
        self.ground = get_object_or_404(Ground, pk=kwargs['ground_id'], venue__tenant=tenant, is_deleted=False)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.ground = self.ground
        messages.success(self.request, 'Pitch added.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('venues:venue-detail', kwargs={'pk': self.ground.venue_id})
