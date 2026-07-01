from django.urls import path
from apps.venues import views

app_name = 'venues'

urlpatterns = [
    path('', views.VenueListView.as_view(), name='venue-list'),
    path('create/', views.VenueCreateView.as_view(), name='venue-create'),
    path('<str:pk>/', views.VenueDetailView.as_view(), name='venue-detail'),
    path('<str:venue_id>/grounds/add/', views.GroundCreateView.as_view(), name='ground-create'),
    path('grounds/<str:ground_id>/pitches/add/', views.PitchCreateView.as_view(), name='pitch-create'),
]
