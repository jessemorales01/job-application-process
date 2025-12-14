from django.contrib import admin
from .models import Customer, Contact, Interaction, Stage, Lead


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
    list_display = ('customer', 'contact', 'interaction_type', 'subject', 'interaction_date')
    search_fields = ('customer__name', 'subject')
    list_filter = ('interaction_type', 'interaction_date')

@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'created_at')
    ordering = ('order',)


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'company', 'status', 'estimated_value', 'created_at')
    search_fields = ('name', 'email', 'company')
    list_filter = ('status', 'created_at')

