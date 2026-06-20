from rest_framework import serializers

from apps.accounts.models import Tenant, UserTenant
from apps.players.models import (
    PlayerProfile,
    PlayerBattingSkill,
    PlayerBowlingSkill,
    PlayerFieldingSkill,
    PlayerContract,
    PlayerTransfer,
    PlayerInjury,
    PlayerAchievement,
    PlayerCareerStats,
)
from apps.teams.models import (
    Team,
    TeamCategory,
    TeamType,
    TeamSeason,
    TeamSquad,
    TeamStaff,
    TeamStat,
    TeamRanking,
    TeamSponsorship,
    TeamAchievement,
    TeamTransfer,
    TeamDocument,
)
from apps.tournaments.models import (
    Tournament,
    TournamentFormat,
    TournamentStage,
    TournamentStageInstance,
    TournamentGroup,
    TournamentMatch,
    TournamentTeam,
    TournamentPlayer,
    TournamentPointsTable,
    TournamentOfficial,
    TournamentSponsor,
    TournamentAward,
    TournamentMedia,
)


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = (
            'id',
            'name',
            'tenant_type',
            'domain',
            'subdomain',
            'logo',
            'primary_color',
            'secondary_color',
            'subscription_plan',
            'verified',
            'status',
        )
        read_only_fields = fields


class UserTenantSerializer(serializers.ModelSerializer):
    tenant = TenantSerializer(read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)

    class Meta:
        model = UserTenant
        fields = ('id', 'tenant', 'role_name', 'is_primary', 'is_active', 'joined_at')
        read_only_fields = fields


class PlayerProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)

    class Meta:
        model = PlayerProfile
        fields = (
            'id',
            'tenant',
            'full_name',
            'first_name',
            'last_name',
            'photo',
            'role',
            'batting_style',
            'bowling_style',
            'player_status',
            'jersey_number',
            'city',
            'state',
            'age',
            'is_bowler',
            'is_wicket_keeper',
        )
        read_only_fields = ('id', 'full_name', 'age')


class TeamCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamCategory
        fields = ('id', 'name')
        read_only_fields = fields


class TeamTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamType
        fields = ('id', 'name')
        read_only_fields = fields


class TeamSerializer(serializers.ModelSerializer):
    team_category = TeamCategorySerializer(read_only=True)
    team_type = TeamTypeSerializer(read_only=True)
    team_category_id = serializers.PrimaryKeyRelatedField(
        queryset=TeamCategory.objects.all(),
        source='team_category',
        required=False,
        allow_null=True,
        write_only=True,
    )
    team_type_id = serializers.PrimaryKeyRelatedField(
        queryset=TeamType.objects.all(),
        source='team_type',
        required=False,
        allow_null=True,
        write_only=True,
    )

    class Meta:
        model = Team
        fields = (
            'id',
            'tenant',
            'name',
            'code',
            'short_name',
            'abbreviation',
            'logo',
            'team_category',
            'team_category_id',
            'team_type',
            'team_type_id',
            'city',
            'state',
            'home_ground',
            'year',
            'is_active',
            'status',
        )
        read_only_fields = ('id', 'team_category', 'team_type')


class TournamentFormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = TournamentFormat
        fields = ('id', 'name', 'code', 'max_teams', 'max_players_per_team')
        read_only_fields = fields


class TournamentSerializer(serializers.ModelSerializer):
    format = TournamentFormatSerializer(read_only=True)
    format_id = serializers.PrimaryKeyRelatedField(
        queryset=TournamentFormat.objects.all(),
        source='format',
        write_only=True,
    )

    class Meta:
        model = Tournament
        fields = (
            'id',
            'tenant',
            'name',
            'slug',
            'format',
            'format_id',
            'season',
            'year',
            'start_date',
            'end_date',
            'venue',
            'city',
            'state',
            'total_teams',
            'total_matches',
            'total_players',
            'is_featured',
            'status',
        )
        read_only_fields = ('id', 'format')


class TournamentTeamSerializer(serializers.ModelSerializer):
    tournament_name = serializers.CharField(source='tournament.name', read_only=True)
    team = TeamSerializer(read_only=True)
    team_id = serializers.PrimaryKeyRelatedField(
        queryset=Team.objects.all(),
        source='team',
        write_only=True,
    )
    group_id = serializers.PrimaryKeyRelatedField(
        queryset=TournamentGroup.objects.all(),
        source='group',
        required=False,
        allow_null=True,
        write_only=True,
    )
    captain_id = serializers.PrimaryKeyRelatedField(
        queryset=PlayerProfile.objects.all(),
        source='captain',
        required=False,
        allow_null=True,
        write_only=True,
    )
    vice_captain_id = serializers.PrimaryKeyRelatedField(
        queryset=PlayerProfile.objects.all(),
        source='vice_captain',
        required=False,
        allow_null=True,
        write_only=True,
    )

    class Meta:
        model = TournamentTeam
        fields = (
            'id',
            'tournament',
            'tournament_name',
            'team',
            'team_id',
            'group',
            'group_id',
            'is_verified',
            'seed',
            'captain',
            'captain_id',
            'vice_captain',
            'vice_captain_id',
            'registration_date',
        )
        read_only_fields = ('id', 'tournament_name', 'team', 'registration_date')

    def validate(self, attrs):
        tournament = attrs.get('tournament') or getattr(self.instance, 'tournament', None)
        team = attrs.get('team') or getattr(self.instance, 'team', None)
        group = attrs.get('group') or getattr(self.instance, 'group', None)
        captain = attrs.get('captain') or getattr(self.instance, 'captain', None)
        vice_captain = attrs.get('vice_captain') or getattr(self.instance, 'vice_captain', None)

        if tournament and team and tournament.tenant_id != team.tenant_id:
            raise serializers.ValidationError('Team must belong to the same tenant as the tournament.')

        if group and tournament and group.stage_instance.tournament_id != tournament.id:
            raise serializers.ValidationError('Group must belong to the selected tournament.')

        for field_name, player in (('captain_id', captain), ('vice_captain_id', vice_captain)):
            if player and tournament and player.tenant_id != tournament.tenant_id:
                raise serializers.ValidationError({field_name: 'Player must belong to the tournament tenant.'})

        if captain and vice_captain and captain.id == vice_captain.id:
            raise serializers.ValidationError('Captain and vice-captain must be different players.')

        return attrs


class TournamentMatchSerializer(serializers.ModelSerializer):
    home_team_name = serializers.CharField(source='home_team.team.name', read_only=True)
    away_team_name = serializers.CharField(source='away_team.team.name', read_only=True)
    winner_name = serializers.CharField(source='winner.team.name', read_only=True)

    class Meta:
        model = TournamentMatch
        fields = (
            'id',
            'tournament',
            'match_number',
            'home_team',
            'away_team',
            'home_team_name',
            'away_team_name',
            'match_date',
            'venue',
            'ground',
            'result_type',
            'winner',
            'winner_name',
            'home_team_score',
            'away_team_score',
            'is_completed',
            'status',
        )
        read_only_fields = fields


class PlayerBattingSkillSerializer(serializers.ModelSerializer):
    overall_rating = serializers.IntegerField(read_only=True)

    class Meta:
        model = PlayerBattingSkill
        fields = '__all__'


class PlayerBowlingSkillSerializer(serializers.ModelSerializer):
    overall_rating = serializers.IntegerField(read_only=True)

    class Meta:
        model = PlayerBowlingSkill
        fields = '__all__'


class PlayerFieldingSkillSerializer(serializers.ModelSerializer):
    overall_rating = serializers.IntegerField(read_only=True)

    class Meta:
        model = PlayerFieldingSkill
        fields = '__all__'


class PlayerContractSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source='player.full_name', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)

    class Meta:
        model = PlayerContract
        fields = '__all__'

    def validate(self, attrs):
        player = attrs.get('player') or getattr(self.instance, 'player', None)
        team = attrs.get('team') or getattr(self.instance, 'team', None)
        if player and team and player.tenant_id != team.tenant_id:
            raise serializers.ValidationError('Player and Team must belong to the same tenant.')
        return attrs


class PlayerTransferSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source='player.full_name', read_only=True)
    from_team_name = serializers.CharField(source='from_team.name', read_only=True)
    to_team_name = serializers.CharField(source='to_team.name', read_only=True)

    class Meta:
        model = PlayerTransfer
        fields = '__all__'

    def validate(self, attrs):
        player = attrs.get('player') or getattr(self.instance, 'player', None)
        to_team = attrs.get('to_team') or getattr(self.instance, 'to_team', None)
        from_team = attrs.get('from_team') or getattr(self.instance, 'from_team', None)
        
        if player and to_team and player.tenant_id != to_team.tenant_id:
            raise serializers.ValidationError('Player and Destination Team must belong to the same tenant.')
        if player and from_team and player.tenant_id != from_team.tenant_id:
            raise serializers.ValidationError('Player and Source Team must belong to the same tenant.')
        return attrs


class PlayerInjurySerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source='player.full_name', read_only=True)

    class Meta:
        model = PlayerInjury
        fields = '__all__'


class PlayerAchievementSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source='player.full_name', read_only=True)
    tournament_name = serializers.CharField(source='tournament.name', read_only=True)

    class Meta:
        model = PlayerAchievement
        fields = '__all__'


class PlayerCareerStatsSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source='player.full_name', read_only=True)

    class Meta:
        model = PlayerCareerStats
        fields = '__all__'


# Team sub-entity serializers
class TeamSeasonSerializer(serializers.ModelSerializer):
    team_name_display = serializers.CharField(source='team.name', read_only=True)

    class Meta:
        model = TeamSeason
        fields = '__all__'


class TeamSquadSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source='player.full_name', read_only=True)

    class Meta:
        model = TeamSquad
        fields = '__all__'


class TeamStaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamStaff
        fields = '__all__'


class TeamStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamStat
        fields = '__all__'


class TeamRankingSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source='team.name', read_only=True)

    class Meta:
        model = TeamRanking
        fields = '__all__'


class TeamSponsorshipSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source='team.name', read_only=True)

    class Meta:
        model = TeamSponsorship
        fields = '__all__'


class TeamAchievementSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source='team.name', read_only=True)

    class Meta:
        model = TeamAchievement
        fields = '__all__'


class TeamTransferSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source='player.full_name', read_only=True)
    from_team_name = serializers.CharField(source='from_team.name', read_only=True)
    to_team_name = serializers.CharField(source='to_team.name', read_only=True)

    class Meta:
        model = TeamTransfer
        fields = '__all__'


class TeamDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamDocument
        fields = '__all__'


# Tournament sub-entity serializers
class TournamentStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TournamentStage
        fields = '__all__'


class TournamentStageInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TournamentStageInstance
        fields = '__all__'


class TournamentGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = TournamentGroup
        fields = '__all__'


class TournamentPlayerSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source='player.full_name', read_only=True)

    class Meta:
        model = TournamentPlayer
        fields = '__all__'


class TournamentPointsTableSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source='team.team.name', read_only=True)

    class Meta:
        model = TournamentPointsTable
        fields = '__all__'


class TournamentOfficialSerializer(serializers.ModelSerializer):
    official_name = serializers.CharField(source='official.full_name', read_only=True)

    class Meta:
        model = TournamentOfficial
        fields = '__all__'


class TournamentSponsorSerializer(serializers.ModelSerializer):
    class Meta:
        model = TournamentSponsor
        fields = '__all__'


class TournamentAwardSerializer(serializers.ModelSerializer):
    winner_name = serializers.CharField(source='winner.full_name', read_only=True)

    class Meta:
        model = TournamentAward
        fields = '__all__'


class TournamentMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TournamentMedia
        fields = '__all__'


