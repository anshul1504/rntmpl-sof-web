from django.urls import path
from apps.tournaments import views

app_name = 'tournaments'

urlpatterns = [
    path('', views.TournamentListView.as_view(), name='tournament-list'),
    path('create/', views.TournamentCreateView.as_view(), name='tournament-create'),
    path('<str:pk>/', views.TournamentDetailView.as_view(), name='tournament-detail'),
    path('<str:pk>/edit/', views.TournamentUpdateView.as_view(), name='tournament-edit'),
    path('<str:tournament_id>/teams/register/', views.TournamentTeamCreateView.as_view(), name='tournament-team-create'),
    path('teams/<str:tournament_team_id>/players/register/', views.TournamentPlayerCreateView.as_view(), name='tournament-player-create'),
    path('<str:tournament_id>/matches/schedule/', views.TournamentMatchCreateView.as_view(), name='tournament-match-create'),
    path('matches/<str:pk>/reschedule/', views.TournamentMatchUpdateView.as_view(), name='tournament-match-update'),
    path('<str:tournament_id>/fixtures/generate/', views.FixtureGeneratorView.as_view(), name='fixture-generate'),
    path('<str:tournament_id>/sponsors/add/', views.TournamentSponsorCreateView.as_view(), name='tournament-sponsor-create'),
    path('<str:tournament_id>/awards/add/', views.TournamentAwardCreateView.as_view(), name='tournament-award-create'),
    path('<str:tournament_id>/officials/add/', views.TournamentOfficialCreateView.as_view(), name='tournament-official-create'),
    path('<str:tournament_id>/rules/', views.TournamentRuleUpdateView.as_view(), name='tournament-rules'),
    path('matches/<str:pk>/setup/', views.MatchSetupView.as_view(), name='match-setup'),
    path('matches/<str:pk>/playing-xi/', views.MatchPlayingXIView.as_view(), name='match-playing-xi'),
    path('matches/<str:pk>/officials/', views.MatchOfficialAssignmentCreateView.as_view(), name='match-official-add'),
    path('matches/<str:pk>/setup/lock/', views.MatchSetupLockView.as_view(), name='match-setup-lock'),
]
