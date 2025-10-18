"""
Unified WhatsApp Sender Service.

This service provides a unified interface for sending WhatsApp messages
that works both in Django and Azure Functions environments.
"""

import os
import logging
import requests
from typing import Dict, Any, Optional, Union
from django.conf import settings

logger = logging.getLogger(__name__)


class WhatsAppSenderService:
    """
    Unified service for sending WhatsApp messages via Azure Communication Services.
    
    This service handles both Django and Azure Functions environments
    with proper error handling and retry logic.
    """
    
    def __init__(self):
        """Initialize the WhatsApp sender service."""
        self.endpoint = self._get_setting('ACS_WHATSAPP_ENDPOINT')
        self.access_key = self._get_setting('ACS_WHATSAPP_API_KEY')
        self.phone_number = self._get_setting('ACS_PHONE_NUMBER')
        self.channel_id = self._get_setting('WHATSAPP_CHANNEL_ID_GUID')
        
        # Validate required settings
        if not all([self.endpoint, self.access_key, self.phone_number]):
            logger.warning("WhatsApp sender not fully configured - some messages may fail")
        
        self.base_url = f"{self.endpoint}/messages" if self.endpoint else None
        self.headers = self._build_headers()
    
    def _get_setting(self, setting_name: str) -> Optional[str]:
        """Get setting value with fallback to environment variables."""
        try:
            # Try Django settings first
            return getattr(settings, setting_name, None)
        except Exception:
            # Fallback to environment variables
            return os.environ.get(setting_name)
    
    def _build_headers(self) -> Dict[str, str]:
        """Build request headers for ACS API."""
        headers = {
            'Content-Type': 'application/json',
            'X-Microsoft-Skype-Chain-ID': 'whatsapp-bot'
        }
        
        if self.access_key:
            headers['Authorization'] = f'HMAC-SHA256 {self.access_key}'
        
        return headers
    
    def send_text_message(
        self, 
        to_number: str, 
        message: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a text message via WhatsApp.
        
        Args:
            to_number: Recipient phone number (with or without whatsapp: prefix)
            message: Message text to send
            context: Optional context data for logging
            
        Returns:
            Dictionary with success status and response data
        """
        try:
            # Normalize phone number
            normalized_number = self._normalize_phone_number(to_number)
            
            # Prepare request payload
            payload = {
                "content": {
                    "type": "text",
                    "text": message
                },
                "from": self.phone_number,
                "to": [normalized_number]
            }
            
            # Add channel ID if available
            if self.channel_id:
                payload["channelRegistrationId"] = self.channel_id
            
            logger.info(f"Sending WhatsApp message to {normalized_number}")
            
            # Send request
            response = self._make_request(payload)
            
            if response.get('success'):
                logger.info(f"Message sent successfully to {normalized_number}")
                return {
                    'success': True,
                    'message_id': response.get('id'),
                    'to': normalized_number,
                    'response': response
                }
            else:
                logger.error(f"Failed to send message to {normalized_number}: {response.get('error')}")
                return {
                    'success': False,
                    'error': response.get('error'),
                    'to': normalized_number
                }
                
        except Exception as e:
            logger.exception(f"Error sending WhatsApp message to {to_number}")
            return {
                'success': False,
                'error': str(e),
                'to': to_number
            }
    
    def send_template_message(
        self,
        to_number: str,
        template_name: str,
        parameters: Dict[str, str],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a template message via WhatsApp.
        
        Args:
            to_number: Recipient phone number
            template_name: Name of the template to use
            parameters: Template parameters
            context: Optional context data for logging
            
        Returns:
            Dictionary with success status and response data
        """
        try:
            # Normalize phone number
            normalized_number = self._normalize_phone_number(to_number)
            
            # Prepare request payload
            payload = {
                "content": {
                    "type": "template",
                    "template": {
                        "name": template_name,
                        "language": "es",
                        "values": [
                            {"name": key, "value": value}
                            for key, value in parameters.items()
                        ]
                    }
                },
                "from": self.phone_number,
                "to": [normalized_number]
            }
            
            # Add channel ID if available
            if self.channel_id:
                payload["channelRegistrationId"] = self.channel_id
            
            logger.info(f"Sending template message '{template_name}' to {normalized_number}")
            
            # Send request
            response = self._make_request(payload)
            
            if response.get('success'):
                logger.info(f"Template message sent successfully to {normalized_number}")
                return {
                    'success': True,
                    'message_id': response.get('id'),
                    'template_name': template_name,
                    'to': normalized_number,
                    'response': response
                }
            else:
                logger.error(f"Failed to send template message to {normalized_number}: {response.get('error')}")
                return {
                    'success': False,
                    'error': response.get('error'),
                    'template_name': template_name,
                    'to': normalized_number
                }
                
        except Exception as e:
            logger.exception(f"Error sending template message to {to_number}")
            return {
                'success': False,
                'error': str(e),
                'template_name': template_name,
                'to': to_number
            }
    
    def _normalize_phone_number(self, phone: str) -> str:
        """Normalize phone number to WhatsApp format."""
        # Remove existing whatsapp: prefix if present
        if phone.startswith('whatsapp:'):
            phone = phone.replace('whatsapp:', '')
        
        # Add whatsapp: prefix
        return f"whatsapp:{phone}"
    
    def _make_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to ACS API with retry logic."""
        if not self.base_url:
            return {'success': False, 'error': 'ACS endpoint not configured'}
        
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.base_url,
                    json=payload,
                    headers=self.headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return {
                        'success': True,
                        'id': response.json().get('id'),
                        'response': response.json()
                    }
                elif response.status_code == 429:
                    # Rate limit - wait and retry
                    if attempt < max_retries - 1:
                        logger.warning(f"Rate limited, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})")
                        import time
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    else:
                        return {
                            'success': False,
                            'error': f'Rate limit exceeded after {max_retries} attempts'
                        }
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.error(f"ACS API error: {error_msg}")
                    return {'success': False, 'error': error_msg}
                    
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Request failed, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries}): {e}")
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    return {'success': False, 'error': f'Request failed after {max_retries} attempts: {str(e)}'}
        
        return {'success': False, 'error': 'Max retries exceeded'}
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate the service configuration."""
        issues = []
        
        if not self.endpoint:
            issues.append("ACS_WHATSAPP_ENDPOINT not configured")
        if not self.access_key:
            issues.append("ACS_WHATSAPP_API_KEY not configured")
        if not self.phone_number:
            issues.append("ACS_PHONE_NUMBER not configured")
        if not self.channel_id:
            issues.append("WHATSAPP_CHANNEL_ID_GUID not configured")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'endpoint_configured': bool(self.endpoint),
            'access_key_configured': bool(self.access_key),
            'phone_number_configured': bool(self.phone_number),
            'channel_id_configured': bool(self.channel_id)
        }


# Global instance for easy access
whatsapp_sender = WhatsAppSenderService()


# Backward compatibility functions
def send_whatsapp_message(to_number: str, message: str, event_data: dict = None) -> bool:
    """
    Backward compatibility function for Azure Functions.
    
    Args:
        to_number: Phone number to send message to
        message: Message text
        event_data: Optional event data (for compatibility)
        
    Returns:
        True if sent successfully, False otherwise
    """
    result = whatsapp_sender.send_text_message(to_number, message)
    return result.get('success', False)
