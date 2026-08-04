from django.contrib import admin
from .models import Problem, Tag, ProblemView, ProblemRevision, Report


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'usage_count')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('-usage_count',)


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'difficulty', 'view_count', 'is_deleted', 'created_at')
    list_filter = ('difficulty', 'is_deleted', 'language')
    search_fields = ('title', 'user__username')
    readonly_fields = ('view_count', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    actions = ['soft_delete_selected']

    def soft_delete_selected(self, request, queryset):
        queryset.update(is_deleted=True)
    soft_delete_selected.short_description = 'Soft-delete selected problems'


@admin.register(ProblemRevision)
class ProblemRevisionAdmin(admin.ModelAdmin):
    list_display = ('problem', 'editor', 'version', 'created_at')
    readonly_fields = ('problem', 'editor', 'title', 'description', 'difficulty', 'version', 'created_at')
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ProblemView)
class ProblemViewAdmin(admin.ModelAdmin):
    list_display = ('problem', 'user', 'ip_address', 'viewed_at')
    readonly_fields = ('problem', 'user', 'ip_address', 'viewed_at')
    ordering = ('-viewed_at',)

    def has_add_permission(self, request):
        return False


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('reporter', 'content_type', 'object_id', 'reason', 'is_resolved', 'created_at')
    list_filter = ('content_type', 'reason', 'is_resolved')
    search_fields = ('reporter__username',)
    actions = ['mark_resolved']

    def mark_resolved(self, request, queryset):
        queryset.update(is_resolved=True)
    mark_resolved.short_description = 'Mark selected reports as resolved'
