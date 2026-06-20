from django.contrib import admin

from apps.players.models import (
    PlayerAchievement,
    PlayerBattingSkill,
    PlayerBowlingSkill,
    PlayerCareerStats,
    PlayerContract,
    PlayerFieldingSkill,
    PlayerInjury,
    PlayerProfile,
    PlayerTransfer,
)


@admin.register(PlayerProfile)
class PlayerProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'role', 'batting_style', 'bowling_style', 'player_status', 'is_retired')
    list_filter = ('role', 'batting_style', 'bowling_style', 'player_status', 'is_retired')
    search_fields = ('first_name', 'last_name', 'email', 'phone')


admin.site.register(PlayerBattingSkill)
admin.site.register(PlayerBowlingSkill)
admin.site.register(PlayerFieldingSkill)
admin.site.register(PlayerContract)
admin.site.register(PlayerTransfer)
admin.site.register(PlayerInjury)
admin.site.register(PlayerAchievement)
admin.site.register(PlayerCareerStats)
