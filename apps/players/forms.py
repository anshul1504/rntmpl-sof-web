from django import forms
from apps.players.models import PlayerProfile, PlayerRole, BattingStyle, BowlingStyle, PlayerStatus

class PlayerProfileForm(forms.ModelForm):
    class Meta:
        model = PlayerProfile
        fields = [
            'first_name',
            'last_name',
            'date_of_birth',
            'gender',
            'nationality',
            'photo',
            'role',
            'batting_style',
            'bowling_style',
            'is_bowler',
            'is_wicket_keeper',
            'jersey_number',
            'height_cm',
            'weight_kg',
            'debut_date',
            'player_status',
            'notes',
            'biography',
            # ContactMixin fields
            'email',
            'phone',
            'alternate_phone',
            'website',
            # AddressMixin fields
            'address_line1',
            'address_line2',
            'city',
            'state',
            'district',
            'pincode',
            'country',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'debut_date': forms.DateInput(attrs={'type': 'date'}),
            'biography': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 2}),
            'address_line1': forms.TextInput(),
            'address_line2': forms.TextInput(),
        }
