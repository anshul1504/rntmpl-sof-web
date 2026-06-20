from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Role, Tenant, User, UserTenant
from apps.auctions.models import AuctionEvent, AuctionFranchise, AuctionLot
from apps.players.models import PlayerProfile
from apps.teams.models import Team
from apps.tournaments.models import (
    Tournament,
    TournamentFormat,
    TournamentPlayer,
    TournamentTeam,
)


class AuctionClosureTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name='Auction League')
        self.user = User.objects.create_user(
            email='auction@example.com', password='strong-test-password'
        )
        role = Role.objects.create(
            tenant=self.tenant, name='Auction Manager', code='AUCTION_MANAGER'
        )
        UserTenant.objects.create(
            user=self.user, tenant=self.tenant, role=role, is_primary=True
        )
        self.client.force_login(self.user)
        session = self.client.session
        session['active_tenant_id'] = str(self.tenant.id)
        session.save()
        format_record = TournamentFormat.objects.create(
            name='Auction T20', code='AUC-T20', slug='auc-t20'
        )
        self.tournament = Tournament.objects.create(
            tenant=self.tenant,
            name='Auction Cup',
            slug='auction-cup',
            format=format_record,
        )
        self.team_one = TournamentTeam.objects.create(
            tournament=self.tournament,
            team=Team.objects.create(
                tenant=self.tenant, name='Bid Team', code='BID-TEAM'
            ),
        )
        self.team_two = TournamentTeam.objects.create(
            tournament=self.tournament,
            team=Team.objects.create(
                tenant=self.tenant, name='Other Team', code='OTHER-TEAM'
            ),
        )
        self.auction = AuctionEvent.objects.create(
            tournament=self.tournament,
            name='Main Auction',
            default_purse=Decimal('1000'),
            max_squad_size=2,
        )
        self.franchise = AuctionFranchise.objects.create(
            auction=self.auction,
            tournament_team=self.team_one,
            initial_purse=Decimal('1000'),
        )
        self.player = PlayerProfile.objects.create(
            tenant=self.tenant, first_name='Auction', last_name='Player'
        )
        self.lot = AuctionLot.objects.create(
            auction=self.auction,
            player=self.player,
            lot_number=1,
            base_price=Decimal('100'),
            current_price=Decimal('400'),
            current_bidder=self.franchise,
            status=AuctionLot.Status.LIVE,
        )

    def test_sold_lot_updates_purse_and_tournament_squad(self):
        response = self.client.post(
            reverse(
                'auctions:auction-lot-close',
                args=[self.lot.pk, 'sold'],
            )
        )

        self.assertEqual(response.status_code, 302)
        self.lot.refresh_from_db()
        self.franchise.refresh_from_db()
        self.assertEqual(self.lot.status, AuctionLot.Status.SOLD)
        self.assertEqual(self.franchise.purse_spent, Decimal('400'))
        self.assertTrue(
            TournamentPlayer.objects.filter(
                tournament_team=self.team_one, player=self.player
            ).exists()
        )

    def test_player_cannot_be_sold_to_second_tournament_team(self):
        TournamentPlayer.objects.create(
            tournament_team=self.team_two, player=self.player
        )

        self.client.post(
            reverse(
                'auctions:auction-lot-close',
                args=[self.lot.pk, 'sold'],
            )
        )

        self.lot.refresh_from_db()
        self.franchise.refresh_from_db()
        self.assertEqual(self.lot.status, AuctionLot.Status.LIVE)
        self.assertEqual(self.franchise.purse_spent, Decimal('0'))
