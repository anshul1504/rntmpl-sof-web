"""
Tournament Models for the Cricket Ecosystem Platform.
All tournament-related models inherit from the common base classes.
Table prefix: tournaments_
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.common.models import (
    BaseModel,
    NamedModel,
    CodedNamedModel,
    TimestampMixin,
    StatusMixin,
    YearMixin,
    SeasonMixin,
    EffectiveDateMixin,
    NoteMixin,
    OrderingMixin,
    SlugMixin,
)


class TournamentFormat(CodedNamedModel):
    """
    Defines the structure/format of a tournament.
    Examples: League, Knockout, Group+Knockout, Round Robin, etc.
    """
    max_teams = models.PositiveIntegerField(default=0, help_text="Maximum number of teams allowed (0 = unlimited)")
    max_players_per_team = models.PositiveIntegerField(default=15)
    allow_draws = models.BooleanField(default=False)
    points_for_win = models.DecimalField(max_digits=5, decimal_places=2, default=2.00)
    points_for_draw = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    points_for_loss = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    has_group_stage = models.BooleanField(default=False)
    has_knockout_stage = models.BooleanField(default=True)
    number_of_legs = models.PositiveIntegerField(default=1, help_text="Number of legs per match (1=single leg, 2=home/away)")

    class Meta:
        db_table = 'tournaments_formats'
        verbose_name = 'Tournament Format'
        verbose_name_plural = 'Tournament Formats'

    def __str__(self):
        return f"{self.name} ({self.code})"


class TournamentStage(NamedModel):
    """
    Represents a stage/phase in a tournament.
    Examples: Group Stage, Quarter Final, Semi Final, Final, etc.
    """
    format = models.ForeignKey(
        TournamentFormat,
        on_delete=models.CASCADE,
        related_name='%(class)s_stages',
        null=True,
        blank=True,
    )
    sequence = models.PositiveIntegerField(default=0, db_index=True)
    is_group_stage = models.BooleanField(default=False)
    is_knockout_stage = models.BooleanField(default=False)
    number_of_teams = models.PositiveIntegerField(default=0, help_text="Number of teams that enter this stage")
    number_of_groups = models.PositiveIntegerField(default=0, help_text="Number of groups (if group stage)")
    teams_qualify_per_group = models.PositiveIntegerField(default=0, help_text="Teams that qualify from each group to next stage")

    class Meta:
        db_table = 'tournaments_stages'
        verbose_name = 'Tournament Stage'
        verbose_name_plural = 'Tournament Stages'
        ordering = ['sequence']

    def __str__(self):
        return self.name


class Tournament(BaseModel, YearMixin, SeasonMixin, EffectiveDateMixin, NoteMixin):
    """
    Main tournament entity. Represents a specific edition of a tournament.
    e.g., "RNT MPL Season 1 - 2025"
    """
    tenant = models.ForeignKey(
        'accounts.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='tournaments',
        db_index=True,
        help_text='Tenant that owns this tournament.',
    )
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    format = models.ForeignKey(
        TournamentFormat,
        on_delete=models.CASCADE,
        related_name='%(class)s_tournaments',
    )
    season = models.CharField(max_length=100, blank=True, default='', db_index=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    registration_start_date = models.DateTimeField(null=True, blank=True)
    registration_end_date = models.DateTimeField(null=True, blank=True)
    venue = models.CharField(max_length=255, blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    state = models.CharField(max_length=100, blank=True, default='')
    country = models.CharField(max_length=100, default='India')
    total_teams = models.PositiveIntegerField(default=0)
    total_matches = models.PositiveIntegerField(default=0)
    total_players = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    banner_image = models.ImageField(upload_to='tournaments/banners/', null=True, blank=True)
    logo = models.ImageField(upload_to='tournaments/logos/', null=True, blank=True)
    rules_and_regulations = models.TextField(blank=True, default='')
    prize_money = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    entry_fee = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    max_teams_allowed = models.PositiveIntegerField(default=0, help_text="0 = unlimited")

    class Meta:
        db_table = 'tournaments'
        verbose_name = 'Tournament'
        verbose_name_plural = 'Tournaments'
        ordering = ['-year', '-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['year', 'season']),
            models.Index(fields=['status', 'start_date']),
        ]

    def __str__(self):
        year_str = f" {self.year}" if self.year else ""
        return f"{self.name}{year_str}"


class TournamentRule(BaseModel):
    """Operational cricket rules applied to every match in a tournament."""
    tournament = models.OneToOneField(
        Tournament,
        on_delete=models.CASCADE,
        related_name='rules',
    )
    overs_per_innings = models.PositiveIntegerField(default=20)
    players_per_side = models.PositiveIntegerField(default=11)
    max_squad_size = models.PositiveIntegerField(default=25)
    max_overs_per_bowler = models.PositiveIntegerField(default=4)
    powerplay_overs = models.PositiveIntegerField(default=6)
    max_foreign_players_in_xi = models.PositiveIntegerField(default=4)
    allow_impact_player = models.BooleanField(default=True)
    allow_super_over = models.BooleanField(default=True)
    allow_dls = models.BooleanField(default=True)
    free_hit_after_no_ball = models.BooleanField(default=True)
    points_for_win = models.DecimalField(max_digits=5, decimal_places=2, default=2)
    points_for_tie = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    points_for_no_result = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    points_for_loss = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        db_table = 'tournaments_rules'

    def __str__(self):
        return f"{self.tournament.name} rules"


class TournamentStageInstance(BaseModel, EffectiveDateMixin):
    """
    Instance of a tournament stage for a specific tournament.
    e.g., "RNT MPL 2025 - Group Stage"
    """
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='%(class)s_stages',
    )
    stage = models.ForeignKey(
        TournamentStage,
        on_delete=models.CASCADE,
        related_name='%(class)s_instances',
    )
    name = models.CharField(max_length=255)
    sequence = models.PositiveIntegerField(default=0, db_index=True)
    is_completed = models.BooleanField(default=False)

    class Meta:
        db_table = 'tournaments_stage_instances'
        verbose_name = 'Tournament Stage Instance'
        verbose_name_plural = 'Tournament Stage Instances'
        ordering = ['tournament', 'sequence']
        unique_together = ['tournament', 'stage']

    def __str__(self):
        return f"{self.tournament.name} - {self.stage.name}"


class TournamentGroup(BaseModel, OrderingMixin):
    """
    Group within a tournament stage (for group stages).
    e.g., Group A, Group B
    """
    stage_instance = models.ForeignKey(
        TournamentStageInstance,
        on_delete=models.CASCADE,
        related_name='%(class)s_groups',
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, blank=True, default='')

    class Meta:
        db_table = 'tournaments_groups'
        verbose_name = 'Tournament Group'
        verbose_name_plural = 'Tournament Groups'
        ordering = ['stage_instance', 'sequence']

    def __str__(self):
        return f"{self.stage_instance} - {self.name}"


class TournamentTeam(BaseModel, NoteMixin):
    """
    Represents a team's participation in a tournament.
    Links a team to a tournament with squad registration.
    """
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='%(class)s_teams',
    )
    team = models.ForeignKey(
        'teams.Team',  # Assuming teams app has Team model
        on_delete=models.CASCADE,
        related_name='%(class)s_tournaments',
    )
    group = models.ForeignKey(
        TournamentGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_teams',
    )
    jersey_color = models.CharField(max_length=20, blank=True, default='')
    is_verified = models.BooleanField(default=False)
    registration_date = models.DateTimeField(auto_now_add=True)
    seed = models.PositiveIntegerField(default=0, help_text="Seeding number for tournament")
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

    class Meta:
        db_table = 'tournaments_teams'
        verbose_name = 'Tournament Team'
        verbose_name_plural = 'Tournament Teams'
        unique_together = ['tournament', 'team']

    def __str__(self):
        return f"{self.team.name} in {self.tournament.name}"


class TournamentPlayer(BaseModel):
    """
    Represents a player registered for a specific tournament team.
    Links a player to a tournament team.
    """
    tournament_team = models.ForeignKey(
        TournamentTeam,
        on_delete=models.CASCADE,
        related_name='%(class)s_players',
    )
    player = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.CASCADE,
        related_name='%(class)s_registrations',
    )
    jersey_number = models.PositiveIntegerField(default=0)
    is_playing = models.BooleanField(default=True, help_text="Currently part of active squad")
    is_foreign_player = models.BooleanField(default=False)
    role = models.CharField(max_length=50, blank=True, default='', help_text="Role in team for this tournament")
    joined_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tournaments_players'
        verbose_name = 'Tournament Player'
        verbose_name_plural = 'Tournament Players'
        unique_together = ['tournament_team', 'player']

    def __str__(self):
        return f"{self.player} - {self.tournament_team}"


class TournamentMatch(BaseModel, EffectiveDateMixin):
    """
    Represents a match within a tournament.
    Links teams, venue, officials, and results.
    """
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='%(class)s_matches',
    )
    stage_instance = models.ForeignKey(
        TournamentStageInstance,
        on_delete=models.CASCADE,
        related_name='%(class)s_matches',
        null=True,
        blank=True,
    )
    group = models.ForeignKey(
        TournamentGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_matches',
    )
    home_team = models.ForeignKey(
        TournamentTeam,
        on_delete=models.CASCADE,
        related_name='%(class)s_home_matches',
    )
    away_team = models.ForeignKey(
        TournamentTeam,
        on_delete=models.CASCADE,
        related_name='%(class)s_away_matches',
    )
    match_date = models.DateTimeField(null=True, blank=True)
    venue = models.CharField(max_length=255, blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    state = models.CharField(max_length=100, blank=True, default='')
    ground = models.CharField(max_length=255, blank=True, default='')
    venue_record = models.ForeignKey(
        'venues.Venue',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='matches',
    )
    ground_record = models.ForeignKey(
        'venues.Ground',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='matches',
    )

    # Match result fields
    class ResultType(models.TextChoices):
        NORMAL = 'NORMAL', 'Normal'
        SUPER_OVER = 'SUPER_OVER', 'Super Over'
        TIE = 'TIE', 'Tie'
        ABANDONED = 'ABANDONED', 'Abandoned'
        WALKOVER = 'WALKOVER', 'Walkover'
        DEFAULTED = 'DEFAULTED', 'Defaulted'
        CANCELLED = 'CANCELLED', 'Cancelled'

    result_type = models.CharField(
        max_length=20,
        choices=ResultType.choices,
        default=ResultType.NORMAL,
    )
    winner = models.ForeignKey(
        TournamentTeam,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_won_matches',
    )
    loser = models.ForeignKey(
        TournamentTeam,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_lost_matches',
    )
    is_draw = models.BooleanField(default=False)
    home_team_score = models.CharField(max_length=50, blank=True, default='')
    away_team_score = models.CharField(max_length=50, blank=True, default='')
    home_team_overs = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    away_team_overs = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    man_of_the_match = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_mom_awards',
    )
    is_completed = models.BooleanField(default=False)
    match_number = models.PositiveIntegerField(default=0, help_text="Match number in tournament")
    leg = models.PositiveIntegerField(default=1, help_text="Which leg (1=first, 2=second, etc.)")

    class Meta:
        db_table = 'tournaments_matches'
        verbose_name = 'Tournament Match'
        verbose_name_plural = 'Tournament Matches'
        ordering = ['match_date', 'match_number']
        indexes = [
            models.Index(fields=['tournament', 'match_date']),
            models.Index(fields=['tournament', 'stage_instance']),
        ]

    def __str__(self):
        return f"{self.tournament.name} - {self.home_team} vs {self.away_team}"


class MatchSetup(BaseModel):
    """Pre-match operational state: toss, decision, lifecycle and setup lock."""

    class Lifecycle(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        READY = 'READY', 'Ready for scoring'
        LIVE = 'LIVE', 'Live'
        INNINGS_BREAK = 'INNINGS_BREAK', 'Innings break'
        COMPLETED = 'COMPLETED', 'Completed'
        ABANDONED = 'ABANDONED', 'Abandoned'
        CANCELLED = 'CANCELLED', 'Cancelled'

    class TossDecision(models.TextChoices):
        BAT = 'BAT', 'Bat'
        BOWL = 'BOWL', 'Bowl'

    match = models.OneToOneField(
        TournamentMatch,
        on_delete=models.CASCADE,
        related_name='setup',
    )
    lifecycle = models.CharField(
        max_length=20,
        choices=Lifecycle.choices,
        default=Lifecycle.SCHEDULED,
        db_index=True,
    )
    toss_winner = models.ForeignKey(
        TournamentTeam,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tosses_won',
    )
    toss_decision = models.CharField(
        max_length=10,
        choices=TossDecision.choices,
        blank=True,
        default='',
    )
    toss_recorded_at = models.DateTimeField(null=True, blank=True)
    setup_locked_at = models.DateTimeField(null=True, blank=True)
    setup_locked_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='locked_match_setups',
    )

    class Meta:
        db_table = 'tournaments_match_setup'

    @property
    def is_ready(self):
        if not self.toss_winner_id or not self.toss_decision:
            return False
        rules = getattr(self.match.tournament, 'rules', None)
        required = rules.players_per_side if rules else 11
        teams = (self.match.home_team_id, self.match.away_team_id)
        return all(
            self.playing_xi.filter(tournament_team_id=team_id, is_substitute=False).count() == required
            for team_id in teams
        )

    def __str__(self):
        return f"Setup: {self.match}"


class MatchPlayingXI(BaseModel):
    """A declared player for a team's match-day XI or substitute bench."""
    setup = models.ForeignKey(
        MatchSetup,
        on_delete=models.CASCADE,
        related_name='playing_xi',
    )
    tournament_team = models.ForeignKey(
        TournamentTeam,
        on_delete=models.CASCADE,
        related_name='match_selections',
    )
    player = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.CASCADE,
        related_name='match_selections',
    )
    batting_position = models.PositiveIntegerField(null=True, blank=True)
    is_captain = models.BooleanField(default=False)
    is_wicket_keeper = models.BooleanField(default=False)
    is_substitute = models.BooleanField(default=False)
    is_impact_player = models.BooleanField(default=False)

    class Meta:
        db_table = 'tournaments_match_playing_xi'
        ordering = ['tournament_team', 'is_substitute', 'batting_position']
        constraints = [
            models.UniqueConstraint(
                fields=['setup', 'player'],
                name='unique_player_in_match_setup',
            ),
        ]

    def __str__(self):
        return f"{self.player} - {self.tournament_team}"


class MatchOfficialAssignment(BaseModel):
    """Tournament official assigned to a specific match duty."""
    setup = models.ForeignKey(
        MatchSetup,
        on_delete=models.CASCADE,
        related_name='official_assignments',
    )
    tournament_official = models.ForeignKey(
        'TournamentOfficial',
        on_delete=models.CASCADE,
        related_name='match_assignments',
    )
    duty = models.CharField(
        max_length=30,
        choices=[
            ('UMPIRE', 'Umpire'),
            ('THIRD_UMPIRE', 'Third Umpire'),
            ('REFEREE', 'Match Referee'),
            ('SCORER', 'Scorer'),
            ('COMMISSIONER', 'Tournament Commissioner'),
            ('OTHER', 'Other'),
        ],
    )

    class Meta:
        db_table = 'tournaments_match_official_assignments'
        constraints = [
            models.UniqueConstraint(
                fields=['setup', 'tournament_official', 'duty'],
                name='unique_match_official_duty',
            ),
        ]

    def __str__(self):
        return f"{self.tournament_official} - {self.setup.match}"


class TournamentPointsTable(TimestampMixin):
    """
    Points table/standings for a group within a tournament.
    Tracks points, wins, losses, net run rate etc.
    """
    group = models.ForeignKey(
        TournamentGroup,
        on_delete=models.CASCADE,
        related_name='%(class)s_standings',
    )
    team = models.ForeignKey(
        TournamentTeam,
        on_delete=models.CASCADE,
        related_name='%(class)s_points',
    )
    matches_played = models.PositiveIntegerField(default=0)
    matches_won = models.PositiveIntegerField(default=0)
    matches_lost = models.PositiveIntegerField(default=0)
    matches_drawn = models.PositiveIntegerField(default=0)
    matches_tied = models.PositiveIntegerField(default=0)
    matches_no_result = models.PositiveIntegerField(default=0)
    points = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    net_run_rate = models.DecimalField(max_digits=8, decimal_places=4, default=0.0000)
    runs_for = models.PositiveIntegerField(default=0)
    runs_against = models.PositiveIntegerField(default=0)
    overs_for = models.DecimalField(max_digits=6, decimal_places=1, default=0.0)
    overs_against = models.DecimalField(max_digits=6, decimal_places=1, default=0.0)
    position = models.PositiveIntegerField(default=0, db_index=True)
    is_qualified = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'tournaments_points_table'
        verbose_name = 'Tournament Points Table'
        verbose_name_plural = 'Tournament Points Tables'
        unique_together = ['group', 'team']
        ordering = ['group', 'position']

    def __str__(self):
        return f"{self.team} - {self.points} pts (Pos: {self.position})"


class TournamentOfficial(BaseModel):
    """
    Officials (umpires, referees, scorers) assigned to a tournament.
    """
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='%(class)s_officials',
    )
    official = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.CASCADE,
        related_name='%(class)s_assignments',
    )

    class Role(models.TextChoices):
        UMPIRE = 'UMPIRE', 'Umpire'
        THIRD_UMPIRE = 'THIRD_UMPIRE', 'Third Umpire'
        REFEREE = 'REFEREE', 'Match Referee'
        SCORER = 'SCORER', 'Scorer'
        COMMISSIONER = 'COMMISSIONER', 'Tournament Commissioner'
        OTHER = 'OTHER', 'Other'

    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.UMPIRE,
    )
    is_chief_official = models.BooleanField(default=False)
    assigned_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tournaments_officials'
        verbose_name = 'Tournament Official'
        verbose_name_plural = 'Tournament Officials'
        unique_together = ['tournament', 'official', 'role']

    def __str__(self):
        return f"{self.official} - {self.get_role_display()} for {self.tournament.name}"


class TournamentSponsor(NamedModel):
    """
    Sponsors associated with a tournament.
    """
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='%(class)s_sponsors',
    )
    sponsorship_level = models.CharField(max_length=50, blank=True, default='')
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    logo = models.ImageField(upload_to='tournaments/sponsors/', null=True, blank=True)
    website = models.URLField(blank=True, default='')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'tournaments_sponsors'
        verbose_name = 'Tournament Sponsor'
        verbose_name_plural = 'Tournament Sponsors'

    def __str__(self):
        return f"{self.name} - {self.tournament.name}"


class TournamentAward(NamedModel):
    """
    Awards/categories for a tournament (e.g., Best Batsman, Best Bowler, Player of Tournament).
    """
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='%(class)s_awards',
    )
    winner = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_award_wins',
    )
    prize_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    criteria = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'tournaments_awards'
        verbose_name = 'Tournament Award'
        verbose_name_plural = 'Tournament Awards'

    def __str__(self):
        return f"{self.name} - {self.tournament.name}"


class TournamentMedia(NamedModel):
    """
    Media items (images, videos, documents) associated with a tournament.
    """
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='%(class)s_media',
    )

    class MediaType(models.TextChoices):
        IMAGE = 'IMAGE', 'Image'
        VIDEO = 'VIDEO', 'Video'
        DOCUMENT = 'DOCUMENT', 'Document'
        OTHER = 'OTHER', 'Other'

    media_type = models.CharField(
        max_length=20,
        choices=MediaType.choices,
        default=MediaType.IMAGE,
    )
    file = models.FileField(upload_to='tournaments/media/')
    caption = models.TextField(blank=True, default='')
    is_featured = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tournaments_media'
        verbose_name = 'Tournament Media'
        verbose_name_plural = 'Tournament Media'

    def __str__(self):
        return f"{self.name} ({self.get_media_type_display()})"
