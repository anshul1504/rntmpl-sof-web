from django import forms

from apps.venues.models import Venue, Ground, Pitch


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = (
                'form-check-input' if isinstance(field.widget, forms.CheckboxInput) else 'form-control'
            )


class VenueForm(StyledModelForm):
    class Meta:
        model = Venue
        fields = [
            'name', 'short_name', 'capacity', 'owner_name', 'address_line1', 'address_line2',
            'city', 'state', 'district', 'pincode', 'country', 'phone', 'email', 'website',
            'has_floodlights', 'has_practice_nets', 'has_dressing_rooms', 'has_medical_room',
            'is_active',
        ]


class GroundForm(StyledModelForm):
    class Meta:
        model = Ground
        fields = ['name', 'boundary_size_meters', 'surface_type', 'is_active']


class PitchForm(StyledModelForm):
    class Meta:
        model = Pitch
        fields = ['code', 'pitch_type', 'is_available', 'notes']
