"""
Enterprise Cricket Ecosystem - Main URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from apps.common.views import landing_page
from apps.publicsite.cms_admin import website_cms_site

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    path('website-admin/', website_cms_site.urls),
    # API Documentation
    path('api/v1/', include('apps.api.urls', namespace='api-v1')),
    # Schema, Swagger, Redoc
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-docs'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc-docs'),

    # Accounts (login, register, dashboard, profile, tenant management)
    path('accounts/', include('apps.accounts.urls')),

    # Players
    path('players/', include('apps.players.urls', namespace='players')),

    # Teams
    path('teams/', include('apps.teams.urls', namespace='teams')),

    # Tournaments
    path('tournaments/', include('apps.tournaments.urls', namespace='tournaments')),

    # Scoring
    path('scoring/', include('apps.scoring.urls', namespace='scoring')),
    path('venues/', include('apps.venues.urls', namespace='venues')),
    path('auctions/', include('apps.auctions.urls', namespace='auctions')),
    path('', include('apps.publicsite.urls', namespace='publicsite')),

    # AllAuth
    path('allauth/', include('allauth.urls')),

]

# Media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = 'apps.publicsite.views.public_404'
handler500 = 'apps.publicsite.views.public_500'
