"""
Live Scoring Models for the Cricket Ecosystem Platform.
Ball-by-ball tracking, innings, scorecards, commentary, and match state.
"""
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

from apps.common.models import BaseModel, TimestampMixin, NoteMixin


# ── Enums / Choices ─────────────────────────────────────────────────────

class InningStatus(models.TextChoices):
    UPCOMING = 'UPCOMING', 'Upcoming'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    COMPLETED = 'COMPLETED', 'Completed'
    DECLARED = 'DECLARED', 'Declared'
    FORFEITED = 'FORFEITED', 'Forfeited'


class BallType(models.TextChoices):
    NORMAL = 'NORMAL', 'Normal'
    WIDE = 'WIDE', 'Wide'
    NO_BALL = 'NO_BALL', 'No Ball'
    BYE = 'BYE', 'Bye'
    LEG_BYE = 'LEG_BYE', 'Leg Bye'
    PENALTY = 'PENALTY', 'Penalty'


class DismissalType(models.TextChoices):
    BOWLED = 'BOWLED', 'Bowled'
    CAUGHT = 'CAUGHT', 'Caught'
    LBW = 'LBW', 'LBW'
    RUN_OUT = 'RUN_OUT', 'Run Out'
    STUMPED = 'STUMPED', 'Stumped'
    HIT_WICKET = 'HIT_WICKET', 'Hit Wicket'
    RETIRED_HURT = 'RETIRED_HURT', 'Retired Hurt'
    RETIRED_OUT = 'RETIRED_OUT', 'Retired Out'
    OBSTRUCTING = 'OBSTRUCTING', 'Obstructing the Field'
    HANDLED_BALL = 'HANDLED_BALL', 'Handled the Ball'
    TIMED_OUT = 'TIMED_OUT', 'Timed Out'
    NOT_OUT = 'NOT_OUT', 'Not Out'


class ExtrasType(models.TextChoices):
    WIDE = 'WIDE', 'Wide'
    NO_BALL = 'NO_BALL', 'No Ball'
    BYE = 'BYE', 'Bye'
    LEG_BYE = 'LEG_BYE', 'Leg Bye'
    PENALTY = 'PENALTY', 'Penalty'


# ── Innings ─────────────────────────────────────────────────────────────

class Innings(BaseModel):
    """
    Represents a single innings of a match.
    Each match can have up to 4 innings (Test) or 2 (Limited Overs).
    """
    match = models.ForeignKey(
        'tournaments.TournamentMatch',
        on_delete=models.CASCADE,
        related_name='innings',
    )
    batting_team = models.ForeignKey(
        'tournaments.TournamentTeam',
        on_delete=models.CASCADE,
        related_name='batting_innings',
    )
    bowling_team = models.ForeignKey(
        'tournaments.TournamentTeam',
        on_delete=models.CASCADE,
        related_name='bowling_innings',
    )
    innings_number = models.PositiveIntegerField(
        default=1,
        help_text='1st innings, 2nd innings, etc.',
    )
    status = models.CharField(
        max_length=20,
        choices=InningStatus.choices,
        default=InningStatus.UPCOMING,
        db_index=True,
    )

    # Score
    total_runs = models.PositiveIntegerField(default=0)
    total_wickets = models.PositiveIntegerField(default=0)
    total_extras = models.PositiveIntegerField(default=0)
    total_overs_bowled = models.DecimalField(
        max_digits=5, decimal_places=1, default=0.0,
        help_text='Overs bowled in decimal format (e.g., 12.3 = 12.3 overs)',
    )
    total_legal_balls = models.PositiveIntegerField(
        default=0,
        help_text='Total legal deliveries bowled (excluding wides/noballs)',
    )
    total_balls_bowled = models.PositiveIntegerField(
        default=0,
        help_text='Total deliveries bowled (including wides/noballs)',
    )
    run_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    required_runs = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Runs needed to win (for 2nd innings)',
    )
    required_overs = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True,
        help_text='Overs remaining (for limited-overs chase)',
    )
    target_runs = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Target set for the opposing team',
    )
    is_declared = models.BooleanField(default=False)
    is_all_out = models.BooleanField(default=False)
    declared_at_wickets = models.PositiveIntegerField(null=True, blank=True)
    declared_at_runs = models.PositiveIntegerField(null=True, blank=True)
    powerplay_overs_remaining = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True, default='')

    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'scoring_innings'
        verbose_name = 'Innings'
        verbose_name_plural = 'Innings'
        ordering = ['match', 'innings_number']
        indexes = [
            models.Index(fields=['match', 'batting_team']),
            models.Index(fields=['match', 'status']),
        ]

    def __str__(self):
        return f"{self.match} - Innings #{self.innings_number} ({self.batting_team})"

    def calculate_run_rate(self):
        if self.total_overs_bowled > 0:
            self.run_rate = Decimal(str(self.total_runs)) / Decimal(str(self.total_overs_bowled))
        else:
            self.run_rate = Decimal('0.00')
        return self.run_rate

    def can_bat(self):
        """Check if the batting team can continue batting."""
        if self.total_wickets >= 10:
            return False
        if self.is_declared:
            return False
        return self.status == InningStatus.IN_PROGRESS


class Ball(BaseModel):
    """
    Ball-by-ball record of every delivery in a match.
    Tracks runs, wickets, extras, and metadata for each delivery.
    """
    innings = models.ForeignKey(
        Innings,
        on_delete=models.CASCADE,
        related_name='balls',
    )
    match = models.ForeignKey(
        'tournaments.TournamentMatch',
        on_delete=models.CASCADE,
        related_name='balls',
    )
    over_number = models.PositiveIntegerField(
        db_index=True,
        help_text='Over number (1-based)',
    )
    ball_number_in_over = models.PositiveIntegerField(
        help_text='Ball number within the over (1-6)',
    )
    ball_number_in_innings = models.PositiveIntegerField(
        db_index=True,
        help_text='Absolute ball number in the innings',
    )

    # Batter & Bowler
    bowler = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.CASCADE,
        related_name='balls_bowled',
    )
    striker = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.CASCADE,
        related_name='balls_faced',
    )
    non_striker = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.CASCADE,
        related_name='balls_at_non_striker',
    )

    # Runs scored on this ball
    runs_from_bat = models.PositiveIntegerField(default=0)
    runs_extras = models.PositiveIntegerField(default=0)
    total_runs_on_ball = models.PositiveIntegerField(default=0)

    # Ball type classification
    ball_type = models.CharField(
        max_length=20,
        choices=BallType.choices,
        default=BallType.NORMAL,
    )
    is_legal = models.BooleanField(default=True)
    is_boundary = models.BooleanField(default=False)
    is_six = models.BooleanField(default=False)
    is_dot_ball = models.BooleanField(default=False)
    is_maiden_ball = models.BooleanField(default=False)

    # Extras breakdown
    extras_type = models.CharField(
        max_length=20,
        choices=ExtrasType.choices,
        blank=True, default='',
    )
    extras_wide_runs = models.PositiveIntegerField(default=0)
    extras_no_ball_runs = models.PositiveIntegerField(default=0)
    extras_bye_runs = models.PositiveIntegerField(default=0)
    extras_leg_bye_runs = models.PositiveIntegerField(default=0)
    extras_penalty_runs = models.PositiveIntegerField(default=0)

    # Wicket
    is_wicket = models.BooleanField(default=False)
    dismissal_type = models.CharField(
        max_length=20,
        choices=DismissalType.choices,
        blank=True, default='',
    )
    dismissed_player = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='dismissals',
    )
    fielder_on_dismissal = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='dismissals_fielded',
    )
    bowler_on_dismissal = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='wickets_taken',
    )
    is_run_out_assist = models.BooleanField(default=False)

    # Commentary
    commentary = models.CharField(max_length=500, blank=True, default='')
    short_commentary = models.CharField(max_length=200, blank=True, default='')

    # Timing
    bowled_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = 'scoring_balls'
        verbose_name = 'Ball'
        verbose_name_plural = 'Balls'
        ordering = ['innings', 'ball_number_in_innings']
        indexes = [
            models.Index(fields=['innings', 'over_number', 'bowler']),
            models.Index(fields=['match', 'over_number']),
            models.Index(fields=['striker', 'innings']),
            models.Index(fields=['bowler', 'innings']),
            models.Index(fields=['is_wicket', 'innings']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['innings', 'over_number', 'ball_number_in_over'],
                name='unique_ball_in_over',
            ),
            models.UniqueConstraint(
                fields=['innings', 'ball_number_in_innings'],
                name='unique_ball_in_innings',
            ),
        ]

    def __str__(self):
        return f"{self.innings} - Over {self.over_number}.{self.ball_number_in_over}"

    def save(self, *args, **kwargs):
        if self.ball_type != BallType.NORMAL:
            self.extras_type = self.ball_type

        # Track runs from extras based on type
        if self.ball_type == BallType.WIDE:
            self.runs_extras = self.extras_wide_runs
        elif self.ball_type == BallType.NO_BALL:
            self.runs_extras = self.extras_no_ball_runs
        elif self.ball_type == BallType.BYE:
            self.runs_extras = self.extras_bye_runs
        elif self.ball_type == BallType.LEG_BYE:
            self.runs_extras = self.extras_leg_bye_runs
        elif self.ball_type == BallType.PENALTY:
            self.runs_extras = self.extras_penalty_runs

        self.total_runs_on_ball = self.runs_from_bat + self.runs_extras

        # Auto-classify ball
        self.is_dot_ball = self.total_runs_on_ball == 0 and not self.is_wicket
        self.is_boundary = self.runs_from_bat in (4,)
        self.is_six = self.runs_from_bat == 6
        self.is_legal = self.ball_type in (BallType.NORMAL, BallType.BYE, BallType.LEG_BYE)
        self.is_maiden_ball = self.is_legal and self.total_runs_on_ball == 0

        super().save(*args, **kwargs)

    @property
    def display_score(self):
        """Human-readable score for this ball."""
        parts = []
        if self.is_wicket:
            parts.append(f'W')
        elif self.is_six:
            parts.append('6')
        elif self.is_boundary:
            parts.append('4')
        elif self.ball_type == BallType.WIDE:
            runs = self.extras_wide_runs or 1
            parts.append(f'WD{"+" + str(runs - 1) if runs > 1 else ""}')
        elif self.ball_type == BallType.NO_BALL:
            runs = self.extras_no_ball_runs or 1
            parts.append(f'NB{"+" + str(runs - 1) if runs > 1 else ""}')
        elif self.runs_from_bat > 0:
            parts.append(str(self.runs_from_bat))
        else:
            parts.append('0')

        if self.dismissal_type and self.is_wicket:
            parts.append(f' - {self.get_dismissal_type_display()}')

        return ' '.join(parts)


# ── Batter Scoring Record ───────────────────────────────────────────────

class BatterInnings(BaseModel):
    """
    Individual batter's performance in a single innings.
    Updated as each ball is bowled.
    """
    innings = models.ForeignKey(
        Innings,
        on_delete=models.CASCADE,
        related_name='batting_records',
    )
    player = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.CASCADE,
        related_name='batting_innings',
    )
    batting_position = models.PositiveIntegerField(
        default=1,
        help_text='Batting position in the order (1-11)',
    )
    is_out = models.BooleanField(default=False)
    dismissal_type = models.CharField(
        max_length=20,
        choices=DismissalType.choices,
        blank=True, default='',
    )
    dismissed_by = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='batters_dismissed',
    )
    fielder = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='batters_run_out',
    )

    # Batting stats
    runs = models.PositiveIntegerField(default=0)
    balls_faced = models.PositiveIntegerField(default=0)
    fours = models.PositiveIntegerField(default=0)
    sixes = models.PositiveIntegerField(default=0)
    strike_rate = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    dot_balls = models.PositiveIntegerField(default=0)

    # How out details
    how_out_description = models.CharField(max_length=255, blank=True, default='')

    # Timing
    batting_time_minutes = models.PositiveIntegerField(null=True, blank=True)
    came_to_crease_at = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Innings ball number when this batter came in',
    )
    dismissed_at = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Innings ball number when this batter was dismissed',
    )

    class Meta:
        db_table = 'scoring_batter_innings'
        verbose_name = 'Batter Innings'
        verbose_name_plural = 'Batter Innings'
        ordering = ['innings', 'batting_position']
        indexes = [
            models.Index(fields=['innings', 'player']),
            models.Index(fields=['player', 'is_out']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['innings', 'player'],
                name='unique_batter_in_innings',
            ),
        ]

    def __str__(self):
        status = f" c {self.dismissed_by}" if self.is_out else "*"
        return f"{self.player} {self.runs}({self.balls_faced}){status}"

    @property
    def display_score(self):
        status = "*" if not self.is_out else ""
        return f"{self.runs}{status} ({self.balls_faced}b {self.fours}x4 {self.sixes}x6)"

    def calculate_strike_rate(self):
        if self.balls_faced > 0:
            self.strike_rate = (Decimal(str(self.runs)) / Decimal(str(self.balls_faced))) * Decimal('100')
        else:
            self.strike_rate = Decimal('0.00')
        return self.strike_rate


# ── Bowler Scoring Record ───────────────────────────────────────────────

class BowlerFigures(BaseModel):
    """
    Individual bowler's figures in a single innings.
    Updated as each ball is bowled.
    """
    innings = models.ForeignKey(
        Innings,
        on_delete=models.CASCADE,
        related_name='bowling_records',
    )
    player = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.CASCADE,
        related_name='bowling_figures',
    )

    # Bowling figures
    overs_bowled = models.DecimalField(
        max_digits=5, decimal_places=1, default=0.0,
    )
    maidens = models.PositiveIntegerField(default=0)
    runs_conceded = models.PositiveIntegerField(default=0)
    wickets = models.PositiveIntegerField(default=0)
    wides = models.PositiveIntegerField(default=0)
    no_balls = models.PositiveIntegerField(default=0)
    dots = models.PositiveIntegerField(default=0)
    fours_conceded = models.PositiveIntegerField(default=0)
    sixes_conceded = models.PositiveIntegerField(default=0)
    economy_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    balls_bowled = models.PositiveIntegerField(default=0)
    legal_deliveries = models.PositiveIntegerField(default=0)

    # Bowling position
    bowling_order = models.PositiveIntegerField(default=1)
    is_bowling = models.BooleanField(default=False)

    class Meta:
        db_table = 'scoring_bowler_figures'
        verbose_name = 'Bowler Figures'
        verbose_name_plural = 'Bowler Figures'
        ordering = ['innings', 'bowling_order']
        indexes = [
            models.Index(fields=['innings', 'player']),
            models.Index(fields=['player', 'wickets']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['innings', 'player'],
                name='unique_bowler_in_innings',
            ),
        ]

    def __str__(self):
        return f"{self.player} {self.wickets}-{self.runs_conceded} ({self.overs_bowled} ov)"

    @property
    def display_figures(self):
        return f"{self.wickets}/{self.runs_conceded}"

    def calculate_economy(self):
        if self.overs_bowled > 0:
            self.economy_rate = Decimal(str(self.runs_conceded)) / Decimal(str(self.overs_bowled))
        else:
            self.economy_rate = Decimal('0.00')
        return self.economy_rate


# ── Fall of Wickets ─────────────────────────────────────────────────────

class FallOfWicket(BaseModel):
    """
    Records the fall of each wicket during an innings.
    Used for the scorecard wickets timeline.
    """
    innings = models.ForeignKey(
        Innings,
        on_delete=models.CASCADE,
        related_name='fall_of_wickets',
    )
    wicket_number = models.PositiveIntegerField(
        help_text='Which wicket fell (1-10)',
    )
    batter = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.CASCADE,
        related_name='fall_of_wickets',
    )
    team_score_at_wicket = models.PositiveIntegerField(
        help_text='Team total when wicket fell',
    )
    overs_at_wicket = models.DecimalField(
        max_digits=5, decimal_places=1,
        help_text='Over when wicket fell',
    )
    ball_number_in_innings = models.PositiveIntegerField(
        help_text='Absolute ball number when wicket fell',
    )
    partnership_runs = models.PositiveIntegerField(
        default=0,
        help_text='Runs scored in this partnership before wicket',
    )
    partnership_balls = models.PositiveIntegerField(
        default=0,
        help_text='Balls faced in this partnership',
    )
    dismissal_type = models.CharField(
        max_length=20,
        choices=DismissalType.choices,
        blank=True, default='',
    )
    dismissed_by = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='wicket_taken_fow',
    )

    class Meta:
        db_table = 'scoring_fall_of_wickets'
        verbose_name = 'Fall of Wicket'
        verbose_name_plural = 'Fall of Wickets'
        ordering = ['innings', 'wicket_number']
        unique_together = ['innings', 'wicket_number']

    def __str__(self):
        return f"{self.wicket_number}. {self.batter} - {self.team_score_at_wicket}/{self.wicket_number} ({self.overs_at_wicket} ov)"


# ── Partnership ─────────────────────────────────────────────────────────

class Partnership(BaseModel):
    """
    Tracks batting partnerships between two players.
    """
    innings = models.ForeignKey(
        Innings,
        on_delete=models.CASCADE,
        related_name='partnerships',
    )
    batter_one = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.CASCADE,
        related_name='partnerships_as_one',
    )
    batter_two = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.CASCADE,
        related_name='partnerships_as_two',
    )
    runs = models.PositiveIntegerField(default=0)
    balls_faced = models.PositiveIntegerField(default=0)
    fours = models.PositiveIntegerField(default=0)
    sixes = models.PositiveIntegerField(default=0)
    is_current = models.BooleanField(default=True)
    start_at_ball = models.PositiveIntegerField()
    end_at_ball = models.PositiveIntegerField(null=True, blank=True)
    ended_by_wicket = models.BooleanField(default=False)
    run_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        db_table = 'scoring_partnerships'
        verbose_name = 'Partnership'
        verbose_name_plural = 'Partnerships'
        ordering = ['-runs']
        indexes = [
            models.Index(fields=['innings', 'is_current']),
        ]

    def __str__(self):
        return f"{self.batter_one} + {self.batter_two} = {self.runs} ({self.balls_faced}b)"


# ── Over Summary ────────────────────────────────────────────────────────

class OverSummary(BaseModel):
    """
    Summary of each over (bowler, runs, wickets, etc.).
    Used for scorecard over-by-over breakdown.
    """
    innings = models.ForeignKey(
        Innings,
        on_delete=models.CASCADE,
        related_name='over_summaries',
    )
    over_number = models.PositiveIntegerField(db_index=True)
    bowler = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.CASCADE,
        related_name='overs_bowled',
    )
    runs_conceded = models.PositiveIntegerField(default=0)
    wickets_in_over = models.PositiveIntegerField(default=0)
    is_maiden = models.BooleanField(default=False)
    is_wicket_maiden = models.BooleanField(default=False)
    total_balls = models.PositiveIntegerField(default=6)
    legal_balls = models.PositiveIntegerField(default=6)
    extra_balls = models.PositiveIntegerField(default=0)
    runs_from_bat = models.PositiveIntegerField(default=0)
    runs_extras = models.PositiveIntegerField(default=0)
    dot_balls = models.PositiveIntegerField(default=0)
    boundaries = models.PositiveIntegerField(default=0)
    sixes_in_over = models.PositiveIntegerField(default=0)
    cumulative_score = models.PositiveIntegerField(
        help_text='Team score at end of this over',
    )
    cumulative_wickets = models.PositiveIntegerField(
        help_text='Team wickets at end of this over',
    )
    is_completed = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'scoring_over_summaries'
        verbose_name = 'Over Summary'
        verbose_name_plural = 'Over Summaries'
        ordering = ['innings', 'over_number']
        unique_together = ['innings', 'over_number']

    def __str__(self):
        runs_str = f"{self.runs_conceded} runs"
        wkts = f", {self.wickets_in_over}w" if self.wickets_in_over else ""
        maiden = " (M)" if self.is_maiden else ""
        return f"Over {self.over_number}: {runs_str}{wkts}{maiden} - {self.bowler}"


# ── Commentary ──────────────────────────────────────────────────────────

class Commentary(BaseModel):
    """
    Ball-by-ball commentary with timestamps.
    Supports auto-generated and manual commentary.
    """
    ball = models.OneToOneField(
        Ball,
        on_delete=models.CASCADE,
        related_name='commentary_detail',
    )
    innings = models.ForeignKey(
        Innings,
        on_delete=models.CASCADE,
        related_name='commentaries',
    )
    match = models.ForeignKey(
        'tournaments.TournamentMatch',
        on_delete=models.CASCADE,
        related_name='commentaries',
    )

    text = models.TextField(blank=True, default='')
    summary = models.CharField(max_length=255, blank=True, default='')
    is_auto_generated = models.BooleanField(default=True)
    is_highlight = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'scoring_commentary'
        verbose_name = 'Commentary'
        verbose_name_plural = 'Commentaries'
        ordering = ['-ball__ball_number_in_innings']
        indexes = [
            models.Index(fields=['match', '-created_at']),
            models.Index(fields=['innings', '-created_at']),
            models.Index(fields=['is_highlight']),
        ]

    def __str__(self):
        return f"Commentary: {self.ball}"


# ── Current Match State ─────────────────────────────────────────────────

class MatchState(BaseModel):
    """
    Denormalized current state of a live match for fast reads.
    Updated frequently during a live match to avoid heavy aggregations.
    """
    match = models.OneToOneField(
        'tournaments.TournamentMatch',
        on_delete=models.CASCADE,
        related_name='live_state',
    )
    current_innings = models.ForeignKey(
        Innings,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='live_state_for',
    )

    # Current batting team
    batting_team = models.ForeignKey(
        'tournaments.TournamentTeam',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='batting_state',
    )
    bowling_team = models.ForeignKey(
        'tournaments.TournamentTeam',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='bowling_state',
    )

    # Current batters at crease
    striker = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='striker_state',
    )
    non_striker = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='non_striker_state',
    )
    current_bowler = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='current_bowler_state',
    )

    # Current over state
    current_over_number = models.PositiveIntegerField(default=0)
    current_ball_in_over = models.PositiveIntegerField(default=0)
    balls_in_current_over = models.PositiveIntegerField(default=0)

    # Score
    runs = models.PositiveIntegerField(default=0)
    wickets = models.PositiveIntegerField(default=0)
    overs_bowled = models.DecimalField(max_digits=5, decimal_places=1, default=0.0)
    run_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    target_runs = models.PositiveIntegerField(null=True, blank=True)
    runs_required = models.PositiveIntegerField(null=True, blank=True)
    required_run_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    balls_remaining = models.PositiveIntegerField(null=True, blank=True)

    # Recent balls (last 5-6 balls for live display)
    recent_balls = models.JSONField(default=list, blank=True)

    # Match timing
    is_live = models.BooleanField(default=False)
    has_started = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'scoring_match_state'
        verbose_name = 'Match State'
        verbose_name_plural = 'Match States'

    def __str__(self):
        return f"Live: {self.match}"


class ScoreCorrection(BaseModel):
    """Audit record for a scorer correction without retaining a live delivery."""
    match = models.ForeignKey(
        'tournaments.TournamentMatch',
        on_delete=models.CASCADE,
        related_name='score_corrections',
    )
    innings = models.ForeignKey(
        Innings,
        on_delete=models.CASCADE,
        related_name='score_corrections',
    )
    ball_reference = models.CharField(max_length=30)
    reason = models.CharField(max_length=255)
    original_data = models.JSONField(default=dict)
    corrected_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='score_corrections',
    )
    corrected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'scoring_score_corrections'
        ordering = ['-corrected_at']

    def __str__(self):
        return f"{self.match} - {self.ball_reference}"


# ── Signals file (placeholder) ──────────────────────────────────────────
