from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'user', 'ip_address', 'resource_type', 'resource_id', 'timestamp')
    list_filter = ('event_type',)
    search_fields = ('user__username', 'ip_address', 'description')
    readonly_fields = ('user', 'event_type', 'resource_type', 'resource_id',
                       'ip_address', 'user_agent', 'description', 'timestamp')
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
