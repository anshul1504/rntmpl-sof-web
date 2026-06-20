"""
Management command to seed demo data for development and client walkthroughs.
Creates a superuser, tenants, roles, tournaments, teams, and players.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

from apps.accounts.models import Tenant, UserTenant, Role
from apps.players.models import PlayerProfile, PlayerCareerStats, PlayerRole, BattingStyle, BowlingStyle
from apps.teams.models import Team, TeamCategory, TeamType, TeamSeason
from apps.tournaments.models import (
    Tournament, TournamentFormat, TournamentStage, TournamentStageInstance,
    TournamentGroup, TournamentTeam, TournamentMatch,
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed demo data for development and client walkthroughs'

    def handle(self, *args, **options):
        self.stdout.write('Seeding demo data...')

        # ── Superuser ──
        if not User.objects.filter(email='admin@rntmpl.com').exists():
            admin = User.objects.create_superuser(
                email='admin@rntmpl.com',
                password='admin123',
                full_name='Platform Admin',
                user_type=User.UserType.SUPER_ADMIN,
                is_verified=True,
            )
            self.stdout.write(self.style.SUCCESS(f'Created superuser: admin@rntmpl.com / admin123'))
        else:
            admin = User.objects.get(email='admin@rntmpl.com')

        # ── Demo Users ──
        demo_users_data = [
            ('player@demo.com', 'player123', 'Virat Sharma', User.UserType.PLAYER),
            ('scorer@demo.com', 'scorer123', 'Anil Scorer', User.UserType.SCORER),
            ('manager@demo.com', 'manager123', 'Rahul Manager', User.UserType.TEAM_MANAGER),
            ('director@demo.com', 'director123', 'Suresh Director', User.UserType.TOURNAMENT_DIRECTOR),
        ]
        for email, password, name, user_type in demo_users_data:
            if not User.objects.filter(email=email).exists():
                User.objects.create_user(
                    email=email, password=password,
                    full_name=name, user_type=user_type, is_verified=True,
                )
                self.stdout.write(f'  Created user: {email} / {password}')

        # ── Tenant ──
        tenant, created = Tenant.objects.get_or_create(
            name='RNT Premier League',
            defaults={
                'tenant_type': Tenant.TenantType.LEAGUE,
                'subdomain': 'rntmpl',
                'email': 'info@rntmpl.com',
                'phone': '+91-9876543210',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'primary_color': '#0f5132',
                'secondary_color': '#22c55e',
                'verified': True,
                'subscription_plan': 'professional',
            },
        )
        if created:
            self.stdout.write(f'  Created tenant: {tenant.name}')

        # Link admin to tenant
        UserTenant.objects.get_or_create(
            user=admin, tenant=tenant,
            defaults={'is_primary': True, 'is_active': True},
        )

        # ── Roles ──
        Role.objects.get_or_create(
            tenant=tenant, code='TENANT_ADMIN',
            defaults={'name': 'Tenant Admin', 'category': Role.RoleCategory.TENANT, 'is_system': True},
        )

        # ── Tournament Formats ──
        fmt, _ = TournamentFormat.objects.get_or_create(
            code='T20_LEAGUE',
            defaults={
                'name': 'T20 League',
                'max_teams': 10,
                'max_players_per_team': 18,
                'points_for_win': 2,
                'points_for_loss': 0,
                'has_group_stage': False,
                'has_knockout_stage': True,
            },
        )

        # ── Tournament Stages ──
        league_stage, _ = TournamentStage.objects.get_or_create(
            name='League Stage', format=fmt,
            defaults={
                'sequence': 1,
                'is_group_stage': True,
                'number_of_teams': 6,
                'number_of_groups': 1,
                'teams_qualify_per_group': 4,
            },
        )
        semis_stage, _ = TournamentStage.objects.get_or_create(
            name='Semi Finals', format=fmt,
            defaults={
                'sequence': 2,
                'is_knockout_stage': True,
                'number_of_teams': 4,
            },
        )
        final_stage, _ = TournamentStage.objects.get_or_create(
            name='Final', format=fmt,
            defaults={
                'sequence': 3,
                'is_knockout_stage': True,
                'number_of_teams': 2,
            },
        )

        # ── Tournament ──
        tournament, _ = Tournament.objects.get_or_create(
            name='RNT MPL Season 1',
            defaults={
                'tenant': tenant,
                'slug': 'rnt-mpl-season-1',
                'format': fmt,
                'season': 'Season 1',
                'year': 2026,
                'start_date': timezone.now().date(),
                'end_date': timezone.now().date() + timezone.timedelta(days=60),
                'venue': 'RNT Cricket Ground',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'total_teams': 6,
                'total_matches': 31,
                'is_featured': True,
                'entry_fee': 50000,
                'prize_money': 500000,
                'status': Tournament.Status.ACTIVE,
            },
        )

        # ── Tournament Stage Instances ──
        tsi_league, _ = TournamentStageInstance.objects.get_or_create(
            tournament=tournament, stage=league_stage,
            defaults={'name': 'League Stage', 'sequence': 1},
        )
        tsi_semis, _ = TournamentStageInstance.objects.get_or_create(
            tournament=tournament, stage=semis_stage,
            defaults={'name': 'Semi Finals', 'sequence': 2},
        )
        tsi_final, _ = TournamentStageInstance.objects.get_or_create(
            tournament=tournament, stage=final_stage,
            defaults={'name': 'Final', 'sequence': 3},
        )

        # ── Groups ──
        group_a, _ = TournamentGroup.objects.get_or_create(
            stage_instance=tsi_league, name='Points Table',
            defaults={'code': 'A', 'sequence': 1},
        )

        # ── Team Categories & Types ──
        cat_senior, _ = TeamCategory.objects.get_or_create(name='Senior', defaults={'description': 'Senior division'})
        type_club, _ = TeamType.objects.get_or_create(name='Club', defaults={'description': 'Club team'})

        # ── Teams ──
        teams_data = [
            ('RNT Royals', 'ROY', '#e11d48', '#fecdd3'),
            ('MPL Strikers', 'STR', '#2563eb', '#bfdbfe'),
            ('City Titans', 'TIT', '#7c3aed', '#ddd6fe'),
            ('Mountain Eagles', 'EAG', '#059669', '#a7f3d0'),
            ('Desert Hawks', 'HAW', '#d97706', '#fde68a'),
            ('Coastal Warriors', 'WAR', '#0891b2', '#cffafe'),
        ]
        team_objs = []
        for name, code, primary, secondary in teams_data:
            team, _ = Team.objects.get_or_create(
                name=name, tenant=tenant,
                defaults={
                    'code': code,
                    'short_name': code,
                    'team_category': cat_senior,
                    'team_type': type_club,
                    'city': 'Mumbai',
                    'state': 'Maharashtra',
                    'jersey_color_primary': primary,
                    'jersey_color_secondary': secondary,
                    'is_active': True,
                    'home_ground': f'{name} Stadium',
                },
            )
            team_objs.append(team)

            # Team season
            TeamSeason.objects.get_or_create(
                team=team, year=2026, season='ALL_YEAR',
                defaults={'is_active': True, 'squad_size': 0},
            )

            # Tournament registration
            TournamentTeam.objects.get_or_create(
                tournament=tournament, team=team,
                defaults={'group': group_a, 'is_verified': True, 'seed': team_objs.index(team) + 1},
            )

        # ── Players ──
        players_data = [
            ('Virat', 'Sharma', PlayerRole.BATTER, BattingStyle.RIGHT_HAND, True, False, 18),
            ('Rohit', 'Singh', PlayerRole.BATTER, BattingStyle.RIGHT_HAND, True, False, 45),
            ('Jasprit', 'Bumrah', PlayerRole.BOWLER, BattingStyle.RIGHT_HAND, False, True, 93),
            ('Ravindra', 'Jadeja', PlayerRole.ALL_ROUNDER, BattingStyle.LEFT_HAND, False, True, 8),
            ('MS', 'Dhoni', PlayerRole.WICKET_KEEPER, BattingStyle.RIGHT_HAND, True, False, 7),
            ('Surya', 'Yadav', PlayerRole.BATTER, BattingStyle.RIGHT_HAND, True, False, 63),
            ('Rishabh', 'Pant', PlayerRole.BATTER_WK, BattingStyle.LEFT_HAND, True, False, 17),
            ('Hardik', 'Pandya', PlayerRole.BATTING_AR, BattingStyle.RIGHT_HAND, False, True, 33),
            ('Bhuvneshwar', 'Kumar', PlayerRole.BOWLER, BattingStyle.RIGHT_HAND, False, True, 15),
            ('KL', 'Rahul', PlayerRole.BATTER_WK, BattingStyle.RIGHT_HAND, True, False, 1),
        ]

        for first, last, role, bat_style, is_bat, is_bowl, jersey in players_data:
            player, created = PlayerProfile.objects.get_or_create(
                first_name=first, last_name=last, tenant=tenant,
                defaults={
                    'role': role,
                    'batting_style': bat_style,
                    'is_wicket_keeper': role in (PlayerRole.WICKET_KEEPER, PlayerRole.BATTER_WK),
                    'is_bowler': is_bowl,
                    'jersey_number': jersey,
                    'gender': 'MALE',
                    'nationality': 'India',
                    'city': 'Mumbai',
                    'state': 'Maharashtra',
                    'player_status': 'ACTIVE',
                },
            )
            if created:
                PlayerCareerStats.objects.get_or_create(player=player)

        # ── Tournament Matches ──
        team_ids = list(TournamentTeam.objects.filter(tournament=tournament).values_list('id', flat=True))
        for i in range(0, len(team_ids), 2):
            if i + 1 < len(team_ids):
                TournamentMatch.objects.get_or_create(
                    tournament=tournament,
                    match_number=(i // 2) + 1,
                    home_team_id=team_ids[i],
                    away_team_id=team_ids[i + 1],
                    stage_instance=tsi_league,
                    group=group_a,
                    defaults={
                        'match_date': timezone.now() + timezone.timedelta(days=(i // 2) + 1, hours=15),
                        'venue': f'{team_objs[i].name} Stadium' if i < len(team_objs) else 'RNT Ground',
                        'ground': 'Main Pitch',
                    },
                )

        self.stdout.write(self.style.SUCCESS(
            f'\nSeed complete!'
            f'\n  Admin: admin@rntmpl.com / admin123'
            f'\n  Tenant: {tenant.name}'
            f'\n  Tournament: {tournament.name}'
            f'\n  Teams: {len(team_objs)}'
            f'\n  Players: {PlayerProfile.objects.count()}'
            f'\n  Matches: {TournamentMatch.objects.count()}'
        ))
