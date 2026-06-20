from django import forms

from apps.auctions.models import AuctionEvent, AuctionLot, AuctionFranchise
from apps.players.models import PlayerProfile


class AuctionEventForm(forms.ModelForm):
    class Meta:
        model = AuctionEvent
        fields = ['name', 'auction_date', 'default_purse', 'minimum_bid_increment', 'max_squad_size']
        widgets = {'auction_date': forms.DateTimeInput(attrs={'type': 'datetime-local'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class AuctionLotForm(forms.ModelForm):
    class Meta:
        model = AuctionLot
        fields = ['player', 'lot_number', 'category', 'base_price']

    def __init__(self, *args, **kwargs):
        auction = kwargs.pop('auction')
        super().__init__(*args, **kwargs)
        existing = auction.lots.values_list('player_id', flat=True)
        self.fields['player'].queryset = PlayerProfile.objects.filter(
            tenant=auction.tournament.tenant,
            player_status='ACTIVE',
            is_deleted=False,
        ).exclude(pk__in=existing)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class BidForm(forms.Form):
    franchise = forms.ModelChoiceField(queryset=AuctionFranchise.objects.none())
    amount = forms.DecimalField(max_digits=12, decimal_places=2, min_value=1)

    def __init__(self, *args, **kwargs):
        lot = kwargs.pop('lot')
        super().__init__(*args, **kwargs)
        self.lot = lot
        self.fields['franchise'].queryset = lot.auction.franchises.select_related('tournament_team__team')
        self.fields['franchise'].widget.attrs['class'] = 'form-select'
        self.fields['amount'].widget.attrs['class'] = 'form-control'

    def clean(self):
        data = super().clean()
        franchise = data.get('franchise')
        amount = data.get('amount')
        minimum = (
            self.lot.base_price if not self.lot.current_bidder_id
            else self.lot.current_price + self.lot.auction.minimum_bid_increment
        )
        if amount is not None and amount < minimum:
            self.add_error('amount', f'Minimum valid bid is {minimum}.')
        if franchise and amount and amount > franchise.purse_remaining:
            self.add_error('amount', 'Bid exceeds the franchise purse remaining.')
        if franchise and franchise.players_bought >= self.lot.auction.max_squad_size:
            self.add_error('franchise', 'Franchise has reached the auction squad limit.')
        return data
