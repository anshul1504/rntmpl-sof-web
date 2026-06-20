from django.urls import path
from apps.scoring import frontend_views

app_name = 'scoring'

urlpatterns = [
    path('', frontend_views.MatchListView.as_view(), name='match-list'),
    path('matches/<str:pk>/', frontend_views.MatchScorecardView.as_view(), name='scorecard'),
    path('matches/<str:pk>/score/', frontend_views.LiveScoringView.as_view(), name='live-score'),
]
