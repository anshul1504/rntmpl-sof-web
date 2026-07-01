"""
Team models for the Cricket Ecosystem Platform.
Handles team registration, team management, team statistics, and related entities.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.common.models import (
    BaseModel,
    NamedModel,
    CodedNamedModel,
    AddressMixin,
    ContactMixin,
    YearMixin,
    SeasonMixin,
    EffectiveDateMixin,
    generate_uuid,
)


class TeamCategory(NamedModel):
    """
    Category of team (e.g., Senior, Junior, U19, U16, Women's, etc.).
    """
    class Meta:
        db_table = 'teams_team_category'
        verbose_name_plural = 'Team Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class TeamType(NamedModel):
    """
    Type of team (e.g., Club, School, College, State, National, Franchise, Academy).
    """
    class Meta:
        db_table = 'teams_team_type'
        verbose_name_plural = 'Team Types'
        ordering = ['name']

    def __str__(self):
        return self.name


class Team(NamedModel, AddressMixin, ContactMixin, YearMixin):
    """
    Core team model representing a cricket team.
    Each team belongs to a category and type.
    """
    tenant = models.ForeignKey(
        'accounts.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='teams',
        db_index=True,
        help_text='Tenant that owns this team.',
    )
    code = models.CharField(max_length=50, unique=True, db_index=True)
    team_category = models.ForeignKey(
        TeamCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_teams',
    )
    team_type = models.ForeignKey(
        TeamType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_teams',
    )
    short_name = models.CharField(max_length=10, blank=True, default='')
    abbreviation = models.CharField(max_length=5, blank=True, default='')
    logo = models.ImageField(upload_to='teams/logos/', blank=True, null=True)
    jersey_color_primary = models.CharField(max_length=7, blank=True, default='')  # Hex color
    jersey_color_secondary = models.CharField(max_length=7, blank=True, default='')  # Hex color
    home_ground = models.CharField(max_length=255, blank=True, default='')
    founded_date = models.DateField(null=True, blank=True)
    website = models.URLField(blank=True, default='')
    social_media_links = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = 'teams_team'
        verbose_name_plural = 'Teams'
        ordering = ['name']
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.short_name})" if self.short_name else self.name


class TeamSeason(BaseModel, SeasonMixin):
    """
    Links a team to a specific season/year.
    Tracks season-specific information like captain, coach, squad size, etc.
    """
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='%(class)s_seasons',
    )
    year = models.PositiveIntegerField(
        db_index=True,
        validators=[MinValueValidator(2000), MaxValueValidator(2100)],
    )
    team_name = models.CharField(max_length=255, blank=True, default='')  # Season-specific team name
    captain = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_captain_for',
    )
    vice_captain = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_vice_captain_for',
    )
    coach = models.CharField(max_length=255, blank=True, default='')
    assistant_coach = models.CharField(max_length=255, blank=True, default='')
    manager = models.CharField(max_length=255, blank=True, default='')
    squad_size = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = 'teams_team_season'
        verbose_name_plural = 'Team Seasons'
        unique_together = ['team', 'year', 'season']
        ordering = ['-year', 'team__name']

    def __str__(self):
        return f"{self.team.name} - {self.get_season_display()} {self.year}"


class TeamSquad(BaseModel):
    """
    Individual player registration for a specific team season.
    Tracks player role, jersey number, and joining/leaving dates.
    """
    team_season = models.ForeignKey(
        TeamSeason,
        on_delete=models.CASCADE,
        related_name='%(class)s_players',
    )
    player = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.CASCADE,
        related_name='%(class)s_team_seasons',
    )
    jersey_number = models.PositiveIntegerField(null=True, blank=True)
    role = models.CharField(max_length=50, blank=True, default='')  # e.g., Batsman, Bowler, All-rounder, WK
    batting_order = models.PositiveIntegerField(null=True, blank=True)
    bowling_style = models.CharField(max_length=100, blank=True, default='')
    batting_style = models.CharField(max_length=100, blank=True, default='')
    is_captain = models.BooleanField(default=False)
    is_vice_captain = models.BooleanField(default=False)
    is_wicket_keeper = models.BooleanField(default=False)
    joined_date = models.DateField(null=True, blank=True)
    left_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    contract_details = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'teams_team_squad'
        verbose_name_plural = 'Team Squads'
        unique_together = ['team_season', 'player']
        ordering = ['team_season', 'batting_order', 'jersey_number']

    def __str__(self):
        return f"{self.player} - {self.team_season}"


class TeamStaff(BaseModel):
    """
    Staff members associated with a team season (coaches, physios, analysts, etc.).
    """
    team_season = models.ForeignKey(
        TeamSeason,
        on_delete=models.CASCADE,
        related_name='%(class)s_members',
    )
    staff_type = models.CharField(
        max_length=50,
        db_index=True,
        choices=[
            ('HEAD_COACH', 'Head Coach'),
            ('ASSISTANT_COACH', 'Assistant Coach'),
            ('BOWLING_COACH', 'Bowling Coach'),
            ('BATTING_COACH', 'Batting Coach'),
            ('FIELDING_COACH', 'Fielding Coach'),
            ('PHYSIOTHERAPIST', 'Physiotherapist'),
            ('TRAINER', 'Trainer'),
            ('DATA_ANALYST', 'Data Analyst'),
            ('VIDEO_ANALYST', 'Video Analyst'),
            ('TEAM_MANAGER', 'Team Manager'),
            ('MEDICAL_OFFICER', 'Medical Officer'),
            ('MASSAGE_THERAPIST', 'Massage Therapist'),
            ('PSYCHOLOGIST', 'Psychologist'),
            ('OTHER', 'Other'),
        ],
    )
    name = models.CharField(max_length=255)
    contact_phone = models.CharField(max_length=20, blank=True, default='')
    contact_email = models.EmailField(blank=True, default='')
    qualifications = models.TextField(blank=True, default='')
    experience_years = models.PositiveIntegerField(default=0)
    joined_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'teams_team_staff'
        verbose_name_plural = 'Team Staff Members'
        ordering = ['team_season', 'staff_type', 'name']

    def __str__(self):
        return f"{self.get_staff_type_display()} - {self.name} ({self.team_season})"


class TeamStat(BaseModel):
    """
    Statistical records for a team across different contexts (matches, tournaments, seasons).
    """
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='%(class)s_stats',
    )
    team_season = models.ForeignKey(
        TeamSeason,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_stats',
    )
    tournament = models.ForeignKey(
        'tournaments.Tournament',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_team_stats',
    )
    context = models.CharField(
        max_length=50,
        db_index=True,
        choices=[
            ('OVERALL', 'Overall'),
            ('SEASON', 'Season'),
            ('TOURNAMENT', 'Tournament'),
            ('HOME', 'Home'),
            ('AWAY', 'Away'),
            ('LAST_10', 'Last 10 Matches'),
            ('LAST_20', 'Last 20 Matches'),
            ('CUSTOM', 'Custom'),
        ],
        default='OVERALL',
    )

    # Match counts
    matches_played = models.PositiveIntegerField(default=0)
    matches_won = models.PositiveIntegerField(default=0)
    matches_lost = models.PositiveIntegerField(default=0)
    matches_tied = models.PositiveIntegerField(default=0)
    matches_drawn = models.PositiveIntegerField(default=0)
    matches_no_result = models.PositiveIntegerField(default=0)
    win_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    # Batting stats
    total_runs = models.PositiveIntegerField(default=0)
    total_balls_faced = models.PositiveIntegerField(default=0)
    highest_total = models.PositiveIntegerField(default=0)
    lowest_total = models.PositiveIntegerField(default=0)
    centuries = models.PositiveIntegerField(default=0)
    half_centuries = models.PositiveIntegerField(default=0)
    fours = models.PositiveIntegerField(default=0)
    sixes = models.PositiveIntegerField(default=0)
    run_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    # Bowling stats
    total_balls_bowled = models.PositiveIntegerField(default=0)
    total_runs_conceded = models.PositiveIntegerField(default=0)
    total_wickets = models.PositiveIntegerField(default=0)
    economy_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    bowling_average = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    best_bowling_figures = models.CharField(max_length=20, blank=True, default='')  # e.g., "5/25"
    five_wicket_hauls = models.PositiveIntegerField(default=0)

    # Fielding stats
    catches = models.PositiveIntegerField(default=0)
    stumpings = models.PositiveIntegerField(default=0)
    run_outs = models.PositiveIntegerField(default=0)

    # Streak info
    current_win_streak = models.PositiveIntegerField(default=0)
    current_loss_streak = models.PositiveIntegerField(default=0)
    longest_win_streak = models.PositiveIntegerField(default=0)
    longest_loss_streak = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'teams_team_stat'
        verbose_name_plural = 'Team Statistics'
        unique_together = ['team', 'team_season', 'tournament', 'context']
        ordering = ['team', '-matches_played']

    def __str__(self):
        return f"Stats: {self.team.name} - {self.get_context_display()} (W:{self.matches_won}/L:{self.matches_lost})"


class TeamRanking(BaseModel):
    """
    Ranking information for teams across different formats.
    """
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='%(class)s_rankings',
    )
    format = models.CharField(
        max_length=20,
        db_index=True,
        choices=[
            ('TEST', 'Test'),
            ('ODI', 'One Day International'),
            ('T20', 'Twenty20'),
            ('T10', 'Ten10'),
            ('THE_HUNDRED', 'The Hundred'),
            ('LIST_A', 'List A'),
            ('FIRST_CLASS', 'First Class'),
            ('CLUB', 'Club'),
            ('OTHER', 'Other'),
        ],
    )
    rank = models.PositiveIntegerField(db_index=True)
    previous_rank = models.PositiveIntegerField(null=True, blank=True)
    points = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    rating = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    ranking_date = models.DateField(auto_now_add=True)
    source = models.CharField(max_length=100, blank=True, default='')

    class Meta:
        db_table = 'teams_team_ranking'
        verbose_name_plural = 'Team Rankings'
        unique_together = ['team', 'format', 'ranking_date']
        ordering = ['format', 'rank']

    def __str__(self):
        return f"{self.team.name} - #{self.rank} ({self.get_format_display()})"


class TeamSponsorship(BaseModel, EffectiveDateMixin):
    """
    Sponsorship records for teams.
    """
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='%(class)s_sponsorships',
    )
    sponsor_name = models.CharField(max_length=255)
    sponsor_logo = models.ImageField(upload_to='teams/sponsors/', blank=True, null=True)
    sponsorship_type = models.CharField(
        max_length=50,
        choices=[
            ('TITLE', 'Title Sponsor'),
            ('KIT', 'Kit Sponsor'),
            ('PRINCIPAL', 'Principal Sponsor'),
            ('ASSOCIATE', 'Associate Sponsor'),
            ('GROUND', 'Ground Sponsor'),
            ('BROADCAST', 'Broadcast Partner'),
            ('DIGITAL', 'Digital Partner'),
            ('OFFICIAL', 'Official Partner'),
            ('OTHER', 'Other'),
        ],
    )
    contract_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='INR')
    is_active = models.BooleanField(default=True, db_index=True)
    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'teams_team_sponsorship'
        verbose_name_plural = 'Team Sponsorships'
        ordering = ['team', '-effective_from']

    def __str__(self):
        return f"{self.sponsor_name} - {self.team.name} ({self.get_sponsorship_type_display()})"


class TeamAchievement(NamedModel):
    """
    Achievements and honors won by a team.
    """
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='%(class)s_achievements',
    )
    achievement_date = models.DateField()
    achievement_type = models.CharField(
        max_length=50,
        db_index=True,
        choices=[
            ('CHAMPIONSHIP', 'Championship Winner'),
            ('RUNNER_UP', 'Runner Up'),
            ('SEMI_FINALIST', 'Semi Finalist'),
            ('QUARTER_FINALIST', 'Quarter Finalist'),
            ('PROMOTION', 'Promotion'),
            ('QUALIFICATION', 'Tournament Qualification'),
            ('RECORD', 'Record Achievement'),
            ('AWARD', 'Award'),
            ('OTHER', 'Other'),
        ],
    )
    tournament = models.ForeignKey(
        'tournaments.Tournament',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_team_achievements',
    )
    season = models.CharField(max_length=50, blank=True, default='')
    description = models.TextField(blank=True, default='')
    image = models.ImageField(upload_to='teams/achievements/', blank=True, null=True)

    class Meta:
        db_table = 'teams_team_achievement'
        verbose_name_plural = 'Team Achievements'
        ordering = ['-achievement_date']

    def __str__(self):
        return f"{self.team.name} - {self.get_achievement_type_display()} ({self.achievement_date.year})"


class TeamTransfer(BaseModel):
    """
    Tracks player transfers between teams.
    """
    player = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.CASCADE,
        related_name='%(class)s_transfers',
    )
    from_team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_transfers_out',
    )
    to_team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_transfers_in',
    )
    transfer_date = models.DateField()
    transfer_type = models.CharField(
        max_length=50,
        choices=[
            ('TRANSFER', 'Transfer'),
            ('LOAN', 'Loan'),
            ('PERMANENT', 'Permanent Transfer'),
            ('FREE_AGENT', 'Free Agent Signing'),
            ('DRAFT', 'Draft Pick'),
            ('PROMOTION', 'Promotion from Academy'),
            ('RELEASE', 'Release'),
            ('RETIREMENT', 'Retirement'),
            ('RECALL', 'Recall from Loan'),
        ],
    )
    transfer_fee = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='INR')
    contract_duration_months = models.PositiveIntegerField(null=True, blank=True)
    season = models.CharField(max_length=50, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = 'teams_team_transfer'
        verbose_name_plural = 'Team Transfers'
        ordering = ['-transfer_date']

    def __str__(self):
        return f"{self.player} - {self.from_team} → {self.to_team} ({self.transfer_date})"


class TeamDocument(BaseModel):
    """
    Documents attached to a team (registration forms, agreements, etc.).
    """
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='%(class)s_documents',
    )
    document_type = models.CharField(
        max_length=50,
        db_index=True,
        choices=[
            ('REGISTRATION', 'Registration Document'),
            ('CONTRACT', 'Contract'),
            ('AGREEMENT', 'Agreement'),
            ('CERTIFICATE', 'Certificate'),
            ('LICENSE', 'License'),
            ('REPORT', 'Report'),
            ('IDENTITY', 'Identity Proof'),
            ('OTHER', 'Other'),
        ],
    )
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='teams/documents/')
    file_size = models.PositiveIntegerField(default=0)  # Size in bytes
    mime_type = models.CharField(max_length=100, blank=True, default='')
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_verified_documents',
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'teams_team_document'
        verbose_name_plural = 'Team Documents'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.team.name} - {self.get_document_type_display()}: {self.title}"
