from django.contrib import admin
from .models import Customer, Contact, Interaction, Stage, Application


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'company', 'phone', 'created_at')
    search_fields = ('name', 'email', 'company')
    list_filter = ('created_at',)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone', 'position', 'created_at')
    search_fields = ('first_name', 'last_name', 'email')
    list_filter = ('created_at',)


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ('application', 'customer', 'contact', 'interaction_type', 'direction', 'subject', 'interaction_date')
    search_fields = ('application__company_name', 'customer__name', 'subject')
    list_filter = ('interaction_type', 'direction', 'interaction_date')

@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'created_at')
    ordering = ('order',)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'email', 'where_applied', 'stage', 'applied_date', 'created_at')
    search_fields = ('company_name', 'email', 'where_applied')
    list_filter = ('stage', 'where_applied', 'created_at')

