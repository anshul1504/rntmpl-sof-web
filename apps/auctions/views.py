from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, FormView

from apps.accounts.models import Tenant
from apps.auctions.forms import AuctionEventForm, AuctionLotForm, BidForm
from apps.accounts.policies import CapabilityRequiredMixin
from apps.auctions.models import AuctionEvent, AuctionFranchise, AuctionLot, AuctionBid
from apps.tournaments.models import Tournament, TournamentPlayer, TournamentTeam


def active_tenant(request):
    tenant_id = request.session.get('active_tenant_id')
    return Tenant.objects.filter(pk=tenant_id, is_deleted=False).first() if tenant_id else getattr(request, 'tenant', None)


class AuctionListView(LoginRequiredMixin, ListView):
    model = AuctionEvent
    template_name = 'auctions/auction_list.html'
    context_object_name = 'auctions'

    def get_queryset(self):
        tenant = active_tenant(self.request)
        return AuctionEvent.objects.filter(tournament__tenant=tenant, is_deleted=False).select_related('tournament') if tenant else AuctionEvent.objects.none()


class AuctionCreateView(LoginRequiredMixin, CapabilityRequiredMixin, CreateView):
    required_capability = 'auctions.manage'
    model = AuctionEvent
    form_class = AuctionEventForm
    template_name = 'auctions/auction_form.html'

    def dispatch(self, request, *args, **kwargs):
        tenant = active_tenant(request)
        self.tournament = get_object_or_404(Tournament, pk=kwargs['tournament_id'], tenant=tenant, is_deleted=False)
        if hasattr(self.tournament, 'auction'):
            return redirect('auctions:auction-detail', pk=self.tournament.auction.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        with transaction.atomic():
            form.instance.tournament = self.tournament
            response = super().form_valid(form)
            AuctionFranchise.objects.bulk_create([
                AuctionFranchise(
                    auction=self.object,
                    tournament_team=team,
                    initial_purse=self.object.default_purse,
                )
                for team in TournamentTeam.objects.filter(
                    tournament=self.tournament, is_deleted=False
                )
            ])
        messages.success(self.request, 'Auction created and franchise purses initialized.')
        return response

    def get_success_url(self):
        return reverse_lazy('auctions:auction-detail', kwargs={'pk': self.object.pk})


class AuctionDetailView(LoginRequiredMixin, DetailView):
    model = AuctionEvent
    template_name = 'auctions/auction_detail.html'
    context_object_name = 'auction'

    def get_queryset(self):
        tenant = active_tenant(self.request)
        return AuctionEvent.objects.filter(tournament__tenant=tenant, is_deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['franchises'] = self.object.franchises.select_related('tournament_team__team')
        context['lots'] = self.object.lots.select_related('player', 'current_bidder__tournament_team__team', 'winner__tournament_team__team')
        return context


class AuctionLotCreateView(LoginRequiredMixin, CapabilityRequiredMixin, CreateView):
    required_capability = 'auctions.manage'
    model = AuctionLot
    form_class = AuctionLotForm
    template_name = 'auctions/auction_lot_form.html'

    def dispatch(self, request, *args, **kwargs):
        tenant = active_tenant(request)
        self.auction = get_object_or_404(AuctionEvent, pk=kwargs['auction_id'], tournament__tenant=tenant)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['auction'] = self.auction
        return kwargs

    def form_valid(self, form):
        form.instance.auction = self.auction
        messages.success(self.request, 'Player lot added.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('auctions:auction-detail', kwargs={'pk': self.auction.pk})


class AuctionLotRoomView(LoginRequiredMixin, CapabilityRequiredMixin, FormView):
    required_capability = 'auctions.manage'
    form_class = BidForm
    template_name = 'auctions/auction_room.html'

    def dispatch(self, request, *args, **kwargs):
        tenant = active_tenant(request)
        self.lot = get_object_or_404(AuctionLot, pk=kwargs['pk'], auction__tournament__tenant=tenant)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['lot'] = self.lot
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lot'] = self.lot
        context['bids'] = self.lot.bids.select_related('franchise__tournament_team__team', 'placed_by')[:30]
        return context

    def form_valid(self, form):
        with transaction.atomic():
            lot = AuctionLot.objects.select_for_update().get(pk=self.lot.pk)
            franchise = AuctionFranchise.objects.select_for_update().get(pk=form.cleaned_data['franchise'].pk)
            amount = form.cleaned_data['amount']
            minimum = lot.base_price if not lot.current_bidder_id else lot.current_price + lot.auction.minimum_bid_increment
            if amount < minimum or amount > franchise.purse_remaining:
                form.add_error('amount', 'Bid is no longer valid. Refresh the current price and purse.')
                return self.form_invalid(form)
            lot.status = AuctionLot.Status.LIVE
            lot.current_bidder = franchise
            lot.current_price = amount
            lot.opened_at = lot.opened_at or timezone.now()
            lot.save()
            AuctionBid.objects.create(lot=lot, franchise=franchise, amount=amount, placed_by=self.request.user)
        messages.success(self.request, 'Bid accepted.')
        return redirect('auctions:auction-room', pk=self.lot.pk)


class AuctionLotCloseView(LoginRequiredMixin, CapabilityRequiredMixin, View):
    required_capability = 'auctions.manage'
    def post(self, request, pk, outcome):
        tenant = active_tenant(request)
        with transaction.atomic():
            lot = get_object_or_404(
                AuctionLot.objects.select_for_update(),
                pk=pk,
                auction__tournament__tenant=tenant,
            )
            if lot.status in {AuctionLot.Status.SOLD, AuctionLot.Status.UNSOLD}:
                messages.info(request, 'This lot is already closed.')
                return redirect('auctions:auction-room', pk=lot.pk)
            if outcome == 'sold':
                if not lot.current_bidder_id:
                    messages.error(request, 'A player cannot be sold without a valid bid.')
                    return redirect('auctions:auction-room', pk=lot.pk)
                franchise = AuctionFranchise.objects.select_for_update().get(pk=lot.current_bidder_id)
                if lot.current_price > franchise.purse_remaining:
                    messages.error(request, 'Franchise purse is insufficient.')
                    return redirect('auctions:auction-room', pk=lot.pk)
                if franchise.players_bought >= lot.auction.max_squad_size:
                    messages.error(request, 'Franchise has reached the auction squad limit.')
                    return redirect('auctions:auction-room', pk=lot.pk)
                existing_registration = TournamentPlayer.objects.filter(
                    tournament_team__tournament=lot.auction.tournament,
                    player=lot.player,
                    is_deleted=False,
                ).exclude(tournament_team=franchise.tournament_team)
                if existing_registration.exists():
                    messages.error(
                        request,
                        'This player is already assigned to another team in the tournament.',
                    )
                    return redirect('auctions:auction-room', pk=lot.pk)
                franchise.purse_spent += lot.current_price
                franchise.save(update_fields=['purse_spent', 'updated_at'])
                lot.status = AuctionLot.Status.SOLD
                lot.winner = franchise
                lot.sold_price = lot.current_price
                TournamentPlayer.objects.get_or_create(
                    tournament_team=franchise.tournament_team,
                    player=lot.player,
                    defaults={'role': lot.player.role, 'is_playing': True},
                )
                messages.success(request, f'{lot.player.full_name} sold to {franchise.tournament_team.team.name}.')
            else:
                lot.status = AuctionLot.Status.UNSOLD
                messages.info(request, f'{lot.player.full_name} marked unsold.')
            lot.closed_at = timezone.now()
            lot.save()
        return redirect('auctions:auction-detail', pk=lot.auction_id)
