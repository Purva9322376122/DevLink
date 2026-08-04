from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'actor', 'verb', 'is_read', 'created_at')
    list_filter = ('verb', 'is_read')
    search_fields = ('recipient__username', 'actor__username', 'preview')
    readonly_fields = ('recipient', 'actor', 'verb', 'content_type', 'object_id',
                       'target_url', 'preview', 'created_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    actions = ['mark_all_read']

    def mark_all_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_all_read.short_description = 'Mark selected as read'
