from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from apps.tournaments.models import (
    Tournament, TournamentFormat, TournamentTeam, TournamentPlayer, TournamentMatch,
    TournamentSponsor, TournamentAward, TournamentOfficial
    , TournamentRule, MatchSetup, MatchPlayingXI, MatchOfficialAssignment
)
from apps.teams.models import Team
from apps.players.models import PlayerProfile
from apps.venues.models import Venue, Ground


class TournamentForm(forms.ModelForm):
    class Meta:
        model = Tournament
        fields = [
            'name',
            'format',
            'season',
            'start_date',
            'end_date',
            'registration_start_date',
            'registration_end_date',
            'venue',
            'city',
            'state',
            'country',
            'rules_and_regulations',
            'prize_money',
            'entry_fee',
            'max_teams_allowed',
            'logo',
            'banner_image',
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'registration_start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'registration_end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'rules_and_regulations': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.FileInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control'})


class TournamentTeamForm(forms.ModelForm):
    class Meta:
        model = TournamentTeam
        fields = ['team', 'jersey_color', 'captain', 'vice_captain', 'is_verified']

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        tournament = kwargs.pop('tournament', None)
        self.tournament = tournament
        super().__init__(*args, **kwargs)
        
        # Filter teams and players by tenant
        if tenant:
            self.fields['team'].queryset = Team.objects.filter(tenant=tenant, is_deleted=False)
            self.fields['captain'].queryset = PlayerProfile.objects.filter(tenant=tenant, is_deleted=False)
            self.fields['vice_captain'].queryset = PlayerProfile.objects.filter(tenant=tenant, is_deleted=False)

        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.FileInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})

    def clean(self):
        cleaned_data = super().clean()
        team = cleaned_data.get('team')
        captain = cleaned_data.get('captain')
        vice_captain = cleaned_data.get('vice_captain')

        if self.tournament and team:
            exists = TournamentTeam.objects.filter(
                tournament=self.tournament,
                team=team,
                is_deleted=False,
            )
            if self.instance.pk:
                exists = exists.exclude(pk=self.instance.pk)
            if exists.exists():
                raise ValidationError('This team is already registered in this tournament.')

        if captain and vice_captain and captain == vice_captain:
            raise ValidationError('Captain and vice captain must be different players.')

        return cleaned_data


class TournamentPlayerForm(forms.ModelForm):
    class Meta:
        model = TournamentPlayer
        fields = ['player', 'jersey_number', 'is_playing', 'role']

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        self.tournament_team = kwargs.pop('tournament_team', None)
        super().__init__(*args, **kwargs)

        if tenant:
            self.fields['player'].queryset = PlayerProfile.objects.filter(tenant=tenant, is_deleted=False)

        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.FileInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})

    def clean(self):
        cleaned_data = super().clean()
        player = cleaned_data.get('player')

        if self.tournament_team and player:
            exists = TournamentPlayer.objects.filter(
                tournament_team=self.tournament_team,
                player=player,
                is_deleted=False,
            )
            if self.instance.pk:
                exists = exists.exclude(pk=self.instance.pk)
            if exists.exists():
                raise ValidationError('This player is already in this tournament squad.')

        return cleaned_data


class TournamentMatchForm(forms.ModelForm):
    class Meta:
        model = TournamentMatch
        fields = ['home_team', 'away_team', 'match_date', 'venue_record', 'ground_record', 'match_number']
        widgets = {
            'match_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        tournament = kwargs.pop('tournament', None)
        self.tournament = tournament
        super().__init__(*args, **kwargs)

        if tournament:
            self.fields['home_team'].queryset = TournamentTeam.objects.filter(tournament=tournament, is_deleted=False)
            self.fields['away_team'].queryset = TournamentTeam.objects.filter(tournament=tournament, is_deleted=False)
            self.fields['venue_record'].queryset = Venue.objects.filter(tenant=tournament.tenant, is_active=True, is_deleted=False)
            self.fields['ground_record'].queryset = Ground.objects.filter(venue__tenant=tournament.tenant, is_active=True, is_deleted=False)

        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.FileInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})

    def clean(self):
        cleaned_data = super().clean()
        home_team = cleaned_data.get('home_team')
        away_team = cleaned_data.get('away_team')
        match_date = cleaned_data.get('match_date')
        venue = cleaned_data.get('venue_record')
        ground = cleaned_data.get('ground_record')

        if home_team and away_team and home_team == away_team:
            raise ValidationError('Home team and away team must be different.')

        for field_name, tournament_team in [('home_team', home_team), ('away_team', away_team)]:
            if self.tournament and tournament_team and tournament_team.tournament_id != self.tournament.id:
                self.add_error(field_name, 'Selected team does not belong to this tournament.')
        if venue and ground and ground.venue_id != venue.id:
            self.add_error('ground_record', 'Selected ground does not belong to the selected venue.')
        if match_date:
            conflicts = TournamentMatch.objects.filter(match_date=match_date, is_deleted=False)
            if self.instance.pk:
                conflicts = conflicts.exclude(pk=self.instance.pk)
            if venue and conflicts.filter(venue_record=venue).exists():
                self.add_error('match_date', 'This venue already has a match at the selected time.')
            if home_team and conflicts.filter(Q(home_team=home_team) | Q(away_team=home_team)).exists():
                self.add_error('home_team', 'Home team already has a match at this time.')
            if away_team and conflicts.filter(Q(home_team=away_team) | Q(away_team=away_team)).exists():
                self.add_error('away_team', 'Away team already has a match at this time.')

        return cleaned_data


class TournamentSponsorForm(forms.ModelForm):
    class Meta:
        model = TournamentSponsor
        fields = ['name', 'sponsorship_level', 'amount', 'website', 'logo', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.FileInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control'})


class TournamentAwardForm(forms.ModelForm):
    class Meta:
        model = TournamentAward
        fields = ['name', 'winner', 'prize_amount', 'criteria']

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

        if tenant:
            self.fields['winner'].queryset = PlayerProfile.objects.filter(tenant=tenant, is_deleted=False)

        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.FileInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})


class TournamentOfficialForm(forms.ModelForm):
    class Meta:
        model = TournamentOfficial
        fields = ['official', 'role', 'is_chief_official']

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

        if tenant:
            self.fields['official'].queryset = PlayerProfile.objects.filter(tenant=tenant, is_deleted=False)

        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.FileInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})


class TournamentRuleForm(forms.ModelForm):
    class Meta:
        model = TournamentRule
        exclude = ['tournament', 'created_by', 'updated_by', 'status', 'is_deleted', 'deleted_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-check-input' if isinstance(field.widget, forms.CheckboxInput) else 'form-control'})

    def clean(self):
        data = super().clean()
        overs = data.get('overs_per_innings') or 0
        bowler_overs = data.get('max_overs_per_bowler') or 0
        powerplay = data.get('powerplay_overs') or 0
        if bowler_overs > overs:
            self.add_error('max_overs_per_bowler', 'Bowler limit cannot exceed innings overs.')
        if powerplay > overs:
            self.add_error('powerplay_overs', 'Powerplay cannot exceed innings overs.')
        return data


class MatchSetupForm(forms.ModelForm):
    class Meta:
        model = MatchSetup
        fields = ['toss_winner', 'toss_decision']

    def __init__(self, *args, **kwargs):
        match = kwargs.pop('match')
        super().__init__(*args, **kwargs)
        self.fields['toss_winner'].queryset = TournamentTeam.objects.filter(
            pk__in=[match.home_team_id, match.away_team_id]
        )
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-select'})


class MatchPlayingXIForm(forms.Form):
    team = forms.ModelChoiceField(queryset=TournamentTeam.objects.none())
    players = forms.ModelMultipleChoiceField(
        queryset=PlayerProfile.objects.none(),
        widget=forms.CheckboxSelectMultiple,
    )
    captain = forms.ModelChoiceField(queryset=PlayerProfile.objects.none())
    wicket_keeper = forms.ModelChoiceField(queryset=PlayerProfile.objects.none())

    def __init__(self, *args, **kwargs):
        match = kwargs.pop('match')
        super().__init__(*args, **kwargs)
        teams = TournamentTeam.objects.filter(pk__in=[match.home_team_id, match.away_team_id])
        players = PlayerProfile.objects.filter(
            tournaments_tournamentplayer_registrations__tournament_team__in=teams,
            tournaments_tournamentplayer_registrations__is_playing=True,
            is_deleted=False,
        ).distinct()
        self.fields['team'].queryset = teams
        self.fields['players'].queryset = players
        self.fields['captain'].queryset = players
        self.fields['wicket_keeper'].queryset = players
        for name in ('team', 'captain', 'wicket_keeper'):
            self.fields[name].widget.attrs.update({'class': 'form-select'})

    def clean(self):
        data = super().clean()
        team = data.get('team')
        players = data.get('players')
        rules = getattr(team.tournament, 'rules', None) if team else None
        required = rules.players_per_side if rules else 11
        if players is not None and players.count() != required:
            self.add_error('players', f'Select exactly {required} players.')
        if team and players is not None:
            valid_ids = set(TournamentPlayer.objects.filter(
                tournament_team=team,
                is_playing=True,
                is_deleted=False,
            ).values_list('player_id', flat=True))
            invalid = [player for player in players if player.pk not in valid_ids]
            if invalid:
                self.add_error('players', 'Every selected player must belong to the selected team squad.')
        if players is not None:
            for field in ('captain', 'wicket_keeper'):
                player = data.get(field)
                if player and player not in players:
                    self.add_error(field, f'{field.replace("_", " ").title()} must be in the playing XI.')
        return data


class MatchOfficialAssignmentForm(forms.ModelForm):
    class Meta:
        model = MatchOfficialAssignment
        fields = ['tournament_official', 'duty']

    def __init__(self, *args, **kwargs):
        match = kwargs.pop('match')
        super().__init__(*args, **kwargs)
        self.fields['tournament_official'].queryset = TournamentOfficial.objects.filter(
            tournament=match.tournament,
            is_deleted=False,
        )
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-select'})


class FixtureGeneratorForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    first_match_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}))
    matches_per_day = forms.IntegerField(min_value=1, max_value=4, initial=2, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    days_between_rounds = forms.IntegerField(min_value=1, max_value=14, initial=1, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    slot_gap_minutes = forms.IntegerField(min_value=60, max_value=600, initial=240, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    venue = forms.ModelChoiceField(queryset=Venue.objects.none(), widget=forms.Select(attrs={'class': 'form-select'}))

    def __init__(self, *args, **kwargs):
        tournament = kwargs.pop('tournament')
        super().__init__(*args, **kwargs)
        self.fields['venue'].queryset = Venue.objects.filter(
            tenant=tournament.tenant, is_active=True, is_deleted=False
        )
