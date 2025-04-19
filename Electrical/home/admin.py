from django.contrib import admin
from .models import UserProfile, Appliance, EnergyConsumption, Achievement

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'monthly_limit', 'season', 'achievement_points')
    search_fields = ('user__username',)

@admin.register(Appliance)
class ApplianceAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'power_consumption', 'daily_usage', 'is_active')
    list_filter = ('is_active', 'user')
    search_fields = ('name', 'user__username')

@admin.register(EnergyConsumption)
class EnergyConsumptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'total_consumption', 'predicted_consumption', 'is_limit_reached')
    list_filter = ('is_limit_reached', 'date')
    search_fields = ('user__username',)

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'badge_level', 'date_earned')
    list_filter = ('badge_level', 'date_earned')
    search_fields = ('title', 'user__username')
