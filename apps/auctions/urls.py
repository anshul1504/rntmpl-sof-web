from django.urls import path
from apps.auctions import views

app_name = 'auctions'

urlpatterns = [
    path('', views.AuctionListView.as_view(), name='auction-list'),
    path('tournaments/<str:tournament_id>/create/', views.AuctionCreateView.as_view(), name='auction-create'),
    path('<str:pk>/', views.AuctionDetailView.as_view(), name='auction-detail'),
    path('<str:auction_id>/lots/add/', views.AuctionLotCreateView.as_view(), name='auction-lot-add'),
    path('lots/<str:pk>/room/', views.AuctionLotRoomView.as_view(), name='auction-room'),
    path('lots/<str:pk>/close/<str:outcome>/', views.AuctionLotCloseView.as_view(), name='auction-lot-close'),
]
