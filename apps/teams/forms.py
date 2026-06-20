from django import forms
from django.core.exceptions import ValidationError

from apps.players.models import PlayerProfile
from apps.teams.models import Team, TeamSeason, TeamSquad, TeamStaff


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = [
            'name',
            'code',
            'short_name',
            'abbreviation',
            'team_category',
            'team_type',
            'logo',
            'jersey_color_primary',
            'jersey_color_secondary',
            'home_ground',
            'founded_date',
            'website',
            # ContactMixin fields
            'email',
            'phone',
            'alternate_phone',
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
            'founded_date': forms.DateInput(attrs={'type': 'date'}),
            'jersey_color_primary': forms.TextInput(attrs={'type': 'color', 'style': 'width: 60px; height: 40px; padding: 2px;'}),
            'jersey_color_secondary': forms.TextInput(attrs={'type': 'color', 'style': 'width: 60px; height: 40px; padding: 2px;'}),
        }


class TeamSeasonForm(forms.ModelForm):
    class Meta:
        model = TeamSeason
        fields = [
            'year', 'season', 'team_name', 'captain', 'vice_captain',
            'coach', 'assistant_coach', 'manager', 'is_active',
        ]
        widgets = {
            'year': forms.NumberInput(attrs={'min': 2000, 'max': 2100}),
        }

    def __init__(self, *args, team=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.team = team
        tenant = getattr(team, 'tenant', None)
        players = PlayerProfile.objects.filter(tenant=tenant, is_deleted=False).order_by(
            'first_name', 'last_name'
        ) if tenant else PlayerProfile.objects.none()
        self.fields['captain'].queryset = players
        self.fields['vice_captain'].queryset = players

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('captain') and cleaned.get('captain') == cleaned.get('vice_captain'):
            raise ValidationError('Captain and vice-captain must be different players.')
        return cleaned


class TeamSquadForm(forms.ModelForm):
    class Meta:
        model = TeamSquad
        fields = [
            'player', 'jersey_number', 'role', 'batting_order',
            'bowling_style', 'batting_style', 'is_captain',
            'is_vice_captain', 'is_wicket_keeper', 'joined_date',
            'left_date', 'is_active', 'contract_details',
        ]
        widgets = {
            'joined_date': forms.DateInput(attrs={'type': 'date'}),
            'left_date': forms.DateInput(attrs={'type': 'date'}),
            'contract_details': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, team_season=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.team_season = team_season
        tenant = getattr(getattr(team_season, 'team', None), 'tenant', None)
        queryset = PlayerProfile.objects.filter(
            tenant=tenant,
            is_deleted=False,
        ).order_by('first_name', 'last_name') if tenant else PlayerProfile.objects.none()
        if team_season:
            existing = TeamSquad.objects.filter(team_season=team_season)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            queryset = queryset.exclude(pk__in=existing.values('player_id'))
        self.fields['player'].queryset = queryset

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('is_captain') and cleaned.get('is_vice_captain'):
            raise ValidationError('A player cannot be captain and vice-captain at the same time.')
        if cleaned.get('left_date') and cleaned.get('joined_date'):
            if cleaned['left_date'] < cleaned['joined_date']:
                self.add_error('left_date', 'Leaving date cannot be before joining date.')
        return cleaned


class TeamStaffForm(forms.ModelForm):
    class Meta:
        model = TeamStaff
        fields = [
            'staff_type', 'name', 'contact_phone', 'contact_email',
            'qualifications', 'experience_years', 'joined_date',
            'end_date', 'is_active', 'notes',
        ]
        widgets = {
            'joined_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'qualifications': forms.Textarea(attrs={'rows': 2}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
