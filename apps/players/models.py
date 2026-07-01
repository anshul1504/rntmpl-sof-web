"""
Player Ecosystem Models for the Cricket Ecosystem Platform.
Includes player profiles, skills, contracts, injuries, achievements, and transfers.
"""
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

from apps.common.models import (
    BaseModel,
    NamedModel,
    AddressMixin,
    ContactMixin,
    NoteMixin,
    EffectiveDateMixin,
    ApprovalMixin,
)


# ──────────────────────────────────────────────
# Enums / Choices
# ──────────────────────────────────────────────

class PlayerRole(models.TextChoices):
    """Cricket playing roles."""
    BATTER = 'BATTER', 'Batter'
    BOWLER = 'BOWLER', 'Bowler'
    ALL_ROUNDER = 'ALL_ROUNDER', 'All Rounder'
    WICKET_KEEPER = 'WICKET_KEEPER', 'Wicket Keeper'
    BATTER_WK = 'BATTER_WK', 'Batter & Wicket Keeper'
    BOWLING_ALL_ROUNDER = 'BOWLING_AR', 'Bowling All Rounder'
    BATTING_ALL_ROUNDER = 'BATTING_AR', 'Batting All Rounder'


class BattingStyle(models.TextChoices):
    RIGHT_HAND = 'RIGHT_HAND', 'Right Handed'
    LEFT_HAND = 'LEFT_HAND', 'Left Handed'


class BowlingStyle(models.TextChoices):
    RIGHT_ARM_FAST = 'RA_FAST', 'Right Arm Fast'
    RIGHT_ARM_FAST_MEDIUM = 'RA_FAST_MEDIUM', 'Right Arm Fast Medium'
    RIGHT_ARM_MEDIUM = 'RA_MEDIUM', 'Right Arm Medium'
    RIGHT_ARM_OFF_BREAK = 'RA_OFF_BREAK', 'Right Arm Off Break'
    RIGHT_ARM_LEG_BREAK = 'RA_LEG_BREAK', 'Right Arm Leg Break'
    LEFT_ARM_FAST = 'LA_FAST', 'Left Arm Fast'
    LEFT_ARM_FAST_MEDIUM = 'LA_FAST_MEDIUM', 'Left Arm Fast Medium'
    LEFT_ARM_MEDIUM = 'LA_MEDIUM', 'Left Arm Medium'
    LEFT_ARM_ORTHODOX = 'LA_ORTHODOX', 'Left Arm Orthodox'
    LEFT_ARM_CHINAMAN = 'LA_CHINAMAN', 'Left Arm Chinaman'
    SLOW_LEFT_ARM = 'SLOW_LA', 'Slow Left Arm'


class ContractType(models.TextChoices):
    FULL_TIME = 'FULL_TIME', 'Full Time'
    PART_TIME = 'PART_TIME', 'Part Time'
    TRIAL = 'TRIAL', 'Trial'
    ACADEMY = 'ACADEMY', 'Academy'
    SEASONAL = 'SEASONAL', 'Seasonal'
    MATCH_BASIS = 'MATCH_BASIS', 'Match Basis'


class InjurySeverity(models.TextChoices):
    MINOR = 'MINOR', 'Minor'
    MODERATE = 'MODERATE', 'Moderate'
    SEVERE = 'SEVERE', 'Severe'
    CRITICAL = 'CRITICAL', 'Critical'


class AchievementType(models.TextChoices):
    MAN_OF_MATCH = 'MAN_OF_MATCH', 'Man of the Match'
    MAN_OF_SERIES = 'MAN_OF_SERIES', 'Man of the Series'
    BEST_BATSMAN = 'BEST_BATSMAN', 'Best Batsman'
    BEST_BOWLER = 'BEST_BOWLER', 'Best Bowler'
    BEST_FIELDER = 'BEST_FIELDER', 'Best Fielder'
    CENTURY = 'CENTURY', 'Century'
    HALF_CENTURY = 'HALF_CENTURY', 'Half Century'
    FIVE_WICKETS = 'FIVE_WICKETS', 'Five Wicket Haul'
    HAT_TRICK = 'HAT_TRICK', 'Hat Trick'
    HIGH_SCORE = 'HIGH_SCORE', 'Highest Score'
    BEST_BOWLING_FIGURES = 'BEST_BOWLING', 'Best Bowling Figures'
    SPECIAL_ACHIEVEMENT = 'SPECIAL', 'Special Achievement'


class PlayerStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    INACTIVE = 'INACTIVE', 'Inactive'
    INJURED = 'INJURED', 'Injured'
    RETIRED = 'RETIRED', 'Retired'
    SUSPENDED = 'SUSPENDED', 'Suspended'
    BANNED = 'BANNED', 'Banned'
    DECEASED = 'DECEASED', 'Deceased'


# ──────────────────────────────────────────────
# Models
# ──────────────────────────────────────────────

class PlayerProfile(BaseModel, AddressMixin, ContactMixin):
    """
    Main player profile storing personal, contact, and cricket-specific information.
    Each player belongs to a team via contracts (not a direct FK so a player can have
    multiple team associations over time).
    """
    # Personal Information
    tenant = models.ForeignKey(
        'accounts.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='players',
        db_index=True,
        help_text='Tenant that owns this player profile.',
    )
    first_name = models.CharField(max_length=100, db_index=True)
    last_name = models.CharField(max_length=100, blank=True, default='', db_index=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[('MALE', 'Male'), ('FEMALE', 'Female'), ('OTHER', 'Other')],
        default='MALE',
    )
    nationality = models.CharField(max_length=100, blank=True, default='India')
    photo = models.ImageField(upload_to='players/photos/', blank=True, null=True)

    # Cricket-specific
    role = models.CharField(
        max_length=20,
        choices=PlayerRole.choices,
        default=PlayerRole.BATTER,
        db_index=True,
    )
    batting_style = models.CharField(
        max_length=20,
        choices=BattingStyle.choices,
        default=BattingStyle.RIGHT_HAND,
    )
    bowling_style = models.CharField(
        max_length=30,
        choices=BowlingStyle.choices,
        blank=True,
        default='',
    )
    is_bowler = models.BooleanField(default=False)
    is_wicket_keeper = models.BooleanField(default=False)
    jersey_number = models.PositiveIntegerField(null=True, blank=True)

    # Physical attributes
    height_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)

    # Career info
    debut_date = models.DateField(null=True, blank=True)
    player_status = models.CharField(
        max_length=20,
        choices=PlayerStatus.choices,
        default=PlayerStatus.ACTIVE,
        db_index=True,
    )
    retirement_date = models.DateField(null=True, blank=True)
    is_retired = models.BooleanField(default=False, db_index=True)

    # Meta
    notes = models.TextField(blank=True, default='')
    biography = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'players_profile'
        verbose_name = 'Player Profile'
        verbose_name_plural = 'Player Profiles'
        ordering = ['first_name', 'last_name']
        indexes = [
            models.Index(fields=['tenant', 'player_status']),
            models.Index(fields=['first_name', 'last_name']),
            models.Index(fields=['role', 'player_status']),
        ]

    def __str__(self):
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    @property
    def full_name(self):
        return str(self)

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )


class PlayerBattingSkill(BaseModel):
    """
    Batting skills and ratings for a player.
    Allows storing historical skill assessments.
    """
    player = models.ForeignKey(
        PlayerProfile,
        on_delete=models.CASCADE,
        related_name='batting_skills',
    )
    assessed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_assessments',
    )

    # Batting attributes (1-100 scale)
    technique = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    attacking_play = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    defensive_play = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    footwork = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    timing = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    shot_selection = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    running_between_wickets = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    spin_playing_ability = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    pace_playing_ability = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )

    # Assessment period
    assessment_date = models.DateField(default=timezone.now)
    valid_from = models.DateField(default=timezone.now)
    valid_to = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'players_batting_skill'
        verbose_name = 'Player Batting Skill'
        verbose_name_plural = 'Player Batting Skills'
        ordering = ['-assessment_date']

    def __str__(self):
        return f"{self.player} batting skill ({self.assessment_date})"

    @property
    def overall_rating(self):
        """Calculate average batting rating."""
        fields = [
            self.technique, self.attacking_play, self.defensive_play,
            self.footwork, self.timing, self.shot_selection,
            self.running_between_wickets, self.spin_playing_ability,
            self.pace_playing_ability,
        ]
        return sum(fields) / len(fields)


class PlayerBowlingSkill(BaseModel):
    """
    Bowling skills and ratings for a player.
    """
    player = models.ForeignKey(
        PlayerProfile,
        on_delete=models.CASCADE,
        related_name='bowling_skills',
    )
    assessed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_bowling_assessments',
    )

    # Bowling attributes (1-100 scale)
    pace_or_speed = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    accuracy = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    swing = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    seam_movement = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    spin = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    yorker_ability = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    bouncer_ability = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    slower_ball_variation = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    googly_doosra = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    death_bowling = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    field_placement_intelligence = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )

    assessment_date = models.DateField(default=timezone.now)
    valid_from = models.DateField(default=timezone.now)
    valid_to = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'players_bowling_skill'
        verbose_name = 'Player Bowling Skill'
        verbose_name_plural = 'Player Bowling Skills'
        ordering = ['-assessment_date']

    def __str__(self):
        return f"{self.player} bowling skill ({self.assessment_date})"

    @property
    def overall_rating(self):
        fields = [
            self.pace_or_speed, self.accuracy, self.swing, self.seam_movement,
            self.spin, self.yorker_ability, self.bouncer_ability,
            self.slower_ball_variation, self.googly_doosra, self.death_bowling,
            self.field_placement_intelligence,
        ]
        return sum(fields) / len(fields)


class PlayerFieldingSkill(BaseModel):
    """Fielding skills for a player."""
    player = models.ForeignKey(
        PlayerProfile,
        on_delete=models.CASCADE,
        related_name='fielding_skills',
    )
    assessed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_fielding_assessments',
    )

    # Fielding attributes (1-100)
    catching = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    throwing = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    ground_fielding = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    agility = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    wicket_keeping = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    assessment_date = models.DateField(default=timezone.now)
    valid_from = models.DateField(default=timezone.now)
    valid_to = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'players_fielding_skill'
        verbose_name = 'Player Fielding Skill'
        verbose_name_plural = 'Player Fielding Skills'
        ordering = ['-assessment_date']

    def __str__(self):
        return f"{self.player} fielding skill ({self.assessment_date})"

    @property
    def overall_rating(self):
        fields = [self.catching, self.throwing, self.ground_fielding, self.agility]
        if self.player.is_wicket_keeper:
            fields.append(self.wicket_keeping)
        return sum(fields) / len(fields)


class PlayerContract(BaseModel, EffectiveDateMixin, ApprovalMixin):
    """
    Player contract linking a player to a team for a specific period.
    A player can have multiple contracts over time but only one active at a time.
    """
    player = models.ForeignKey(
        PlayerProfile,
        on_delete=models.CASCADE,
        related_name='contracts',
    )
    team = models.ForeignKey(
        'teams.Team',
        on_delete=models.CASCADE,
        related_name='player_contracts',
    )
    contract_type = models.CharField(
        max_length=20,
        choices=ContractType.choices,
        default=ContractType.FULL_TIME,
    )
    contract_number = models.CharField(max_length=50, unique=True, db_index=True)
    signing_date = models.DateField(default=timezone.now)
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    # Financial details
    annual_salary = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    signing_bonus = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    match_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    performance_bonus = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    # Terms
    no_of_matches = models.PositiveIntegerField(null=True, blank=True)
    termination_clause = models.TextField(blank=True, default='')
    special_terms = models.TextField(blank=True, default='')
    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'players_contract'
        verbose_name = 'Player Contract'
        verbose_name_plural = 'Player Contracts'
        ordering = ['-signing_date']
        indexes = [
            models.Index(fields=['player', 'is_active']),
            models.Index(fields=['team', 'is_active']),
            models.Index(fields=['contract_type', 'is_active']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['player', 'is_active'],
                condition=models.Q(is_active=True),
                name='unique_active_player_contract',
            ),
        ]

    def __str__(self):
        return f"{self.player} → {self.team} ({self.get_contract_type_display()})"


class PlayerTransfer(BaseModel, ApprovalMixin):
    """Records transfer of a player between teams."""
    player = models.ForeignKey(
        PlayerProfile,
        on_delete=models.CASCADE,
        related_name='transfers',
    )
    from_team = models.ForeignKey(
        'teams.Team',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transferred_out_players',
    )
    to_team = models.ForeignKey(
        'teams.Team',
        on_delete=models.CASCADE,
        related_name='transferred_in_players',
    )
    transfer_date = models.DateField(default=timezone.now)
    transfer_type = models.CharField(
        max_length=20,
        choices=[
            ('PERMANENT', 'Permanent'),
            ('LOAN', 'Loan'),
            ('FREE_AGENT', 'Free Agent'),
            ('AUCTION', 'Auction'),
            ('RELEASE', 'Release'),
        ],
        default='PERMANENT',
    )
    transfer_fee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    loan_start_date = models.DateField(null=True, blank=True)
    loan_end_date = models.DateField(null=True, blank=True)
    contract_at_transfer = models.ForeignKey(
        PlayerContract,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transfers_from_contract',
    )
    reason = models.TextField(blank=True, default='')
    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'players_transfer'
        verbose_name = 'Player Transfer'
        verbose_name_plural = 'Player Transfers'
        ordering = ['-transfer_date']
        indexes = [
            models.Index(fields=['player', 'transfer_date']),
            models.Index(fields=['from_team', 'to_team']),
            models.Index(fields=['transfer_type']),
        ]

    def __str__(self):
        from_team_name = str(self.from_team) if self.from_team else 'Free Agent'
        return f"{self.player}: {from_team_name} → {self.to_team} ({self.transfer_date})"


class PlayerInjury(BaseModel):
    """Records injuries sustained by a player."""
    player = models.ForeignKey(
        PlayerProfile,
        on_delete=models.CASCADE,
        related_name='injuries',
    )
    injury_type = models.CharField(max_length=100, db_index=True)
    severity = models.CharField(
        max_length=20,
        choices=InjurySeverity.choices,
        default=InjurySeverity.MODERATE,
    )
    body_part = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    injury_date = models.DateField(db_index=True)
    expected_recovery_date = models.DateField(null=True, blank=True)
    actual_recovery_date = models.DateField(null=True, blank=True)
    is_recovered = models.BooleanField(default=False, db_index=True)
    treated_by = models.CharField(max_length=255, blank=True, default='')
    treatment_notes = models.TextField(blank=True, default='')
    follow_up_required = models.BooleanField(default=False)

    class Meta:
        db_table = 'players_injury'
        verbose_name = 'Player Injury'
        verbose_name_plural = 'Player Injuries'
        ordering = ['-injury_date']
        indexes = [
            models.Index(fields=['player', 'is_recovered']),
            models.Index(fields=['injury_type', 'severity']),
        ]

    def __str__(self):
        return f"{self.player} - {self.injury_type} ({self.injury_date})"


class PlayerAchievement(BaseModel):
    """Records achievements and awards won by a player."""
    player = models.ForeignKey(
        PlayerProfile,
        on_delete=models.CASCADE,
        related_name='achievements',
    )
    achievement_type = models.CharField(
        max_length=30,
        choices=AchievementType.choices,
        db_index=True,
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    achieved_date = models.DateField(db_index=True)
    tournament = models.ForeignKey(
        'tournaments.Tournament',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='player_achievements',
    )
    match = models.ForeignKey(
        'tournaments.TournamentMatch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='player_achievements',
    )
    team_at_time = models.ForeignKey(
        'teams.Team',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='player_achievements',
    )
    is_career_achievement = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'players_achievement'
        verbose_name = 'Player Achievement'
        verbose_name_plural = 'Player Achievements'
        ordering = ['-achieved_date']
        indexes = [
            models.Index(fields=['player', 'achievement_type']),
            models.Index(fields=['achieved_date']),
        ]

    def __str__(self):
        return f"{self.player} - {self.title} ({self.achieved_date})"


class PlayerCareerStats(BaseModel):
    """
    Aggregate career statistics for a player.
    Updated periodically (e.g., after each match or series).
    Stored as a separate model for quick lookup rather than computing on the fly.
    """
    player = models.OneToOneField(
        PlayerProfile,
        on_delete=models.CASCADE,
        related_name='career_stats',
    )

    # Batting stats
    matches_played = models.PositiveIntegerField(default=0)
    innings_batted = models.PositiveIntegerField(default=0)
    not_outs = models.PositiveIntegerField(default=0)
    runs_scored = models.PositiveIntegerField(default=0)
    balls_faced = models.PositiveIntegerField(default=0)
    highest_score = models.PositiveIntegerField(default=0)
    hundreds = models.PositiveIntegerField(default=0)
    fifties = models.PositiveIntegerField(default=0)
    ducks = models.PositiveIntegerField(default=0)
    fours = models.PositiveIntegerField(default=0)
    sixes = models.PositiveIntegerField(default=0)
    batting_average = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    strike_rate = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))

    # Bowling stats
    balls_bowled = models.PositiveIntegerField(default=0)
    runs_conceded = models.PositiveIntegerField(default=0)
    wickets_taken = models.PositiveIntegerField(default=0)
    best_bowling_wickets = models.PositiveIntegerField(default=0)
    best_bowling_runs = models.PositiveIntegerField(default=0)
    five_wicket_hauls = models.PositiveIntegerField(default=0)
    ten_wicket_hauls = models.PositiveIntegerField(default=0)
    bowling_average = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    economy_rate = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    bowling_strike_rate = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))

    # Fielding stats
    catches = models.PositiveIntegerField(default=0)
    stumpings = models.PositiveIntegerField(default=0)
    run_outs = models.PositiveIntegerField(default=0)

    # Meta
    last_updated = models.DateTimeField(auto_now=True)
    format = models.CharField(
        max_length=10,
        choices=[
            ('TEST', 'Test'),
            ('ODI', 'ODI'),
            ('T20', 'T20'),
            ('ALL', 'All Formats'),
        ],
        default='ALL',
        db_index=True,
    )

    class Meta:
        db_table = 'players_career_stats'
        verbose_name = 'Player Career Stats'
        verbose_name_plural = 'Player Career Stats'
        indexes = [
            models.Index(fields=['runs_scored', 'wickets_taken']),
            models.Index(fields=['batting_average', 'bowling_average']),
        ]

    def __str__(self):
        return f"Career Stats: {self.player} ({self.get_format_display()})"
