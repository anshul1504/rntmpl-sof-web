from django.urls import path
from apps.players import views

app_name = 'players'

urlpatterns = [
    path('', views.PlayerListView.as_view(), name='player-list'),
    path('add/', views.PlayerCreateView.as_view(), name='player-create'),
    path('<str:pk>/', views.PlayerDetailView.as_view(), name='player-detail'),
    path('<str:pk>/edit/', views.PlayerUpdateView.as_view(), name='player-edit'),
]
