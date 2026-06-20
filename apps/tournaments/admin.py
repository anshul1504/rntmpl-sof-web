from django.contrib import admin

from apps.tournaments.models import (
    Tournament,
    TournamentAward,
    TournamentFormat,
    TournamentGroup,
    TournamentMatch,
    TournamentMedia,
    TournamentOfficial,
    TournamentPlayer,
    TournamentPointsTable,
    TournamentSponsor,
    TournamentStage,
    TournamentStageInstance,
    TournamentTeam,
    TournamentRule,
    MatchSetup,
    MatchPlayingXI,
    MatchOfficialAssignment,
)


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ('name', 'format', 'season', 'year', 'start_date', 'end_date', 'status', 'is_featured')
    list_filter = ('format', 'season', 'year', 'status', 'is_featured')
    search_fields = ('name', 'slug', 'venue', 'city', 'state')


@admin.register(TournamentMatch)
class TournamentMatchAdmin(admin.ModelAdmin):
    list_display = ('tournament', 'match_number', 'home_team', 'away_team', 'match_date', 'winner', 'is_completed')
    list_filter = ('tournament', 'result_type', 'is_completed')
    search_fields = ('tournament__name', 'venue', 'ground')


admin.site.register(TournamentFormat)
admin.site.register(TournamentStage)
admin.site.register(TournamentStageInstance)
admin.site.register(TournamentGroup)
admin.site.register(TournamentTeam)
admin.site.register(TournamentPlayer)
admin.site.register(TournamentPointsTable)
admin.site.register(TournamentOfficial)
admin.site.register(TournamentSponsor)
admin.site.register(TournamentAward)
admin.site.register(TournamentMedia)
admin.site.register(TournamentRule)
admin.site.register(MatchSetup)
admin.site.register(MatchPlayingXI)
admin.site.register(MatchOfficialAssignment)
