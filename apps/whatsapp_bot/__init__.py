"""
WhatsApp Bot Handler for ACS

This module provides a comprehensive WhatsApp bot handler that integrates with
Azure Communication Services (ACS) for template-based messaging, PostgreSQL
for dynamic data retrieval, optional Redis for conversation context, and OpenAI for fallback responses.

Note: Redis is only used for conversation context management and is optional.
If not configured, LocMemCache will be used instead.
"""

default_app_config = 'apps.whatsapp_bot.apps.WhatsAppBotConfig' 