from django.contrib import admin
from .models import Contact, Interaction, Stage, Application


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone', 'position', 'created_at')
    search_fields = ('first_name', 'last_name', 'email')
    list_filter = ('created_at',)


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ('application', 'contact', 'interaction_type', 'subject', 'interaction_date')
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

