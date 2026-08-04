from django.contrib import admin
from .models import Solution, Vote, Comment, SolutionRevision


@admin.register(Solution)
class SolutionAdmin(admin.ModelAdmin):
    list_display = ('user', 'problem', 'language', 'is_accepted', 'is_deleted', 'created_at')
    list_filter = ('is_accepted', 'is_deleted', 'language')
    search_fields = ('user__username', 'problem__title')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'solution', 'created_at')
    readonly_fields = ('user', 'solution', 'created_at')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'solution', 'is_edited', 'is_deleted', 'created_at')
    list_filter = ('is_deleted', 'is_edited')
    search_fields = ('user__username', 'text')
    readonly_fields = ('created_at', 'edited_at')


@admin.register(SolutionRevision)
class SolutionRevisionAdmin(admin.ModelAdmin):
    list_display = ('solution', 'editor', 'version', 'language', 'created_at')
    readonly_fields = ('solution', 'editor', 'explanation', 'code', 'language', 'version', 'created_at')
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
