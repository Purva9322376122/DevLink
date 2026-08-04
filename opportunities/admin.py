from django.contrib import admin
from .models import Opportunity, Invitation, Application

# Register your models here.

# admin.site.register(Opportunity)




@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "created_at")


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("sender", "receiver", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("sender__username", "receiver__username")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("user", "opportunity", "status", "created_at")