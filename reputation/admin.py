from django.contrib import admin
from .models import ReputationEvent, Badge, UserBadge


@admin.register(ReputationEvent)
class ReputationEventAdmin(admin.ModelAdmin):
    list_display = ('user', 'event_type', 'delta', 'description', 'created_at')
    list_filter = ('event_type',)
    search_fields = ('user__username', 'description')
    ordering = ('-created_at',)


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'trigger', 'icon')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', 'awarded_at')
    list_filter = ('badge',)
    search_fields = ('user__username',)
    ordering = ('-awarded_at',)
