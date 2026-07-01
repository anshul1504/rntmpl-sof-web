from django.urls import path
from apps.teams import views

app_name = 'teams'

urlpatterns = [
    path('', views.TeamListView.as_view(), name='team-list'),
    path('register/', views.TeamCreateView.as_view(), name='team-create'),
    path('<str:pk>/', views.TeamDetailView.as_view(), name='team-detail'),
    path('<str:pk>/edit/', views.TeamUpdateView.as_view(), name='team-edit'),
    path('<str:team_id>/seasons/add/', views.TeamSeasonCreateView.as_view(), name='team-season-create'),
    path('seasons/<str:pk>/edit/', views.TeamSeasonUpdateView.as_view(), name='team-season-edit'),
    path('seasons/<str:season_id>/squad/add/', views.TeamSquadCreateView.as_view(), name='team-squad-create'),
    path('squad/<str:pk>/edit/', views.TeamSquadUpdateView.as_view(), name='team-squad-edit'),
    path('squad/<str:pk>/remove/', views.TeamSquadRemoveView.as_view(), name='team-squad-remove'),
    path('seasons/<str:season_id>/staff/add/', views.TeamStaffCreateView.as_view(), name='team-staff-create'),
    path('staff/<str:pk>/edit/', views.TeamStaffUpdateView.as_view(), name='team-staff-edit'),
    path('staff/<str:pk>/remove/', views.TeamStaffRemoveView.as_view(), name='team-staff-remove'),
]
