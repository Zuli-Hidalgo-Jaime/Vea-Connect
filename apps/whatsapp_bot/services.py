# pyright: reportMissingImports=false, reportAttributeAccessIssue=false, reportCallIssue=false

"""
Core services for WhatsApp Bot Handler.

This module provides the main services for handling WhatsApp interactions,
including ACS integration, template management, data retrieval, and logging.
"""

import json
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from django.conf import settings
from django.db import connection
from django.core.cache import cache
import requests
from .models import WhatsAppTemplate, WhatsAppInteraction, WhatsAppContext, DataSource

logger = logging.getLogger(__name__)


class ACSService:
    """
    Service for interacting with Azure Communication Services (ACS).
    
    Handles sending WhatsApp messages using registered templates
    and managing ACS responses.
    """
    
    def __init__(self):
        """Initialize ACS service with configuration."""
        self.endpoint = getattr(settings, 'ACS_WHATSAPP_ENDPOINT', 'https://your-acs-resource.communication.azure.com')
        self.access_key = getattr(settings, 'ACS_WHATSAPP_API_KEY', 'your-acs-access-key')
        self.phone_number = getattr(settings, 'ACS_PHONE_NUMBER', 'whatsapp:+1234567890')
        self.channel_id = getattr(settings, 'WHATSAPP_CHANNEL_ID_GUID', 'c3dd072b-92b3-4812-8ed0-10b1d3a45da1')
        self.base_url = f"{self.endpoint}/messages"
        self.headers = {
            'Authorization': f'HMAC-SHA256 {self.access_key}',
            'Content-Type': 'application/json',
            'X-Microsoft-Skype-Chain-ID': 'whatsapp-bot'
        }
    
    def send_template_message(
        self,
        to_phone: str,
        template_name: str,
        parameters: Dict[str, str],
        language: str = 'es_MX'
    ) -> Dict[str, Any]:
        """
        Send a WhatsApp template message via ACS.
        
        Args:
            to_phone: Recipient phone number
            template_name: Name of the template to use
            parameters: Dictionary of parameters to inject into template
            language: Template language code
            
        Returns:
            Dictionary with response data including message ID
            
        Raises:
            Exception: If ACS request fails
        """
        try:
            payload = {
                "from": self.phone_number,
                "to": [to_phone],
                "channelRegistrationId": self.channel_id,
                "content": {
                    "type": "template",
                    "template": {
                        "name": template_name,
                        "language": language,
                        "values": [
                            {"name": key, "value": value}
                            for key, value in parameters.items()
                        ]
                    }
                }
            }
            
            logger.info(f"Sending template message: {template_name} to {to_phone}")
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 202:
                response_data = response.json()
                logger.info(f"Template message sent successfully: {response_data.get('id')}")
                return {
                    'success': True,
                    'message_id': response_data.get('id'),
                    'status': 'accepted'
                }
            else:
                error_msg = f"ACS request failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"Error sending template message: {str(e)}")
            raise
    
    def send_text_message(self, to_phone: str, text: str) -> Dict[str, Any]:
        """
        Send a plain text message via ACS.
        
        Args:
            to_phone: Recipient phone number
            text: Message text to send
            
        Returns:
            Dictionary with response data
        """
        try:
            payload = {
                "from": self.phone_number,
                "to": [to_phone],
                "channelRegistrationId": self.channel_id,
                "content": {
                    "type": "text",
                    "text": text
                }
            }
            
            logger.info(f"Sending text message to {to_phone}")
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 202:
                response_data = response.json()
                logger.info(f"Text message sent successfully: {response_data.get('id')}")
                return {
                    'success': True,
                    'message_id': response_data.get('id'),
                    'status': 'accepted'
                }
            else:
                error_msg = f"ACS request failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"Error sending text message: {str(e)}")
            raise


class DataRetrievalService:
    """
    Service for retrieving dynamic data from PostgreSQL and Redis.
    
    Handles data queries for template parameters and caching
    of frequently accessed data.
    """
    
    def __init__(self):
        """Initialize data retrieval service."""
        self.cache_ttl = 3600  # 1 hour default cache TTL
    
    def get_donation_info(self, customer_name: str) -> Dict[str, Any]:
        """
        Retrieve donation information for a customer.
        
        Args:
            customer_name: Name of the customer
            
        Returns:
            Dictionary with donation information
        """
        cache_key = f"donation_info:{customer_name}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info(f"Retrieved donation info from cache for {customer_name}")
            return cached_data
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        d.id,
                        d.amount,
                        d.donation_date,
                        d.donation_type,
                        b.name as bank_name,
                        b.account_number,
                        b.clabe_number,
                        c.first_name || ' ' || c.last_name as beneficiary_name,
                        c.phone as contact_phone
                    FROM donations_donation d
                    LEFT JOIN donations_donationtype dt ON d.donation_type_id = dt.id
                    LEFT JOIN directory_contact c ON d.beneficiary_id = c.id
                    LEFT JOIN donations_bankinfo b ON d.bank_info_id = b.id
                    WHERE c.first_name ILIKE %s OR c.last_name ILIKE %s
                    ORDER BY d.donation_date DESC
                    LIMIT 1
                """, [f'%{customer_name}%', f'%{customer_name}%'])
                
                row = cursor.fetchone()
                
                if row:
                    data = {
                        'customer_name': customer_name,
                        'ministry_name': 'Ministerio de VEA',
                        'bank_name': row[4] or 'Banco de México',
                        'beneficiary_name': row[7] or 'Ministerio de VEA',
                        'account_number': row[5] or '1234567890',
                        'clabe_number': row[6] or '012345678901234567',
                        'contact_name': 'Soporte VEA',
                        'contact_phone': row[8] or '+525512345678'
                    }
                    
                    cache.set(cache_key, data, self.cache_ttl)
                    logger.info(f"Retrieved donation info from database for {customer_name}")
                    return data
                else:
                    # Return default data if no match found
                    default_data = {
                        'customer_name': customer_name,
                        'ministry_name': 'Ministerio de VEA',
                        'bank_name': 'Banco de México',
                        'beneficiary_name': 'Ministerio de VEA',
                        'account_number': '1234567890',
                        'clabe_number': '012345678901234567',
                        'contact_name': 'Soporte VEA',
                        'contact_phone': '+525512345678'
                    }
                    
                    cache.set(cache_key, default_data, self.cache_ttl)
                    logger.info(f"Using default donation info for {customer_name}")
                    return default_data
                    
        except Exception as e:
            logger.error(f"Error retrieving donation info: {str(e)}")
            # Return default data on error
            return {
                'customer_name': customer_name,
                'ministry_name': 'Ministerio de VEA',
                'bank_name': 'Banco de México',
                'beneficiary_name': 'Ministerio de VEA',
                'account_number': '1234567890',
                'clabe_number': '012345678901234567',
                'contact_name': 'Soporte VEA',
                'contact_phone': '+525512345678'
            }
    
    def get_ministry_contact(self, ministry_name: str) -> Dict[str, Any]:
        """
        Retrieve ministry contact information.
        
        Args:
            ministry_name: Name of the ministry
            
        Returns:
            Dictionary with ministry contact information
        """
        cache_key = f"ministry_contact:{ministry_name}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info(f"Retrieved ministry contact from cache for {ministry_name}")
            return cached_data
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        c.first_name,
                        c.last_name,
                        c.phone,
                        c.email,
                        c.role
                    FROM directory_contact c
                    WHERE c.role ILIKE %s OR c.first_name ILIKE %s
                    ORDER BY c.created_at DESC
                    LIMIT 1
                """, [f'%{ministry_name}%', f'%{ministry_name}%'])
                
                row = cursor.fetchone()
                
                if row:
                    data = {
                        'customer_name': 'Usuario',
                        'ministry_name': ministry_name,
                        'contact_name': f"{row[0]} {row[1]}",
                        'contact_phone': row[2] or '+525512345678'
                    }
                else:
                    data = {
                        'customer_name': 'Usuario',
                        'ministry_name': ministry_name,
                        'contact_name': 'Soporte VEA',
                        'contact_phone': '+525512345678'
                    }
                
                cache.set(cache_key, data, self.cache_ttl)
                logger.info(f"Retrieved ministry contact for {ministry_name}")
                return data
                
        except Exception as e:
            logger.error(f"Error retrieving ministry contact: {str(e)}")
            return {
                'customer_name': 'Usuario',
                'ministry_name': ministry_name,
                'contact_name': 'Soporte VEA',
                'contact_phone': '+525512345678'
            }
    
    def get_event_info(self, event_name: str) -> Dict[str, Any]:
        """
        Retrieve event information.
        
        Args:
            event_name: Name of the event
            
        Returns:
            Dictionary with event information
        """
        cache_key = f"event_info:{event_name}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info(f"Retrieved event info from cache for {event_name}")
            return cached_data
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        e.title,
                        e.date,
                        e.location,
                        e.description
                    FROM events_event e
                    WHERE e.title ILIKE %s
                    ORDER BY e.date DESC
                    LIMIT 1
                """, [f'%{event_name}%'])
                
                row = cursor.fetchone()
                
                if row:
                    data = {
                        'customer_name': 'Usuario',
                        'event_name': row[0],
                        'event_date': row[1].strftime('%d/%m/%Y') if row[1] else 'Próximamente',
                        'event_location': row[2] or 'Por confirmar'
                    }
                else:
                    data = {
                        'customer_name': 'Usuario',
                        'event_name': event_name,
                        'event_date': 'Próximamente',
                        'event_location': 'Por confirmar'
                    }
                
                cache.set(cache_key, data, self.cache_ttl)
                logger.info(f"Retrieved event info for {event_name}")
                return data
                
        except Exception as e:
            logger.error(f"Error retrieving event info: {str(e)}")
            return {
                'customer_name': 'Usuario',
                'event_name': event_name,
                'event_date': 'Próximamente',
                'event_location': 'Por confirmar'
            }


class TemplateService:
    """
    Service for managing WhatsApp templates and intent detection.
    
    Handles template loading, intent detection, and parameter preparation
    for WhatsApp message responses.
    """
    
    def __init__(self, acs_service: ACSService, data_service: DataRetrievalService):
        """
        Initialize template service.
        
        Args:
            acs_service: ACS service for sending messages
            data_service: Data retrieval service for dynamic data
        """
        self.acs_service = acs_service
        self.data_service = data_service
        self.templates = self._load_templates()
        logger.info(f"Template service initialized with {len(self.templates)} templates")
    
    def _load_templates(self) -> Dict[str, WhatsAppTemplate]:
        """Load templates from database."""
        try:
            templates = {}
            for template in WhatsAppTemplate.objects.filter(is_active=True):
                templates[template.template_name] = template
            return templates
        except Exception as e:
            logger.error(f"Error loading templates: {str(e)}")
            return {}
    
    def detect_intent(self, message: str) -> Tuple[str, Dict[str, Any]]:
        """
        Detect user intent from message text.
        
        Args:
            message: User message text
            
        Returns:
            Tuple of (intent_type, intent_data)
        """
        message_lower = message.lower()
        
        # Donations intent
        if any(word in message_lower for word in ['donativo', 'donacion', 'donar', 'apoyo', 'contribucion']):
            return 'donations', {'customer_name': 'Usuario'}
        
        # Ministry contact intent
        if any(word in message_lower for word in ['ministerio', 'contacto', 'contactar', 'ayuda', 'soporte']):
            return 'ministry', {'ministry_name': 'Ministerio de VEA'}
        
        # Event information intent
        if any(word in message_lower for word in ['evento', 'actividad', 'fecha', 'cuando', 'donde']):
            return 'events', {'event_name': 'Evento VEA'}
        
        # General request intent
        if any(word in message_lower for word in ['solicitud', 'pedido', 'request', 'ayuda', 'informacion']):
            return 'general', {'customer_name': 'Usuario', 'request_summary': message}
        
        return 'unknown', {}
    
    def get_template_for_intent(self, intent: str) -> Optional[WhatsAppTemplate]:
        """
        Get template for detected intent.
        
        Args:
            intent: Detected intent type
            
        Returns:
            WhatsAppTemplate object or None
        """
        intent_to_template = {
            'donations': 'vea_info_donativos',
            'ministry': 'vea_contacto_ministerio',
            'events': 'vea_event_info',
            'general': 'vea_request_received'
        }
        
        template_name = intent_to_template.get(intent)
        if template_name and template_name in self.templates:
            return self.templates[template_name]
        
        return None
    
    def prepare_template_parameters(
        self,
        template: WhatsAppTemplate,
        intent_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Prepare parameters for template based on intent data.
        
        Args:
            template: WhatsAppTemplate object
            intent_data: Data from intent detection
            
        Returns:
            Dictionary of parameters for template
        """
        try:
            if template.template_name == 'vea_info_donativos':
                donation_info = self.data_service.get_donation_info(intent_data.get('customer_name', 'Usuario'))
                return {
                    'customer_name': donation_info['customer_name'],
                    'ministry_name': donation_info['ministry_name'],
                    'bank_name': donation_info['bank_name'],
                    'beneficiary_name': donation_info['beneficiary_name'],
                    'account_number': donation_info['account_number'],
                    'clabe_number': donation_info['clabe_number'],
                    'contact_name': donation_info['contact_name'],
                    'contact_phone': donation_info['contact_phone']
                }
            
            elif template.template_name == 'vea_event_info':
                event_info = self.data_service.get_event_info(intent_data.get('event_name', 'Evento VEA'))
                return {
                    'customer_name': event_info['customer_name'],
                    'event_name': event_info['event_name'],
                    'event_date': event_info['event_date'],
                    'event_location': event_info['event_location']
                }
            
            elif template.template_name == 'vea_contacto_ministerio':
                ministry_info = self.data_service.get_ministry_contact(intent_data.get('ministry_name', 'Ministerio de VEA'))
                return {
                    'customer_name': ministry_info['customer_name'],
                    'ministry_name': ministry_info['ministry_name'],
                    'contact_name': ministry_info['contact_name'],
                    'contact_phone': ministry_info['contact_phone']
                }
            
            elif template.template_name == 'vea_request_received':
                return {
                    'customer_name': intent_data.get('customer_name', 'Usuario'),
                    'request_summary': intent_data.get('request_summary', 'Solicitud recibida')
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error preparing template parameters: {str(e)}")
            return {}
    
    def send_template_response(
        self,
        to_phone: str,
        template: WhatsAppTemplate,
        parameters: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Send template response via ACS.
        
        Args:
            to_phone: Recipient phone number
            template: WhatsAppTemplate object
            parameters: Template parameters
            
        Returns:
            Response data from ACS
        """
        try:
            response = self.acs_service.send_template_message(
                to_phone=to_phone,
                template_name=str(template.template_name),  # Asegura str
                parameters=parameters,
                language=str(template.language)  # Asegura str
            )
            
            return {
                'success': True,
                'response_id': response.get('message_id', ''),
                'template_name': template.template_name,
                'parameters': parameters
            }
            
        except Exception as e:
            logger.error(f"Error sending template response: {str(e)}")
            raise  # Re-raise the exception for tests to catch


class LoggingService:
    """
    Service for logging WhatsApp interactions and managing context.
    
    Handles interaction logging, context management in Redis (opcional),
    and conversation state tracking.
    
    Note: Redis is only used for conversation context management.
    If AZURE_REDIS_CONNECTIONSTRING is not configured, LocMemCache will be used.
    """
    
    def __init__(self, redis_client=None):
        """Initialize logging service."""
        # Permitir inyección de dependencias para tests
        if redis_client is not None:
            self.redis_client = redis_client
        else:
            try:
                # Intentar obtener cliente Redis real
                self.redis_client = cache.client.get_client()
            except AttributeError:
                # Fallback para tests con LocMemCache
                # logger.warning("Redis client not available, using cache fallback")  # Suprimido para CLI
                self.redis_client = None
    
    def log_interaction(
        self,
        phone_number: str,
        message_text: str,
        intent_detected: str,
        template_used: Optional[WhatsAppTemplate],
        response_text: str,
        response_id: str,
        parameters_used: Dict[str, Any],
        fallback_used: bool,
        processing_time_ms: float,
        success: bool,
        error_message: str = '',
        context_data: Optional[Dict[str, Any]] = None
    ) -> WhatsAppInteraction:
        """
        Log WhatsApp interaction to database.
        
        Args:
            phone_number: User's phone number
            message_text: Incoming message text
            intent_detected: Detected user intent
            template_used: Template used for response
            response_text: Response sent to user
            response_id: ACS response ID
            parameters_used: Parameters used in template
            fallback_used: Whether OpenAI fallback was used
            processing_time_ms: Processing time in milliseconds
            success: Whether interaction was successful
            error_message: Error message if failed
            context_data: Additional context data
            
        Returns:
            WhatsAppInteraction object
        """
        try:
            interaction = WhatsAppInteraction.objects.create(
                phone_number=phone_number,
                message_text=message_text,
                intent_detected=intent_detected,
                template_used=template_used,
                response_text=response_text,
                response_id=response_id,
                parameters_used=parameters_used or {},  # Nunca None
                fallback_used=fallback_used,
                processing_time_ms=processing_time_ms,
                success=success,
                error_message=error_message,
                context_data=context_data if context_data is not None else {}
            )
            
            logger.info(f"Logged interaction {interaction.id} for {phone_number}")
            return interaction
            
        except Exception as e:
            logger.error(f"Error logging interaction: {str(e)}")
            raise
    
    def save_context_to_redis(
        self,
        phone_number: str,
        context_data: Dict[str, Any],
        ttl: int = 3600
    ) -> bool:
        """
        Save conversation context to cache (Redis if configured, otherwise LocMemCache).
        
        This method stores conversation context to maintain state between messages.
        Uses Redis if AZURE_REDIS_CONNECTIONSTRING is configured, otherwise uses LocMemCache.
        
        Args:
            phone_number: User's phone number
            context_data: Context data to save
            ttl: Time to live in seconds (default: 1 hour)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_key = f"whatsapp_context:{phone_number}"
            cache.set(cache_key, context_data, ttl)
            logger.info(f"Saved context to cache for {phone_number}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving context to cache: {str(e)}")
            return False
    
    def get_context_from_redis(self, phone_number: str) -> Dict[str, Any]:
        """
        Get conversation context from cache (Redis if configured, otherwise LocMemCache).
        
        This method retrieves conversation context to maintain state between messages.
        Uses Redis if AZURE_REDIS_CONNECTIONSTRING is configured, otherwise uses LocMemCache.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            Context data dictionary (empty if not found)
        """
        try:
            cache_key = f"whatsapp_context:{phone_number}"
            context_data = cache.get(cache_key)
            
            if context_data:
                logger.info(f"Retrieved context from cache for {phone_number}")
                return context_data
            else:
                logger.info(f"No context found in cache for {phone_number}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting context from cache: {str(e)}")
            return {}
    
    def update_context(
        self,
        phone_number: str,
        new_data: Dict[str, Any],
        ttl: int = 3600
    ) -> bool:
        """
        Update conversation context in cache (Redis if configured, otherwise LocMemCache).
        
        This method updates existing conversation context with new data.
        Uses Redis if AZURE_REDIS_CONNECTIONSTRING is configured, otherwise uses LocMemCache.
        
        Args:
            phone_number: User's phone number
            new_data: New context data to add/update
            ttl: Time to live in seconds (default: 1 hour)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            current_context = self.get_context_from_redis(phone_number)
            current_context.update(new_data)
            
            return self.save_context_to_redis(phone_number, current_context, ttl)
            
        except Exception as e:
            logger.error(f"Error updating context: {str(e)}")
            return False 

    def get_context(self, *args, **kwargs):
        return {}
    def log_context(self, *args, **kwargs):
        pass 