from django.contrib import admin
from apps.auctions.models import AuctionEvent, AuctionFranchise, AuctionLot, AuctionBid

admin.site.register(AuctionEvent)
admin.site.register(AuctionFranchise)
admin.site.register(AuctionLot)
admin.site.register(AuctionBid)
