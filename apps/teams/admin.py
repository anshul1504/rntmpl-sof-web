from django.contrib import admin
from .models import (
    Team, TeamCategory, TeamType, TeamSeason, TeamSquad, TeamStaff, TeamStat,
    TeamRanking, TeamSponsorship, TeamAchievement, TeamTransfer, TeamDocument,
)


class TeamSeasonInline(admin.TabularInline):
    model = TeamSeason
    extra = 0
    fields = ('year', 'season', 'captain', 'coach', 'squad_size', 'is_active')
    show_change_link = True


class TeamStatInline(admin.TabularInline):
    model = TeamStat
    extra = 0
    fields = ('context', 'matches_played', 'matches_won', 'matches_lost', 'win_percentage')
    show_change_link = True


class TeamRankingInline(admin.TabularInline):
    model = TeamRanking
    extra = 0
    fields = ('format', 'rank', 'points', 'rating')
    show_change_link = True


class TeamSponsorshipInline(admin.TabularInline):
    model = TeamSponsorship
    extra = 0
    fields = ('sponsor_name', 'sponsorship_type', 'sponsor_logo', 'is_active')
    show_change_link = True


class TeamAchievementInline(admin.TabularInline):
    model = TeamAchievement
    extra = 0
    fields = ('name', 'achievement_type', 'achievement_date', 'tournament')
    show_change_link = True


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'team_category', 'team_type', 'city', 'state', 'is_active')
    list_filter = ('team_category', 'team_type', 'state', 'is_active')
    search_fields = ('name', 'short_name', 'abbreviation', 'code', 'email', 'phone', 'city')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Team Identity', {'fields': ('tenant', 'name', 'code', 'short_name', 'abbreviation', 'description', 'logo')}),
        ('Classification', {'fields': ('team_category', 'team_type', 'founded_date', 'is_active')}),
        ('Team Colours', {'fields': ('jersey_color_primary', 'jersey_color_secondary')}),
        ('Location', {'fields': ('home_ground', 'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country')}),
        ('Contact and Links', {'fields': ('phone', 'email', 'website', 'social_media_links')}),
        ('System', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    inlines = (TeamSeasonInline, TeamStatInline, TeamRankingInline, TeamSponsorshipInline, TeamAchievementInline)


@admin.register(TeamSeason)
class TeamSeasonAdmin(admin.ModelAdmin):
    list_display = ('team', 'year', 'season', 'captain', 'coach', 'squad_size', 'is_active')
    list_filter = ('year', 'season', 'is_active')
    search_fields = ('team__name', 'coach', 'manager')


@admin.register(TeamSquad)
class TeamSquadAdmin(admin.ModelAdmin):
    list_display = ('player', 'team_season', 'role', 'jersey_number', 'is_captain', 'is_active')
    list_filter = ('role', 'is_captain', 'is_vice_captain', 'is_wicket_keeper', 'is_active')
    search_fields = ('player__first_name', 'player__last_name', 'team_season__team__name')


@admin.register(TeamStaff)
class TeamStaffAdmin(admin.ModelAdmin):
    list_display = ('name', 'team_season', 'staff_type', 'experience_years', 'is_active')
    list_filter = ('staff_type', 'is_active')
    search_fields = ('name', 'team_season__team__name', 'contact_email')


admin.site.register(TeamCategory)
admin.site.register(TeamType)
admin.site.register(TeamStat)
admin.site.register(TeamRanking)
admin.site.register(TeamSponsorship)
admin.site.register(TeamAchievement)
admin.site.register(TeamTransfer)
admin.site.register(TeamDocument)
