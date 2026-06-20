from django.db import models

from apps.common.models import BaseModel, AddressMixin, ContactMixin


class Venue(BaseModel, AddressMixin, ContactMixin):
    tenant = models.ForeignKey(
        'accounts.Tenant',
        on_delete=models.CASCADE,
        related_name='venues',
        db_index=True,
    )
    name = models.CharField(max_length=255, db_index=True)
    short_name = models.CharField(max_length=50, blank=True, default='')
    capacity = models.PositiveIntegerField(default=0)
    owner_name = models.CharField(max_length=255, blank=True, default='')
    has_floodlights = models.BooleanField(default=False)
    has_practice_nets = models.BooleanField(default=False)
    has_dressing_rooms = models.BooleanField(default=True)
    has_medical_room = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = 'venues'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'name'], name='unique_venue_name_per_tenant'),
        ]

    def __str__(self):
        return self.name


class Ground(BaseModel):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='grounds')
    name = models.CharField(max_length=255)
    boundary_size_meters = models.PositiveIntegerField(null=True, blank=True)
    surface_type = models.CharField(
        max_length=30,
        choices=[
            ('GRASS', 'Natural Grass'),
            ('ARTIFICIAL', 'Artificial Turf'),
            ('MATTING', 'Matting'),
            ('OTHER', 'Other'),
        ],
        default='GRASS',
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'venues_grounds'
        ordering = ['venue', 'name']
        constraints = [
            models.UniqueConstraint(fields=['venue', 'name'], name='unique_ground_name_per_venue'),
        ]

    def __str__(self):
        return f'{self.venue.name} - {self.name}'


class Pitch(BaseModel):
    ground = models.ForeignKey(Ground, on_delete=models.CASCADE, related_name='pitches')
    code = models.CharField(max_length=30)
    pitch_type = models.CharField(
        max_length=30,
        choices=[
            ('BALANCED', 'Balanced'),
            ('BATTING', 'Batting friendly'),
            ('PACE', 'Pace friendly'),
            ('SPIN', 'Spin friendly'),
            ('GREEN', 'Green'),
            ('DRY', 'Dry'),
        ],
        default='BALANCED',
    )
    last_used_at = models.DateTimeField(null=True, blank=True)
    is_available = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'venues_pitches'
        constraints = [
            models.UniqueConstraint(fields=['ground', 'code'], name='unique_pitch_code_per_ground'),
        ]

    def __str__(self):
        return f'{self.ground} - Pitch {self.code}'
