"""
Python models and data structures for WhatsApp Event Grid webhook.

This module provides lightweight dataclasses and utility functions for
handling configuration options and parsing ACS Advanced Messaging events.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class NotificationMessagesClientOptions:
    """
    Configuration options for ACS Notification Messages client.
    
    Maps to existing environment variables for ACS connection and endpoint.
    """
    endpoint: str = field(default_factory=lambda: os.environ.get('ACS_WHATSAPP_ENDPOINT', ''))
    access_key: str = field(default_factory=lambda: os.environ.get('ACS_WHATSAPP_API_KEY', ''))
    phone_number: str = field(default_factory=lambda: os.environ.get('ACS_PHONE_NUMBER', ''))
    channel_id: str = field(default_factory=lambda: os.environ.get('WHATSAPP_CHANNEL_ID_GUID', ''))
    
    def is_valid(self) -> bool:
        """Check if all required configuration is present."""
        return all([self.endpoint, self.access_key, self.phone_number])
    
    def get_base_url(self) -> str:
        """Get the base URL for ACS API calls."""
        return f"{self.endpoint}/messages" if self.endpoint else ""


@dataclass
class OpenAIClientOptions:
    """
    Configuration options for Azure OpenAI client.
    
    Maps to existing OpenAI environment variables.
    """
    endpoint: str = field(default_factory=lambda: os.environ.get('AZURE_OPENAI_ENDPOINT', ''))
    api_key: str = field(default_factory=lambda: os.environ.get('AZURE_OPENAI_API_KEY', ''))
    chat_deployment: str = field(default_factory=lambda: os.environ.get('AZURE_OPENAI_CHAT_DEPLOYMENT', 'gpt-35-turbo'))
    chat_api_version: str = field(default_factory=lambda: os.environ.get('AZURE_OPENAI_CHAT_API_VERSION', '2024-02-15-preview'))
    embeddings_deployment: str = field(default_factory=lambda: os.environ.get('AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT', 'text-embedding-ada-002'))
    embeddings_api_version: str = field(default_factory=lambda: os.environ.get('AZURE_OPENAI_EMBEDDINGS_API_VERSION', '2023-05-15'))
    
    def is_valid(self) -> bool:
        """Check if all required configuration is present."""
        return all([self.endpoint, self.api_key, self.chat_deployment])


@dataclass
class AdvancedMessageReceivedEventData:
    """
    Parsed data from ACS Advanced Message Received event.
    
    Represents the normalized structure after parsing various ACS payload schemas.
    """
    sender: str
    text: str
    timestamp: Optional[datetime] = None
    message_id: Optional[str] = None
    schema_used: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate required fields after initialization."""
        if not self.sender or not self.text:
            raise ValueError("sender and text are required fields")


def extract_incoming_text(event_payload: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
    """
    Extract incoming text and sender from ACS event payload.
    
    This function provides a tolerant parser for multiple ACS Advanced Messaging schemas:
    - Legacy: data.messageBody and data.from
    - Standard: data.message.content.text and data.message.from.phoneNumber
    - Alternative: data.content with text/body structure
    
    Args:
        event_payload: Raw event payload from Event Grid
        
    Returns:
        Tuple of (sender_e164, text, meta) where:
        - sender_e164: Normalized phone number in E.164 format
        - text: Extracted message text
        - meta: Additional metadata about the parsing
    """
    meta = {
        'schema_used': None,
        'parsing_success': False,
        'errors': []
    }
    
    try:
        data = event_payload.get('data', {})
        
        # Schema 1: Legacy format - data.messageBody and data.from
        if 'messageBody' in data and 'from' in data:
            text = data.get('messageBody', '').strip()
            sender = data.get('from', '').strip()
            if text and sender:
                meta['schema_used'] = 'legacy'
                meta['parsing_success'] = True
                return _normalize_phone_number(sender), text, meta
        
        # Schema 2: Standard format - data.message.content.text and data.message.from.phoneNumber
        if 'message' in data:
            message = data.get('message', {})
            if isinstance(message, dict):
                content = message.get('content', {})
                if isinstance(content, dict) and 'text' in content:
                    text = content.get('text', '').strip()
                    sender = message.get('from', {}).get('phoneNumber', '').strip()
                    if text and sender:
                        meta['schema_used'] = 'standard'
                        meta['parsing_success'] = True
                        return _normalize_phone_number(sender), text, meta
        
        # Schema 3: Alternative format - data.content with text/body
        if 'content' in data:
            content = data.get('content', {})
            if isinstance(content, dict):
                # Try text field first
                if 'text' in content:
                    text = content.get('text', '').strip()
                    sender = data.get('from', '').strip()
                    if text and sender:
                        meta['schema_used'] = 'content_text'
                        meta['parsing_success'] = True
                        return _normalize_phone_number(sender), text, meta
                
                # Try body field
                if 'body' in content:
                    text = content.get('body', '').strip()
                    sender = data.get('from', '').strip()
                    if text and sender:
                        meta['schema_used'] = 'content_body'
                        meta['parsing_success'] = True
                        return _normalize_phone_number(sender), text, meta
        
        # Schema 4: Direct text in data
        if 'text' in data:
            text = data.get('text', '').strip()
            sender = data.get('from', '').strip()
            if text and sender:
                meta['schema_used'] = 'direct_text'
                meta['parsing_success'] = True
                return _normalize_phone_number(sender), text, meta
        
        # If no schema matched, log the structure for debugging
        meta['errors'].append(f"No matching schema found. Available keys: {list(data.keys())}")
        logger.warning(f"Could not parse ACS event payload. Available data keys: {list(data.keys())}")
        
        return "", "", meta
        
    except Exception as e:
        meta['errors'].append(f"Exception during parsing: {str(e)}")
        logger.error(f"Error parsing ACS event payload: {e}")
        return "", "", meta


def _normalize_phone_number(phone: str) -> str:
    """
    Normalize phone number to E.164 format.
    
    Args:
        phone: Phone number in any format
        
    Returns:
        Phone number in E.164 format (e.g., +525512345678)
    """
    if not phone:
        return ""
    
    # Remove all non-digit characters except +
    cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
    
    # If it starts with +, assume it's already in international format
    if cleaned.startswith('+'):
        return cleaned
    
    # If it's 10 digits, assume it's a Mexican number
    if len(cleaned) == 10:
        return f"+52{cleaned}"
    
    # If it's 12 digits and starts with 52, add +
    if len(cleaned) == 12 and cleaned.startswith('52'):
        return f"+{cleaned}"
    
    # If it's 11 digits and starts with 1, assume US number
    if len(cleaned) == 11 and cleaned.startswith('1'):
        return f"+{cleaned}"
    
    # Default: return as is with + prefix if not present
    return cleaned if cleaned.startswith('+') else f"+{cleaned}"


def create_event_data_from_payload(event_payload: Dict[str, Any]) -> Optional[AdvancedMessageReceivedEventData]:
    """
    Create AdvancedMessageReceivedEventData from event payload.
    
    Args:
        event_payload: Raw event payload from Event Grid
        
    Returns:
        Parsed event data or None if parsing failed
    """
    try:
        sender, text, meta = extract_incoming_text(event_payload)
        
        if not meta['parsing_success']:
            logger.warning(f"Failed to parse event payload: {meta['errors']}")
            return None
        
        return AdvancedMessageReceivedEventData(
            sender=sender,
            text=text,
            timestamp=datetime.utcnow(),
            message_id=event_payload.get('id'),
            schema_used=meta['schema_used'],
            raw_data=event_payload
        )
        
    except Exception as e:
        logger.error(f"Error creating event data from payload: {e}")
        return None


def get_configuration_options() -> Tuple[NotificationMessagesClientOptions, OpenAIClientOptions]:
    """
    Get configuration options from environment variables.
    
    Returns:
        Tuple of (acs_options, openai_options)
    """
    acs_options = NotificationMessagesClientOptions()
    openai_options = OpenAIClientOptions()
    
    return acs_options, openai_options
