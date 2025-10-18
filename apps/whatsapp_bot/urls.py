"""
URL patterns for WhatsApp Bot API endpoints.

This module defines the URL routing for all WhatsApp bot functionality
including webhooks, message processing, and administration endpoints.
"""

from django.urls import path
from . import views

app_name = 'whatsapp_bot'

urlpatterns = [
    # Webhook endpoint (no authentication required)
    path('webhook/', views.webhook_handler, name='webhook_handler'),
    
    # Health check endpoint (public)
    path('health/', views.health_check, name='health_check'),
    
    # Message processing endpoints (authenticated)
    path('send/', views.send_message, name='send_message'),
    path('history/', views.get_interaction_history, name='interaction_history'),
    
    # Statistics and monitoring endpoints (authenticated)
    path('statistics/', views.get_bot_statistics, name='bot_statistics'),
    
    # Template management endpoints (authenticated)
    path('templates/', views.get_templates, name='get_templates'),
    path('templates/test/', views.test_template, name='test_template'),
] 