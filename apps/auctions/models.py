from decimal import Decimal

from django.db import models
from django.utils import timezone

from apps.common.models import BaseModel


class AuctionEvent(BaseModel):
    class Lifecycle(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        READY = 'READY', 'Ready'
        LIVE = 'LIVE', 'Live'
        PAUSED = 'PAUSED', 'Paused'
        COMPLETED = 'COMPLETED', 'Completed'

    tournament = models.OneToOneField(
        'tournaments.Tournament',
        on_delete=models.CASCADE,
        related_name='auction',
    )
    name = models.CharField(max_length=255)
    auction_date = models.DateTimeField(null=True, blank=True)
    default_purse = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('10000000'))
    minimum_bid_increment = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('50000'))
    max_squad_size = models.PositiveIntegerField(default=25)
    lifecycle = models.CharField(max_length=20, choices=Lifecycle.choices, default=Lifecycle.DRAFT)

    class Meta:
        db_table = 'auctions_events'

    def __str__(self):
        return self.name


class AuctionFranchise(BaseModel):
    auction = models.ForeignKey(AuctionEvent, on_delete=models.CASCADE, related_name='franchises')
    tournament_team = models.OneToOneField(
        'tournaments.TournamentTeam',
        on_delete=models.CASCADE,
        related_name='auction_franchise',
    )
    initial_purse = models.DecimalField(max_digits=14, decimal_places=2)
    purse_spent = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        db_table = 'auctions_franchises'

    @property
    def purse_remaining(self):
        return self.initial_purse - self.purse_spent

    @property
    def players_bought(self):
        return self.winning_lots.filter(status=AuctionLot.Status.SOLD).count()

    def __str__(self):
        return f'{self.auction} - {self.tournament_team.team.name}'


class AuctionLot(BaseModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        LIVE = 'LIVE', 'Live'
        SOLD = 'SOLD', 'Sold'
        UNSOLD = 'UNSOLD', 'Unsold'
        WITHDRAWN = 'WITHDRAWN', 'Withdrawn'

    auction = models.ForeignKey(AuctionEvent, on_delete=models.CASCADE, related_name='lots')
    player = models.ForeignKey('players.PlayerProfile', on_delete=models.CASCADE, related_name='auction_lots')
    lot_number = models.PositiveIntegerField()
    category = models.CharField(max_length=50, blank=True, default='')
    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    current_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_bidder = models.ForeignKey(
        AuctionFranchise,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leading_lots',
    )
    winner = models.ForeignKey(
        AuctionFranchise,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='winning_lots',
    )
    sold_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'auctions_lots'
        ordering = ['lot_number']
        constraints = [
            models.UniqueConstraint(fields=['auction', 'player'], name='unique_player_per_auction'),
            models.UniqueConstraint(fields=['auction', 'lot_number'], name='unique_lot_number_per_auction'),
        ]

    def __str__(self):
        return f'Lot {self.lot_number}: {self.player}'


class AuctionBid(BaseModel):
    lot = models.ForeignKey(AuctionLot, on_delete=models.CASCADE, related_name='bids')
    franchise = models.ForeignKey(AuctionFranchise, on_delete=models.CASCADE, related_name='bids')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    placed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='auction_bids',
    )
    placed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'auctions_bids'
        ordering = ['-placed_at']

    def __str__(self):
        return f'{self.franchise} - {self.amount}'
