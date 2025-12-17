from django.contrib import admin
from .models import Interaction, Stage, Application, EmailAccount, AutoDetectedApplication


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ('application', 'interaction_type', 'subject', 'interaction_date')
    search_fields = ('application__company_name', 'subject')
    list_filter = ('interaction_type', 'interaction_date')

@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'created_at')
    ordering = ('order',)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'position', 'stage', 'where_applied', 'salary_range', 'applied_date', 'created_at')
    search_fields = ('company_name', 'position', 'email', 'stack')
    list_filter = ('stage', 'where_applied', 'created_at')


@admin.register(EmailAccount)
class EmailAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'provider', 'is_active', 'last_sync_at', 'created_at')
    search_fields = ('email', 'user__username')
    list_filter = ('provider', 'is_active', 'created_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AutoDetectedApplication)
class AutoDetectedApplicationAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'position', 'status', 'confidence_score', 'detected_at', 'reviewed_at')
    search_fields = ('company_name', 'position', 'email_message_id')
    list_filter = ('status', 'confidence_score', 'detected_at')
    readonly_fields = ('detected_at', 'reviewed_at')
    date_hierarchy = 'detected_at'

