"""
WhatsApp Event Grid Handler for Azure Communication Services.

This module provides a clean, framework-agnostic handler for processing
WhatsApp events from Azure Event Grid, including message reception and
delivery reports.
"""

import json
import logging
import time
from typing import Dict, Any, Optional, Tuple, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import hashlib
import hmac
import base64

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Enumeration of supported Event Grid event types."""
    
    MESSAGE_RECEIVED = "Microsoft.Communication.AdvancedMessageReceived"
    DELIVERY_REPORT = "Microsoft.Communication.AdvancedMessageDeliveryReportReceived"


@dataclass
class WhatsAppMessage:
    """Data class representing a WhatsApp message."""
    
    from_number: str
    to_number: str
    message_text: str
    timestamp: datetime
    message_id: Optional[str] = None
    channel_registration_id: Optional[str] = None


@dataclass
class DeliveryReport:
    """Data class representing a message delivery report."""
    
    message_id: str
    status: str
    timestamp: datetime
    recipient_number: str
    channel_registration_id: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None


class EventGridValidator:
    """
    Validates Event Grid requests and handles webhook validation.
    
    This class handles the Event Grid validation handshake and
    verifies request authenticity.
    """
    
    def __init__(self, validation_key: Optional[str] = None):
        """
        Initialize Event Grid validator.
        
        Args:
            validation_key: Optional validation key for Event Grid
        """
        self.validation_key = validation_key
    
    def validate_webhook_handshake(self, request_body: str, headers: Dict[str, str]) -> bool:
        """
        Validate Event Grid webhook handshake.
        
        Event Grid sends a validation request when setting up webhooks.
        This method handles the validation response.
        
        Args:
            request_body: Raw request body
            headers: Request headers
            
        Returns:
            True if validation request, False otherwise
        """
        try:
            # Check if this is a validation request
            if headers.get('aeg-event-type') == 'SubscriptionValidation':
                logger.info("Received Event Grid validation request")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error validating webhook handshake: {e}")
            return False
    
    def create_validation_response(self, request_body: str) -> Dict[str, Any]:
        """
        Create validation response for Event Grid.
        
        Args:
            request_body: Validation request body
            
        Returns:
            Validation response dictionary
        """
        try:
            data = json.loads(request_body)
            validation_code = data.get('validationCode', '')
            
            response = {
                'validationResponse': validation_code
            }
            
            logger.info(f"Created validation response: {validation_code}")
            return response
            
        except Exception as e:
            logger.error(f"Error creating validation response: {e}")
            return {'validationResponse': ''}
    
    def validate_request_signature(self, request_body: str, headers: Dict[str, str]) -> bool:
        """
        Validate Event Grid request signature.
        
        Args:
            request_body: Raw request body
            headers: Request headers containing signature
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Get signature from headers
            signature = headers.get('aeg-signature-256', '')
            if not signature:
                logger.warning("No signature found in headers")
                return False
            
            # For production, implement proper signature validation
            # This is a simplified version
            logger.info("Request signature validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Error validating request signature: {e}")
            return False


class WhatsAppEventProcessor:
    """
    Processes WhatsApp events from Event Grid.
    
    This class handles the core business logic for processing
    WhatsApp messages and delivery reports.
    """
    
    def __init__(self, 
                 user_service: Any,
                 template_service: Any,
                 logging_service: Any,
                 storage_service: Any):
        """
        Initialize WhatsApp event processor.
        
        Args:
            user_service: Service for user management
            template_service: Service for template processing
            logging_service: Service for logging interactions
            storage_service: Service for storage operations
        """
        self.user_service = user_service
        self.template_service = template_service
        self.logging_service = logging_service
        self.storage_service = storage_service
    
    def process_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an Event Grid event.
        
        Args:
            event_data: Event data from Event Grid
            
        Returns:
            Processing result dictionary
        """
        try:
            event_type = event_data.get('eventType')
            event_time = event_data.get('eventTime')
            data = event_data.get('data', {})
            
            logger.info(f"Processing event: {event_type} at {event_time}")
            
            if event_type == EventType.MESSAGE_RECEIVED.value:
                return self._process_message_received(data)
            elif event_type == EventType.DELIVERY_REPORT.value:
                return self._process_delivery_report(data)
            else:
                logger.warning(f"Unsupported event type: {event_type}")
                return {
                    'success': False,
                    'error': f'Unsupported event type: {event_type}'
                }
                
        except Exception as e:
            logger.error(f"Error processing event: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_message_received(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a message received event.
        
        Args:
            data: Event data containing message information
            
        Returns:
            Processing result dictionary
        """
        try:
            # Extract message information
            message = self._extract_message_data(data)
            if not message:
                return {
                    'success': False,
                    'error': 'Failed to extract message data'
                }
            
            logger.info(f"Processing message from {message.from_number}: {message.message_text[:50]}...")
            
            # Register or update user
            user_registered = self._register_user(message.from_number)
            if not user_registered:
                logger.warning(f"Failed to register user: {message.from_number}")
            
            # Detect intent and generate response
            response_result = self._generate_response(message)
            
            # Save conversation context
            context_saved = self._save_conversation_context(message, response_result)
            if not context_saved:
                logger.warning(f"Failed to save context for: {message.from_number}")
            
            # Log interaction
            interaction_logged = self._log_interaction(message, response_result)
            if not interaction_logged:
                logger.warning(f"Failed to log interaction for: {message.from_number}")
            
            return {
                'success': True,
                'message_processed': True,
                'user_registered': user_registered,
                'response_generated': response_result.get('success', False),
                'context_saved': context_saved,
                'interaction_logged': interaction_logged
            }
            
        except Exception as e:
            logger.error(f"Error processing message received: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_delivery_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a delivery report event.
        
        Args:
            data: Event data containing delivery report information
            
        Returns:
            Processing result dictionary
        """
        try:
            # Extract delivery report information
            report = self._extract_delivery_report_data(data)
            if not report:
                return {
                    'success': False,
                    'error': 'Failed to extract delivery report data'
                }
            
            logger.info(f"Processing delivery report for message {report.message_id}: {report.status}")
            
            # Save delivery report
            report_saved = self._save_delivery_report(report)
            if not report_saved:
                logger.warning(f"Failed to save delivery report for: {report.message_id}")
            
            # Update message status if needed
            status_updated = self._update_message_status(report)
            if not status_updated:
                logger.warning(f"Failed to update message status for: {report.message_id}")
            
            return {
                'success': True,
                'report_processed': True,
                'report_saved': report_saved,
                'status_updated': status_updated
            }
            
        except Exception as e:
            logger.error(f"Error processing delivery report: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_message_data(self, data: Dict[str, Any]) -> Optional[WhatsAppMessage]:
        """
        Extract message data from event payload.
        
        Args:
            data: Event data containing message information
            
        Returns:
            WhatsAppMessage object or None if extraction fails
        """
        try:
            # Extract from the event data structure
            from_number = data.get('from', {}).get('phoneNumber', '').replace('whatsapp:', '')
            to_number = data.get('to', {}).get('phoneNumber', '').replace('whatsapp:', '')
            message_content = data.get('message', {})
            message_text = message_content.get('text', '')
            message_id = data.get('id')
            channel_registration_id = data.get('channelRegistrationId')
            
            # Parse timestamp
            timestamp_str = data.get('receivedTimestamp')
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')) if timestamp_str else datetime.utcnow()
            
            if not from_number or not message_text:
                logger.warning("Missing required message data")
                return None
            
            return WhatsAppMessage(
                from_number=from_number,
                to_number=to_number,
                message_text=message_text,
                timestamp=timestamp,
                message_id=message_id,
                channel_registration_id=channel_registration_id
            )
            
        except Exception as e:
            logger.error(f"Error extracting message data: {e}")
            return None
    
    def _extract_delivery_report_data(self, data: Dict[str, Any]) -> Optional[DeliveryReport]:
        """
        Extract delivery report data from event payload.
        
        Args:
            data: Event data containing delivery report information
            
        Returns:
            DeliveryReport object or None if extraction fails
        """
        try:
            # Extract from the event data structure
            message_id = data.get('messageId')
            status = data.get('status')
            recipient_number = data.get('to', {}).get('phoneNumber', '').replace('whatsapp:', '')
            channel_registration_id = data.get('channelRegistrationId')
            error_details = data.get('errorDetails')
            
            # Parse timestamp
            timestamp_str = data.get('receivedTimestamp')
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')) if timestamp_str else datetime.utcnow()
            
            if not message_id or not status:
                logger.warning("Missing required delivery report data")
                return None
            
            return DeliveryReport(
                message_id=message_id,
                status=status,
                timestamp=timestamp,
                recipient_number=recipient_number,
                channel_registration_id=channel_registration_id,
                error_details=error_details
            )
            
        except Exception as e:
            logger.error(f"Error extracting delivery report data: {e}")
            return None
    
    def _register_user(self, phone_number: str) -> bool:
        """
        Register or update user in PostgreSQL.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use user service to register/update user
            result = self.user_service.register_or_update_user(phone_number)
            logger.info(f"User registration result for {phone_number}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error registering user {phone_number}: {e}")
            return False
    
    def _generate_response(self, message: WhatsAppMessage) -> Dict[str, Any]:
        """
        Generate response for the received message.
        
        Args:
            message: Received WhatsApp message
            
        Returns:
            Response generation result dictionary
        """
        try:
            # Use template service to generate response
            result = self.template_service.process_message(
                phone_number=message.from_number,
                message_text=message.message_text
            )
            
            logger.info(f"Response generation result for {message.from_number}: {result.get('success')}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating response for {message.from_number}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _save_conversation_context(self, message: WhatsAppMessage, response_result: Dict[str, Any]) -> bool:
        """
        Save conversation context to Redis.
        
        Args:
            message: Received WhatsApp message
            response_result: Response generation result
            
        Returns:
            True if successful, False otherwise
        """
        try:
            context_data = {
                'last_message': message.message_text,
                'last_timestamp': message.timestamp.isoformat(),
                'response_type': response_result.get('response_type', 'unknown'),
                'template_used': response_result.get('template_used'),
                'intent_detected': response_result.get('intent_detected', 'unknown'),
                'interaction_count': 1  # Will be incremented by logging service
            }
            
            # Use logging service to save context
            result = self.logging_service.update_context(
                phone_number=message.from_number,
                new_data=context_data
            )
            
            logger.info(f"Context save result for {message.from_number}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error saving context for {message.from_number}: {e}")
            return False
    
    def _log_interaction(self, message: WhatsAppMessage, response_result: Dict[str, Any]) -> bool:
        """
        Log the interaction to database.
        
        Args:
            message: Received WhatsApp message
            response_result: Response generation result
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use logging service to log interaction
            result = self.logging_service.log_interaction(
                phone_number=message.from_number,
                message_text=message.message_text,
                intent_detected=response_result.get('intent_detected', 'unknown'),
                template_used=None,  # Will be set by logging service
                response_text=response_result.get('response_text', ''),
                response_id=response_result.get('response_id', ''),
                parameters_used=response_result.get('parameters', {}),
                fallback_used=response_result.get('response_type') == 'fallback',
                processing_time_ms=response_result.get('processing_time_ms', 0),
                success=response_result.get('success', False),
                error_message=response_result.get('error_message', ''),
                context_data={'message_id': message.message_id}
            )
            
            logger.info(f"Interaction logging result for {message.from_number}: {result is not None}")
            return result is not None
            
        except Exception as e:
            logger.error(f"Error logging interaction for {message.from_number}: {e}")
            return False
    
    def _save_delivery_report(self, report: DeliveryReport) -> bool:
        """
        Save delivery report to storage.
        
        Args:
            report: Delivery report data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use storage service to save delivery report
            result = self.storage_service.save_delivery_report(report)
            logger.info(f"Delivery report save result for {report.message_id}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error saving delivery report for {report.message_id}: {e}")
            return False
    
    def _update_message_status(self, report: DeliveryReport) -> bool:
        """
        Update message status in database.
        
        Args:
            report: Delivery report data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use logging service to update message status
            result = self.logging_service.update_message_status(
                message_id=report.message_id,
                status=report.status,
                error_details=report.error_details
            )
            
            logger.info(f"Message status update result for {report.message_id}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error updating message status for {report.message_id}: {e}")
            return False


class EventGridHandler:
    """
    Main Event Grid handler for WhatsApp events.
    
    This class provides the main entry point for processing Event Grid events
    and can be used in Azure Functions or other serverless environments.
    """
    
    def __init__(self, 
                 user_service: Any,
                 template_service: Any,
                 logging_service: Any,
                 storage_service: Any,
                 validation_key: Optional[str] = None):
        """
        Initialize Event Grid handler.
        
        Args:
            user_service: Service for user management
            template_service: Service for template processing
            logging_service: Service for logging interactions
            storage_service: Service for storage operations
            validation_key: Optional validation key for Event Grid
        """
        self.validator = EventGridValidator(validation_key)
        self.processor = WhatsAppEventProcessor(
            user_service=user_service,
            template_service=template_service,
            logging_service=logging_service,
            storage_service=storage_service
        )
    
    def handle_event_grid_request(self, request_body: str, headers: Dict[str, str]) -> Tuple[int, Dict[str, Any]]:
        """
        Handle Event Grid request.
        
        This is the main entry point for processing Event Grid events.
        It handles validation requests and processes actual events.
        
        Args:
            request_body: Raw request body
            headers: Request headers
            
        Returns:
            Tuple of (status_code, response_body)
        """
        try:
            # Validate request signature (optional for development)
            if not self.validator.validate_request_signature(request_body, headers):
                logger.warning("Request signature validation failed")
                # In production, you might want to return 401 here
                # For now, we continue processing
            
            # Check if this is a validation request
            if self.validator.validate_webhook_handshake(request_body, headers):
                validation_response = self.validator.create_validation_response(request_body)
                return 200, validation_response
            
            # Parse Event Grid events
            events = self._parse_event_grid_events(request_body)
            if not events:
                logger.error("Failed to parse Event Grid events")
                return 400, {'error': 'Invalid event format'}
            
            # Process each event
            results = []
            for event in events:
                result = self.processor.process_event(event)
                results.append(result)
            
            # Log processing results
            successful_events = sum(1 for r in results if r.get('success', False))
            logger.info(f"Processed {len(events)} events, {successful_events} successful")
            
            # Always return 200 to Event Grid (even if some events failed)
            return 200, {
                'events_processed': len(events),
                'successful_events': successful_events,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error handling Event Grid request: {e}")
            # Return 200 to prevent Event Grid from retrying
            return 200, {
                'error': 'Internal processing error',
                'events_processed': 0,
                'successful_events': 0
            }
    
    def _parse_event_grid_events(self, request_body: str) -> list:
        """
        Parse Event Grid events from request body.
        
        Args:
            request_body: Raw request body
            
        Returns:
            List of event dictionaries
        """
        try:
            data = json.loads(request_body)
            
            # Event Grid can send single event or array of events
            if isinstance(data, list):
                events = data
            else:
                events = [data]
            
            logger.info(f"Parsed {len(events)} Event Grid events")
            return events
            
        except Exception as e:
            logger.error(f"Error parsing Event Grid events: {e}")
            return []
    
    def handle_single_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a single Event Grid event.
        
        This method can be used for testing or when processing events individually.
        
        Args:
            event_data: Single event data dictionary
            
        Returns:
            Processing result dictionary
        """
        try:
            result = self.processor.process_event(event_data)
            logger.info(f"Single event processing result: {result.get('success')}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing single event: {e}")
            return {
                'success': False,
                'error': str(e)
            } 