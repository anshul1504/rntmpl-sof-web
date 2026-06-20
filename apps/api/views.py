from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from apps.accounts.models import Tenant, UserTenant
from apps.api.permissions import IsAuthenticatedReadOnly
from apps.api.serializers import (
    PlayerProfileSerializer,
    PlayerBattingSkillSerializer,
    PlayerBowlingSkillSerializer,
    PlayerFieldingSkillSerializer,
    PlayerContractSerializer,
    PlayerTransferSerializer,
    PlayerInjurySerializer,
    PlayerAchievementSerializer,
    PlayerCareerStatsSerializer,
    TeamSerializer,
    TenantSerializer,
    TournamentMatchSerializer,
    TournamentSerializer,
    TournamentTeamSerializer,
    UserTenantSerializer,
    TeamSeasonSerializer,
    TeamSquadSerializer,
    TeamStaffSerializer,
    TeamStatSerializer,
    TeamRankingSerializer,
    TeamSponsorshipSerializer,
    TeamAchievementSerializer,
    TeamTransferSerializer,
    TeamDocumentSerializer,
    TournamentStageSerializer,
    TournamentStageInstanceSerializer,
    TournamentGroupSerializer,
    TournamentPlayerSerializer,
    TournamentPointsTableSerializer,
    TournamentOfficialSerializer,
    TournamentSponsorSerializer,
    TournamentAwardSerializer,
    TournamentMediaSerializer,
)
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
    TournamentMatch,
    TournamentTeam,
    TournamentStage,
    TournamentStageInstance,
    TournamentGroup,
    TournamentPlayer,
    TournamentPointsTable,
    TournamentOfficial,
    TournamentSponsor,
    TournamentAward,
    TournamentMedia,
)


def tenant_ids_for_user(user):
    if user.is_superuser or user.user_type == user.UserType.SUPER_ADMIN:
        return None

    return list(
        UserTenant.objects.filter(user=user, is_active=True, tenant__is_deleted=False)
        .values_list('tenant_id', flat=True)
    )


def scoped_to_user_tenants(queryset, user, tenant_field='tenant_id'):
    tenant_ids = tenant_ids_for_user(user)
    if tenant_ids is None:
        return queryset
    if not tenant_ids:
        return queryset.none()
    return queryset.filter(**{f'{tenant_field}__in': tenant_ids})


def user_can_access_tenant(user, tenant):
    if not tenant:
        return False
    tenant_ids = tenant_ids_for_user(user)
    if tenant_ids is None:
        return True
    return tenant.id in tenant_ids


class TenantOwnedWriteMixin:
    def perform_create(self, serializer):
        tenant = serializer.validated_data.get('tenant')
        if not user_can_access_tenant(self.request.user, tenant):
            raise PermissionDenied('You do not have access to this tenant.')
        serializer.save()

    def perform_update(self, serializer):
        tenant = serializer.validated_data.get('tenant', getattr(serializer.instance, 'tenant', None))
        if not user_can_access_tenant(self.request.user, tenant):
            raise PermissionDenied('You do not have access to this tenant.')
        serializer.save()


class TenantViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ('name', 'domain', 'subdomain')
    ordering_fields = ('name', 'tenant_type', 'created_at')
    ordering = ('name',)

    def get_queryset(self):
        user = self.request.user
        tenant_ids = tenant_ids_for_user(user)
        if tenant_ids is None:
            return Tenant.objects.all()

        return Tenant.objects.filter(id__in=tenant_ids)


class MyTenantMembershipViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserTenantSerializer
    permission_classes = [IsAuthenticated]
    ordering = ('-is_primary', 'joined_at')

    def get_queryset(self):
        return (
            UserTenant.objects.select_related('tenant', 'role')
            .filter(user=self.request.user, is_active=True, tenant__is_deleted=False)
            .order_by('-is_primary', 'joined_at')
        )


class PlayerProfileViewSet(TenantOwnedWriteMixin, viewsets.ModelViewSet):
    serializer_class = PlayerProfileSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ('first_name', 'last_name', 'city', 'state')
    filterset_fields = ('role', 'batting_style', 'bowling_style', 'player_status', 'is_retired')
    ordering_fields = ('first_name', 'last_name', 'created_at')
    ordering = ('first_name', 'last_name')

    def get_queryset(self):
        return scoped_to_user_tenants(PlayerProfile.objects.all(), self.request.user)


class TeamViewSet(TenantOwnedWriteMixin, viewsets.ModelViewSet):
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ('name', 'code', 'short_name', 'city', 'state')
    filterset_fields = ('team_category', 'team_type', 'is_active', 'status')
    ordering_fields = ('name', 'year', 'created_at')
    ordering = ('name',)

    def get_queryset(self):
        queryset = Team.objects.select_related('team_category', 'team_type')
        return scoped_to_user_tenants(queryset, self.request.user)


class TournamentViewSet(TenantOwnedWriteMixin, viewsets.ModelViewSet):
    serializer_class = TournamentSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ('name', 'slug', 'venue', 'city', 'state')
    filterset_fields = ('format', 'season', 'year', 'is_featured', 'status')
    ordering_fields = ('year', 'start_date', 'created_at', 'name')
    ordering = ('-year', '-created_at')

    def get_queryset(self):
        queryset = Tournament.objects.select_related('format')
        return scoped_to_user_tenants(queryset, self.request.user)


class TournamentTeamViewSet(viewsets.ModelViewSet):
    serializer_class = TournamentTeamSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ('tournament', 'team', 'group', 'is_verified')
    ordering_fields = ('registration_date', 'seed')
    ordering = ('seed', 'registration_date')

    def get_queryset(self):
        queryset = TournamentTeam.objects.select_related('tournament', 'team', 'group')
        return scoped_to_user_tenants(queryset, self.request.user, tenant_field='tournament__tenant_id')

    def perform_create(self, serializer):
        tournament = serializer.validated_data.get('tournament')
        if not user_can_access_tenant(self.request.user, tournament.tenant):
            raise PermissionDenied('You do not have access to this tournament tenant.')
        serializer.save()

    def perform_update(self, serializer):
        tournament = serializer.validated_data.get(
            'tournament',
            getattr(serializer.instance, 'tournament', None),
        )
        if not user_can_access_tenant(self.request.user, tournament.tenant):
            raise PermissionDenied('You do not have access to this tournament tenant.')
        serializer.save()


class TournamentMatchViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TournamentMatchSerializer
    permission_classes = [IsAuthenticatedReadOnly]
    search_fields = ('tournament__name', 'venue', 'ground')
    filterset_fields = ('tournament', 'group', 'result_type', 'is_completed', 'status')
    ordering_fields = ('match_date', 'match_number', 'created_at')
    ordering = ('match_date', 'match_number')

    def get_queryset(self):
        queryset = TournamentMatch.objects.select_related(
            'tournament',
            'home_team__team',
            'away_team__team',
            'winner__team',
        )
        return scoped_to_user_tenants(queryset, self.request.user, tenant_field='tournament__tenant_id')


class PlayerSubEntityViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        player = serializer.validated_data.get('player')
        if player and not user_can_access_tenant(self.request.user, player.tenant):
            raise PermissionDenied("You do not have access to this player's tenant.")
        serializer.save()

    def perform_update(self, serializer):
        player = serializer.validated_data.get('player', getattr(serializer.instance, 'player', None))
        if player and not user_can_access_tenant(self.request.user, player.tenant):
            raise PermissionDenied("You do not have access to this player's tenant.")
        serializer.save()


class PlayerBattingSkillViewSet(PlayerSubEntityViewSet):
    serializer_class = PlayerBattingSkillSerializer
    queryset = PlayerBattingSkill.objects.all()

    def get_queryset(self):
        return scoped_to_user_tenants(self.queryset.select_related('player'), self.request.user, tenant_field='player__tenant_id')


class PlayerBowlingSkillViewSet(PlayerSubEntityViewSet):
    serializer_class = PlayerBowlingSkillSerializer
    queryset = PlayerBowlingSkill.objects.all()

    def get_queryset(self):
        return scoped_to_user_tenants(self.queryset.select_related('player'), self.request.user, tenant_field='player__tenant_id')


class PlayerFieldingSkillViewSet(PlayerSubEntityViewSet):
    serializer_class = PlayerFieldingSkillSerializer
    queryset = PlayerFieldingSkill.objects.all()

    def get_queryset(self):
        return scoped_to_user_tenants(self.queryset.select_related('player'), self.request.user, tenant_field='player__tenant_id')


class PlayerContractViewSet(PlayerSubEntityViewSet):
    serializer_class = PlayerContractSerializer
    queryset = PlayerContract.objects.all()

    def get_queryset(self):
        return scoped_to_user_tenants(self.queryset.select_related('player', 'team'), self.request.user, tenant_field='player__tenant_id')


class PlayerTransferViewSet(PlayerSubEntityViewSet):
    serializer_class = PlayerTransferSerializer
    queryset = PlayerTransfer.objects.all()

    def get_queryset(self):
        return scoped_to_user_tenants(self.queryset.select_related('player', 'from_team', 'to_team'), self.request.user, tenant_field='player__tenant_id')


class PlayerInjuryViewSet(PlayerSubEntityViewSet):
    serializer_class = PlayerInjurySerializer
    queryset = PlayerInjury.objects.all()

    def get_queryset(self):
        return scoped_to_user_tenants(self.queryset.select_related('player'), self.request.user, tenant_field='player__tenant_id')


class PlayerAchievementViewSet(PlayerSubEntityViewSet):
    serializer_class = PlayerAchievementSerializer
    queryset = PlayerAchievement.objects.all()

    def get_queryset(self):
        return scoped_to_user_tenants(self.queryset.select_related('player', 'tournament'), self.request.user, tenant_field='player__tenant_id')


class PlayerCareerStatsViewSet(PlayerSubEntityViewSet):
    serializer_class = PlayerCareerStatsSerializer
    queryset = PlayerCareerStats.objects.all()

    def get_queryset(self):
        return scoped_to_user_tenants(self.queryset.select_related('player'), self.request.user, tenant_field='player__tenant_id')


# --- Team Sub-Entity ViewSets ---

class TeamSeasonViewSet(viewsets.ModelViewSet):
    serializer_class = TeamSeasonSerializer
    queryset = TeamSeason.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return scoped_to_user_tenants(self.queryset.select_related('team', 'captain', 'vice_captain'), self.request.user, tenant_field='team__tenant_id')

    def perform_create(self, serializer):
        team = serializer.validated_data.get('team')
        if team and not user_can_access_tenant(self.request.user, team.tenant):
            raise PermissionDenied("You do not have access to this team's tenant.")
        serializer.save()

    def perform_update(self, serializer):
        team = serializer.validated_data.get('team', getattr(serializer.instance, 'team', None))
        if team and not user_can_access_tenant(self.request.user, team.tenant):
            raise PermissionDenied("You do not have access to this team's tenant.")
        serializer.save()


class TeamSquadViewSet(viewsets.ModelViewSet):
    serializer_class = TeamSquadSerializer
    queryset = TeamSquad.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return scoped_to_user_tenants(self.queryset.select_related('team_season__team', 'player'), self.request.user, tenant_field='team_season__team__tenant_id')

    def perform_create(self, serializer):
        team_season = serializer.validated_data.get('team_season')
        if team_season and not user_can_access_tenant(self.request.user, team_season.team.tenant):
            raise PermissionDenied("You do not have access to this team's tenant.")
        serializer.save()

    def perform_update(self, serializer):
        team_season = serializer.validated_data.get('team_season', getattr(serializer.instance, 'team_season', None))
        if team_season and not user_can_access_tenant(self.request.user, team_season.team.tenant):
            raise PermissionDenied("You do not have access to this team's tenant.")
        serializer.save()


class TeamStaffViewSet(viewsets.ModelViewSet):
    serializer_class = TeamStaffSerializer
    queryset = TeamStaff.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return scoped_to_user_tenants(self.queryset.select_related('team_season__team'), self.request.user, tenant_field='team_season__team__tenant_id')

    def perform_create(self, serializer):
        team_season = serializer.validated_data.get('team_season')
        if team_season and not user_can_access_tenant(self.request.user, team_season.team.tenant):
            raise PermissionDenied("You do not have access to this team's tenant.")
        serializer.save()

    def perform_update(self, serializer):
        team_season = serializer.validated_data.get('team_season', getattr(serializer.instance, 'team_season', None))
        if team_season and not user_can_access_tenant(self.request.user, team_season.team.tenant):
            raise PermissionDenied("You do not have access to this team's tenant.")
        serializer.save()


class TeamStatViewSet(viewsets.ModelViewSet):
    serializer_class = TeamStatSerializer
    queryset = TeamStat.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return scoped_to_user_tenants(self.queryset.select_related('team', 'team_season', 'tournament'), self.request.user, tenant_field='team__tenant_id')

    def perform_create(self, serializer):
        team = serializer.validated_data.get('team')
        if team and not user_can_access_tenant(self.request.user, team.tenant):
            raise PermissionDenied("You do not have access to this team's tenant.")
        serializer.save()

    def perform_update(self, serializer):
        team = serializer.validated_data.get('team', getattr(serializer.instance, 'team', None))
        if team and not user_can_access_tenant(self.request.user, team.tenant):
            raise PermissionDenied("You do not have access to this team's tenant.")
        serializer.save()


class TeamRankingViewSet(viewsets.ModelViewSet):
    serializer_class = TeamRankingSerializer
    queryset = TeamRanking.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return scoped_to_user_tenants(self.queryset.select_related('team'), self.request.user, tenant_field='team__tenant_id')

    def perform_create(self, serializer):
        team = serializer.validated_data.get('team')
        if team and not user_can_access_tenant(self.request.user, team.tenant):
            raise PermissionDenied("You do not have access to this team's tenant.")
        serializer.save()

    def perform_update(self, serializer):
        team = serializer.validated_data.get('team', getattr(serializer.instance, 'team', None))
        if team and not user_can_access_tenant(self.request.user, team.tenant):
            raise PermissionDenied("You do not have access to this team's tenant.")
        serializer.save()


class TeamSponsorshipViewSet(viewsets.ModelViewSet):
    serializer_class = TeamSponsorshipSerializer
    queryset = TeamSponsorship.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return scoped_to_user_tenants(self.queryset.select_related('team'), self.request.user, tenant_field='team__tenant_id')

    def perform_create(self, serializer):
        team = serializer.validated_data.get('team')
        if team and not user_can_access_tenant(self.request.user, team.tenant):
            raise PermissionDenied("You do not have access to this team's tenant.")
        serializer.save()

    def perform_update(self, serializer):
        team = serializer.validated_data.get('team', getattr(serializer.instance, 'team', None))
        if team and not user_can_access_tenant(self.request.user, team.tenant):
            raise PermissionDenied("You do not have access to this team's tenant.")
        serializer.save()


class TeamAchievementViewSet(viewsets.ModelViewSet):
    serializer_class = TeamAchievementSerializer
    queryset = TeamAchievement.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return scoped_to_user_tenants(self.queryset.select_related('team'), self.request.user, tenant_field='team__tenant_id')

    def perform_create(self, serializer):
        team = serializer.validated_data.get('team')
        if team and not user_can_access_tenant(self.request.user, team.tenant):
            raise PermissionDenied("You do not have access to this team's tenant.")
        serializer.save()

    def perform_update(self, serializer):
        team = serializer.validated_data.get('team', getattr(serializer.instance, 'team', None))
        if team and not user_can_access_tenant(self.request.user, team.tenant):
            raise PermissionDenied("You do not have access to this team's tenant.")
        serializer.save()


class TeamDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = TeamDocumentSerializer
    queryset = TeamDocument.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return scoped_to_user_tenants(self.queryset.select_related('team'), self.request.user, tenant_field='team__tenant_id')

    def perform_create(self, serializer):
        team = serializer.validated_data.get('team')
        if team and not user_can_access_tenant(self.request.user, team.tenant):
            raise PermissionDenied("You do not have access to this team's tenant.")
        serializer.save()

    def perform_update(self, serializer):
        team = serializer.validated_data.get('team', getattr(serializer.instance, 'team', None))
        if team and not user_can_access_tenant(self.request.user, team.tenant):
            raise PermissionDenied("You do not have access to this team's tenant.")
        serializer.save()


# --- Tournament Sub-Entity ViewSets ---

class TournamentStageViewSet(viewsets.ModelViewSet):
    serializer_class = TournamentStageSerializer
    queryset = TournamentStage.objects.all()
    permission_classes = [IsAuthenticated]

    # TournamentStage has no direct link to Tournament, it is linked via format.
    # We don't filter listing since it is a static configuration entity linked to format.
    # However, let's allow it for simplicity.
    def get_queryset(self):
        return self.queryset


class TournamentStageInstanceViewSet(viewsets.ModelViewSet):
    serializer_class = TournamentStageInstanceSerializer
    queryset = TournamentStageInstance.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return scoped_to_user_tenants(self.queryset.select_related('tournament', 'stage'), self.request.user, tenant_field='tournament__tenant_id')

    def perform_create(self, serializer):
        tournament = serializer.validated_data.get('tournament')
        if tournament and not user_can_access_tenant(self.request.user, tournament.tenant):
            raise PermissionDenied("You do not have access to this tournament's tenant.")
        serializer.save()

    def perform_update(self, serializer):
        tournament = serializer.validated_data.get('tournament', getattr(serializer.instance, 'tournament', None))
        if tournament and not user_can_access_tenant(self.request.user, tournament.tenant):
            raise PermissionDenied("You do not have access to this tournament's tenant.")
        serializer.save()


class TournamentGroupViewSet(viewsets.ModelViewSet):
    serializer_class = TournamentGroupSerializer
    queryset = TournamentGroup.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return scoped_to_user_tenants(self.queryset.select_related('stage_instance__tournament'), self.request.user, tenant_field='stage_instance__tournament__tenant_id')

    def perform_create(self, serializer):
        stage_instance = serializer.validated_data.get('stage_instance')
        if stage_instance and not user_can_access_tenant(self.request.user, stage_instance.tournament.tenant):
            raise PermissionDenied("You do not have access to this tournament's tenant.")
        serializer.save()

    def perform_update(self, serializer):
        stage_instance = serializer.validated_data.get('stage_instance', getattr(serializer.instance, 'stage_instance', None))
        if stage_instance and not user_can_access_tenant(self.request.user, stage_instance.tournament.tenant):
            raise PermissionDenied("You do not have access to this tournament's tenant.")
        serializer.save()


class TournamentPlayerViewSet(viewsets.ModelViewSet):
    serializer_class = TournamentPlayerSerializer
    queryset = TournamentPlayer.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return scoped_to_user_tenants(self.queryset.select_related('tournament_team__tournament', 'player'), self.request.user, tenant_field='tournament_team__tournament__tenant_id')

    def perform_create(self, serializer):
        tournament_team = serializer.validated_data.get('tournament_team')
        if tournament_team and not user_can_access_tenant(self.request.user, tournament_team.tournament.tenant):
            raise PermissionDenied("You do not have access to this tournament's tenant.")
        serializer.save()

    def perform_update(self, serializer):
        tournament_team = serializer.validated_data.get('tournament_team', getattr(serializer.instance, 'tournament_team', None))
        if tournament_team and not user_can_access_tenant(self.request.user, tournament_team.tournament.tenant):
            raise PermissionDenied("You do not have access to this tournament's tenant.")
        serializer.save()


class TournamentPointsTableViewSet(viewsets.ModelViewSet):
    serializer_class = TournamentPointsTableSerializer
    queryset = TournamentPointsTable.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return scoped_to_user_tenants(self.queryset.select_related('group__stage_instance__tournament', 'team__team'), self.request.user, tenant_field='group__stage_instance__tournament__tenant_id')

    def perform_create(self, serializer):
        group = serializer.validated_data.get('group')
        if group and not user_can_access_tenant(self.request.user, group.stage_instance.tournament.tenant):
            raise PermissionDenied("You do not have access to this tournament's tenant.")
        serializer.save()

    def perform_update(self, serializer):
        group = serializer.validated_data.get('group', getattr(serializer.instance, 'group', None))
        if group and not user_can_access_tenant(self.request.user, group.stage_instance.tournament.tenant):
            raise PermissionDenied("You do not have access to this tournament's tenant.")
        serializer.save()


class TournamentOfficialViewSet(viewsets.ModelViewSet):
    serializer_class = TournamentOfficialSerializer
    queryset = TournamentOfficial.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return scoped_to_user_tenants(self.queryset.select_related('tournament', 'official'), self.request.user, tenant_field='tournament__tenant_id')

    def perform_create(self, serializer):
        tournament = serializer.validated_data.get('tournament')
        if tournament and not user_can_access_tenant(self.request.user, tournament.tenant):
            raise PermissionDenied("You do not have access to this tournament's tenant.")
        serializer.save()

    def perform_update(self, serializer):
        tournament = serializer.validated_data.get('tournament', getattr(serializer.instance, 'tournament', None))
        if tournament and not user_can_access_tenant(self.request.user, tournament.tenant):
            raise PermissionDenied("You do not have access to this tournament's tenant.")
        serializer.save()


class TournamentSponsorViewSet(viewsets.ModelViewSet):
    serializer_class = TournamentSponsorSerializer
    queryset = TournamentSponsor.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return scoped_to_user_tenants(self.queryset.select_related('tournament'), self.request.user, tenant_field='tournament__tenant_id')

    def perform_create(self, serializer):
        tournament = serializer.validated_data.get('tournament')
        if tournament and not user_can_access_tenant(self.request.user, tournament.tenant):
            raise PermissionDenied("You do not have access to this tournament's tenant.")
        serializer.save()

    def perform_update(self, serializer):
        tournament = serializer.validated_data.get('tournament', getattr(serializer.instance, 'tournament', None))
        if tournament and not user_can_access_tenant(self.request.user, tournament.tenant):
            raise PermissionDenied("You do not have access to this tournament's tenant.")
        serializer.save()


class TournamentAwardViewSet(viewsets.ModelViewSet):
    serializer_class = TournamentAwardSerializer
    queryset = TournamentAward.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return scoped_to_user_tenants(self.queryset.select_related('tournament', 'winner'), self.request.user, tenant_field='tournament__tenant_id')

    def perform_create(self, serializer):
        tournament = serializer.validated_data.get('tournament')
        if tournament and not user_can_access_tenant(self.request.user, tournament.tenant):
            raise PermissionDenied("You do not have access to this tournament's tenant.")
        serializer.save()

    def perform_update(self, serializer):
        tournament = serializer.validated_data.get('tournament', getattr(serializer.instance, 'tournament', None))
        if tournament and not user_can_access_tenant(self.request.user, tournament.tenant):
            raise PermissionDenied("You do not have access to this tournament's tenant.")
        serializer.save()


class TournamentMediaViewSet(viewsets.ModelViewSet):
    serializer_class = TournamentMediaSerializer
    queryset = TournamentMedia.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return scoped_to_user_tenants(self.queryset.select_related('tournament'), self.request.user, tenant_field='tournament__tenant_id')

    def perform_create(self, serializer):
        tournament = serializer.validated_data.get('tournament')
        if tournament and not user_can_access_tenant(self.request.user, tournament.tenant):
            raise PermissionDenied("You do not have access to this tournament's tenant.")
        serializer.save()

    def perform_update(self, serializer):
        tournament = serializer.validated_data.get('tournament', getattr(serializer.instance, 'tournament', None))
        if tournament and not user_can_access_tenant(self.request.user, tournament.tenant):
            raise PermissionDenied("You do not have access to this tournament's tenant.")
        serializer.save()


