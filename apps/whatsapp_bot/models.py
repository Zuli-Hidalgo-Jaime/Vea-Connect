from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class WhatsAppTemplate(models.Model):
    """
    Model for storing WhatsApp message templates registered in ACS.
    
    This model tracks templates that can be used for priority responses
    in the WhatsApp bot handler.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template_name = models.CharField(max_length=100, unique=True, help_text="Template name in ACS")
    template_id = models.CharField(max_length=100, unique=True, help_text="Template ID from ACS")
    channel_id = models.CharField(max_length=100, default='c3dd072b-92b3-4812-8ed0-10b1d3a45da1', help_text="ACS Channel ID")
    language = models.CharField(max_length=10, default='es_MX', help_text="Template language code")
    category = models.CharField(
        max_length=50,
        choices=[
            ('donations', 'Donations'),
            ('ministry', 'Ministry Contact'),
            ('events', 'Event Information'),
            ('general', 'General'),
        ],
        default='general',
        help_text="Template category for organization"
    )
    parameters = models.JSONField(default=list, help_text="List of required parameters")
    is_active = models.BooleanField(default=True, help_text="Whether template is active")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'whatsapp_templates'
        ordering = ['category', 'template_name']
        verbose_name = "WhatsApp Template"
        verbose_name_plural = "WhatsApp Templates"
    
    def __str__(self):
        return f"{self.template_name} ({self.category})"


class WhatsAppInteraction(models.Model):
    """
    Model for logging WhatsApp bot interactions.
    
    Tracks all interactions with users, including templates used,
    responses sent, and context information.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(max_length=20, help_text="User's phone number")
    message_text = models.TextField(help_text="Incoming message from user")
    intent_detected = models.CharField(max_length=100, blank=True, help_text="Detected user intent")
    template_used = models.ForeignKey(
        WhatsAppTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interactions',
        help_text="Template used for response"
    )
    response_text = models.TextField(help_text="Response sent to user")
    response_id = models.CharField(max_length=100, blank=True, help_text="ACS response ID")
    parameters_used = models.JSONField(default=dict, help_text="Parameters injected into template")
    fallback_used = models.BooleanField(default=False, help_text="Whether OpenAI fallback was used")
    processing_time_ms = models.FloatField(default=0.0, help_text="Response processing time")
    success = models.BooleanField(default=True, help_text="Whether interaction was successful")
    error_message = models.TextField(blank=True, help_text="Error message if interaction failed")
    context_data = models.JSONField(default=dict, help_text="Additional context data")
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'whatsapp_interactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['created_at']),
            models.Index(fields=['template_used']),
            models.Index(fields=['success']),
        ]
        verbose_name = "WhatsApp Interaction"
        verbose_name_plural = "WhatsApp Interactions"
    
    def __str__(self):
        return f"Interaction {self.id} - {self.phone_number} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"


class WhatsAppContext(models.Model):
    """
    Model for storing conversation context in Redis.
    
    This model represents the structure of context data that will be
    stored in Redis for maintaining conversation state.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(max_length=20, unique=True, help_text="User's phone number")
    context_data = models.JSONField(default=dict, help_text="Conversation context data")
    last_interaction = models.DateTimeField(default=timezone.now, help_text="Last interaction time")
    session_start = models.DateTimeField(default=timezone.now, help_text="Session start time")
    is_active = models.BooleanField(default=True, help_text="Whether session is active")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'whatsapp_contexts'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['is_active']),
            models.Index(fields=['updated_at']),
        ]
        verbose_name = "WhatsApp Context"
        verbose_name_plural = "WhatsApp Contexts"
    
    def __str__(self):
        return f"Context {self.phone_number} - {self.updated_at.strftime('%Y-%m-%d %H:%M')}"


class DataSource(models.Model):
    """
    Model for tracking data sources used in template responses.
    
    This model helps track which data sources (PostgreSQL tables, Redis keys)
    are used for different types of responses.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, help_text="Data source name")
    source_type = models.CharField(
        max_length=50,
        choices=[
            ('postgresql', 'PostgreSQL'),
            ('redis', 'Redis'),
            ('api', 'External API'),
        ],
        help_text="Type of data source"
    )
    table_name = models.CharField(max_length=100, blank=True, help_text="PostgreSQL table name")
    query_template = models.TextField(blank=True, help_text="Query template for data retrieval")
    cache_ttl = models.IntegerField(default=3600, help_text="Cache TTL in seconds")
    is_active = models.BooleanField(default=True, help_text="Whether data source is active")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'whatsapp_data_sources'
        ordering = ['name']
        verbose_name = "Data Source"
        verbose_name_plural = "Data Sources"
    
    def __str__(self):
        return f"{self.name} ({self.source_type})" 