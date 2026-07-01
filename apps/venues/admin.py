from django.contrib import admin
from apps.venues.models import Venue, Ground, Pitch

admin.site.register(Venue)
admin.site.register(Ground)
admin.site.register(Pitch)
