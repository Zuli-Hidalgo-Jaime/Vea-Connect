"""
Django admin interface for WhatsApp Bot models.

This module provides admin interfaces for managing WhatsApp templates,
interactions, contexts, and data sources.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    WhatsAppTemplate,
    WhatsAppInteraction,
    WhatsAppContext,
    DataSource
)


@admin.register(WhatsAppTemplate)
class WhatsAppTemplateAdmin(admin.ModelAdmin):
    """
    Admin interface for WhatsApp templates.
    
    Provides management interface for WhatsApp message templates
    registered in Azure Communication Services.
    """
    
    list_display = [
        'template_name',
        'template_id',
        'category',
        'language',
        'is_active',
        'parameter_count',
        'created_at'
    ]
    
    list_filter = [
        'category',
        'language',
        'is_active',
        'created_at'
    ]
    
    search_fields = [
        'template_name',
        'template_id',
        'category'
    ]
    
    readonly_fields = [
        'id',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('template_name', 'template_id', 'language', 'category')
        }),
        ('Configuration', {
            'fields': ('parameters', 'is_active')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def parameter_count(self, obj):
        """Display the number of parameters for the template."""
        return len(obj.parameters) if obj.parameters else 0
    parameter_count.short_description = 'Parameters'
    
    def get_queryset(self, request):
        """Optimize queryset with related data."""
        return super().get_queryset(request).select_related()


@admin.register(WhatsAppInteraction)
class WhatsAppInteractionAdmin(admin.ModelAdmin):
    """
    Admin interface for WhatsApp interactions.
    
    Provides management interface for tracking and analyzing
    WhatsApp bot interactions with users.
    """
    
    list_display = [
        'phone_number',
        'intent_detected',
        'template_used_display',
        'fallback_used',
        'success',
        'processing_time_display',
        'created_at'
    ]
    
    list_filter = [
        'intent_detected',
        'fallback_used',
        'success',
        'template_used',
        'created_at'
    ]
    
    search_fields = [
        'phone_number',
        'message_text',
        'intent_detected',
        'response_text'
    ]
    
    readonly_fields = [
        'id',
        'phone_number',
        'message_text',
        'intent_detected',
        'template_used',
        'response_text',
        'response_id',
        'parameters_used_display',
        'fallback_used',
        'processing_time_ms',
        'success',
        'error_message',
        'context_data_display',
        'created_at'
    ]
    
    fieldsets = (
        ('Interaction Details', {
            'fields': (
                'phone_number',
                'message_text',
                'intent_detected',
                'template_used',
                'response_text',
                'response_id'
            )
        }),
        ('Processing Information', {
            'fields': (
                'parameters_used_display',
                'fallback_used',
                'processing_time_ms',
                'success',
                'error_message'
            )
        }),
        ('Context Data', {
            'fields': ('context_data_display',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    def template_used_display(self, obj):
        """Display template name with link to template admin."""
        if obj.template_used:
            url = reverse('admin:whatsapp_bot_whatsapptemplate_change', args=[obj.template_used.id])
            return format_html('<a href="{}">{}</a>', url, obj.template_used.template_name)
        return 'None'
    template_used_display.short_description = 'Template Used'
    
    def parameters_used_display(self, obj):
        """Display parameters in a formatted way."""
        if obj.parameters_used:
            formatted_params = []
            for key, value in obj.parameters_used.items():
                formatted_params.append(f"<strong>{key}:</strong> {value}")
            return mark_safe('<br>'.join(formatted_params))
        return 'None'
    parameters_used_display.short_description = 'Parameters Used'
    
    def context_data_display(self, obj):
        """Display context data in a formatted way."""
        if obj.context_data:
            formatted_context = []
            for key, value in obj.context_data.items():
                formatted_context.append(f"<strong>{key}:</strong> {value}")
            return mark_safe('<br>'.join(formatted_context))
        return 'None'
    context_data_display.short_description = 'Context Data'
    
    def processing_time_display(self, obj):
        """Display processing time in a human-readable format."""
        if obj.processing_time_ms:
            if obj.processing_time_ms < 1000:
                return f"{obj.processing_time_ms:.1f}ms"
            else:
                return f"{obj.processing_time_ms/1000:.2f}s"
        return 'N/A'
    processing_time_display.short_description = 'Processing Time'
    
    def get_queryset(self, request):
        """Optimize queryset with related data."""
        return super().get_queryset(request).select_related('template_used')
    
    def has_add_permission(self, request):
        """Disable adding interactions manually."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing interactions."""
        return False


@admin.register(WhatsAppContext)
class WhatsAppContextAdmin(admin.ModelAdmin):
    """
    Admin interface for WhatsApp conversation contexts.
    
    Provides management interface for viewing and managing
    conversation context data stored in Redis.
    """
    
    list_display = [
        'phone_number',
        'is_active',
        'interaction_count',
        'last_interaction',
        'session_start',
        'session_duration'
    ]
    
    list_filter = [
        'is_active',
        'session_start',
        'last_interaction'
    ]
    
    search_fields = [
        'phone_number'
    ]
    
    readonly_fields = [
        'id',
        'phone_number',
        'context_data_display',
        'last_interaction',
        'session_start',
        'is_active',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Context Information', {
            'fields': (
                'phone_number',
                'is_active',
                'session_start',
                'last_interaction'
            )
        }),
        ('Context Data', {
            'fields': ('context_data_display',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def context_data_display(self, obj):
        """Display context data in a formatted way."""
        if obj.context_data:
            formatted_context = []
            for key, value in obj.context_data.items():
                formatted_context.append(f"<strong>{key}:</strong> {value}")
            return mark_safe('<br>'.join(formatted_context))
        return 'None'
    context_data_display.short_description = 'Context Data'
    
    def interaction_count(self, obj):
        """Display the number of interactions for this context."""
        return obj.context_data.get('interaction_count', 0)
    interaction_count.short_description = 'Interactions'
    
    def session_duration(self, obj):
        """Display session duration."""
        if obj.session_start and obj.last_interaction:
            duration = obj.last_interaction - obj.session_start
            hours = duration.total_seconds() / 3600
            if hours < 1:
                return f"{duration.total_seconds() / 60:.0f} minutes"
            elif hours < 24:
                return f"{hours:.1f} hours"
            else:
                days = hours / 24
                return f"{days:.1f} days"
        return 'N/A'
    session_duration.short_description = 'Session Duration'
    
    def has_add_permission(self, request):
        """Disable adding contexts manually."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing contexts."""
        return False


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    """
    Admin interface for data sources.
    
    Provides management interface for configuring data sources
    used by the WhatsApp bot for dynamic data retrieval.
    """
    
    list_display = [
        'name',
        'source_type',
        'table_name',
        'cache_ttl_display',
        'is_active',
        'created_at'
    ]
    
    list_filter = [
        'source_type',
        'is_active',
        'created_at'
    ]
    
    search_fields = [
        'name',
        'table_name',
        'query_template'
    ]
    
    readonly_fields = [
        'id',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'source_type', 'is_active')
        }),
        ('Configuration', {
            'fields': ('table_name', 'query_template', 'cache_ttl')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def cache_ttl_display(self, obj):
        """Display cache TTL in a human-readable format."""
        if obj.cache_ttl:
            if obj.cache_ttl < 60:
                return f"{obj.cache_ttl} seconds"
            elif obj.cache_ttl < 3600:
                return f"{obj.cache_ttl / 60:.0f} minutes"
            else:
                return f"{obj.cache_ttl / 3600:.1f} hours"
        return 'No cache'
    cache_ttl_display.short_description = 'Cache TTL'


# Customize admin site
admin.site.site_header = "WhatsApp Bot Administration"
admin.site.site_title = "WhatsApp Bot Admin"
admin.site.index_title = "Welcome to WhatsApp Bot Administration" 