"""
Unit tests for WhatsApp Event Grid Handler.

This module contains comprehensive tests for the Event Grid handler
including event processing, validation, and Azure Function integration.
"""

import json
import logging
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from .event_grid_handler import (
    EventGridHandler,
    EventGridValidator,
    WhatsAppEventProcessor,
    WhatsAppMessage,
    DeliveryReport,
    EventType
)
from .user_service import UserService
from .storage_service import StorageService

logger = logging.getLogger(__name__)


class EventGridValidatorTest(unittest.TestCase):
    """Test cases for Event Grid validator."""
    
    def setUp(self):
        """Set up test data."""
        self.validator = EventGridValidator()
    
    def test_validate_webhook_handshake(self):
        """Test webhook handshake validation."""
        # Test validation request
        headers = {'aeg-event-type': 'SubscriptionValidation'}
        result = self.validator.validate_webhook_handshake('test body', headers)
        self.assertTrue(result)
        
        # Test regular request
        headers = {'aeg-event-type': 'Notification'}
        result = self.validator.validate_webhook_handshake('test body', headers)
        self.assertFalse(result)
    
    def test_create_validation_response(self):
        """Test validation response creation."""
        request_body = '{"validationCode": "test-code-123"}'
        response = self.validator.create_validation_response(request_body)
        
        self.assertIn('validationResponse', response)
        self.assertEqual(response['validationResponse'], 'test-code-123')
    
    def test_validate_request_signature(self):
        """Test request signature validation."""
        headers = {'aeg-signature-256': 'test-signature'}
        result = self.validator.validate_request_signature('test body', headers)
        self.assertTrue(result)
        
        # Test missing signature
        headers = {}
        result = self.validator.validate_request_signature('test body', headers)
        self.assertFalse(result)


class WhatsAppEventProcessorTest(unittest.TestCase):
    """Test cases for WhatsApp event processor."""
    
    def setUp(self):
        """Set up test data."""
        self.user_service = Mock()
        self.template_service = Mock()
        self.logging_service = Mock()
        self.storage_service = Mock()
        
        self.processor = WhatsAppEventProcessor(
            user_service=self.user_service,
            template_service=self.template_service,
            logging_service=self.logging_service,
            storage_service=self.storage_service
        )
    
    def test_process_message_received_event(self):
        """Test processing message received event."""
        event_data = {
            'eventType': EventType.MESSAGE_RECEIVED.value,
            'eventTime': '2024-01-01T12:00:00Z',
            'data': {
                'from': {'phoneNumber': 'whatsapp:+1234567890'},
                'to': {'phoneNumber': 'whatsapp:+0987654321'},
                'message': {'text': 'Test message'},
                'receivedTimestamp': '2024-01-01T12:00:00Z',
                'id': 'test-message-id',
                'channelRegistrationId': 'test-channel-id'
            }
        }
        
        # Mock service responses
        self.user_service.register_or_update_user.return_value = True
        self.template_service.process_message.return_value = {
            'success': True,
            'response_type': 'template',
            'response_id': 'msg-123',
            'intent_detected': 'donations'
        }
        self.logging_service.update_context.return_value = True
        self.logging_service.log_interaction.return_value = Mock()
        
        result = self.processor.process_event(event_data)
        
        self.assertTrue(result['success'])
        self.assertTrue(result['message_processed'])
        self.assertTrue(result['user_registered'])
        self.assertTrue(result['response_generated'])
    
    def test_process_delivery_report_event(self):
        """Test processing delivery report event."""
        event_data = {
            'eventType': EventType.DELIVERY_REPORT.value,
            'eventTime': '2024-01-01T12:00:00Z',
            'data': {
                'messageId': 'test-message-id',
                'status': 'Delivered',
                'receivedTimestamp': '2024-01-01T12:00:00Z',
                'to': {'phoneNumber': 'whatsapp:+1234567890'},
                'channelRegistrationId': 'test-channel-id'
            }
        }
        
        # Mock service responses
        self.storage_service.save_delivery_report.return_value = True
        self.logging_service.update_message_status.return_value = True
        
        result = self.processor.process_event(event_data)
        
        self.assertTrue(result['success'])
        self.assertTrue(result['report_processed'])
        self.assertTrue(result['report_saved'])
        self.assertTrue(result['status_updated'])
    
    def test_extract_message_data(self):
        """Test message data extraction."""
        data = {
            'from': {'phoneNumber': 'whatsapp:+1234567890'},
            'to': {'phoneNumber': 'whatsapp:+0987654321'},
            'message': {'text': 'Test message'},
            'receivedTimestamp': '2024-01-01T12:00:00Z',
            'id': 'test-message-id',
            'channelRegistrationId': 'test-channel-id'
        }
        
        message = self.processor._extract_message_data(data)
        
        self.assertIsNotNone(message)
        self.assertEqual(message.from_number, '+1234567890')
        self.assertEqual(message.message_text, 'Test message')
        self.assertEqual(message.message_id, 'test-message-id')
    
    def test_extract_delivery_report_data(self):
        """Test delivery report data extraction."""
        data = {
            'messageId': 'test-message-id',
            'status': 'Delivered',
            'receivedTimestamp': '2024-01-01T12:00:00Z',
            'to': {'phoneNumber': 'whatsapp:+1234567890'},
            'channelRegistrationId': 'test-channel-id'
        }
        
        report = self.processor._extract_delivery_report_data(data)
        
        self.assertIsNotNone(report)
        self.assertEqual(report.message_id, 'test-message-id')
        self.assertEqual(report.status, 'Delivered')
        self.assertEqual(report.recipient_number, '+1234567890')
    
    def test_unsupported_event_type(self):
        """Test handling of unsupported event types."""
        event_data = {
            'eventType': 'Unsupported.Event.Type',
            'eventTime': '2024-01-01T12:00:00Z',
            'data': {}
        }
        
        result = self.processor.process_event(event_data)
        
        self.assertFalse(result['success'])
        self.assertIn('Unsupported event type', result['error'])


class EventGridHandlerTest(unittest.TestCase):
    """Test cases for Event Grid handler."""
    
    def setUp(self):
        """Set up test data."""
        self.user_service = Mock()
        self.template_service = Mock()
        self.logging_service = Mock()
        self.storage_service = Mock()
        
        self.handler = EventGridHandler(
            user_service=self.user_service,
            template_service=self.template_service,
            logging_service=self.logging_service,
            storage_service=self.storage_service
        )
    
    def test_handle_event_grid_request_validation(self):
        """Test handling validation request."""
        request_body = '{"validationCode": "test-code-123"}'
        headers = {'aeg-event-type': 'SubscriptionValidation'}
        
        status_code, response = self.handler.handle_event_grid_request(request_body, headers)
        
        self.assertEqual(status_code, 200)
        self.assertIn('validationResponse', response)
        self.assertEqual(response['validationResponse'], 'test-code-123')
    
    def test_handle_event_grid_request_events(self):
        """Test handling actual events."""
        event_data = {
            'id': 'test-event-id',
            'eventType': EventType.MESSAGE_RECEIVED.value,
            'eventTime': '2024-01-01T12:00:00Z',
            'data': {
                'from': {'phoneNumber': 'whatsapp:+1234567890'},
                'to': {'phoneNumber': 'whatsapp:+0987654321'},
                'message': {'text': 'Test message'},
                'receivedTimestamp': '2024-01-01T12:00:00Z'
            }
        }
        
        request_body = json.dumps([event_data])
        headers = {'aeg-event-type': 'Notification'}
        
        # Mock processor response
        with patch.object(self.handler.processor, 'process_event') as mock_process:
            mock_process.return_value = {'success': True, 'message_processed': True}
            
            status_code, response = self.handler.handle_event_grid_request(request_body, headers)
            
            self.assertEqual(status_code, 200)
            self.assertEqual(response['events_processed'], 1)
            self.assertEqual(response['successful_events'], 1)
    
    def test_handle_event_grid_request_multiple_events(self):
        """Test handling multiple events."""
        events = [
            {
                'id': 'event-1',
                'eventType': EventType.MESSAGE_RECEIVED.value,
                'eventTime': '2024-01-01T12:00:00Z',
                'data': {'from': {'phoneNumber': 'whatsapp:+1234567890'}, 'message': {'text': 'Test 1'}}
            },
            {
                'id': 'event-2',
                'eventType': EventType.DELIVERY_REPORT.value,
                'eventTime': '2024-01-01T12:00:00Z',
                'data': {'messageId': 'msg-1', 'status': 'Delivered'}
            }
        ]
        
        request_body = json.dumps(events)
        headers = {'aeg-event-type': 'Notification'}
        
        # Mock processor responses
        with patch.object(self.handler.processor, 'process_event') as mock_process:
            mock_process.side_effect = [
                {'success': True, 'message_processed': True},
                {'success': True, 'report_processed': True}
            ]
            
            status_code, response = self.handler.handle_event_grid_request(request_body, headers)
            
            self.assertEqual(status_code, 200)
            self.assertEqual(response['events_processed'], 2)
            self.assertEqual(response['successful_events'], 2)
    
    def test_handle_event_grid_request_error(self):
        """Test handling request with error."""
        request_body = 'invalid json'
        headers = {'aeg-event-type': 'Notification'}
        
        status_code, response = self.handler.handle_event_grid_request(request_body, headers)
        
        self.assertEqual(status_code, 400)
        self.assertIn('error', response)
    
    def test_handle_single_event(self):
        """Test handling single event."""
        event_data = {
            'id': 'test-event-id',
            'eventType': EventType.MESSAGE_RECEIVED.value,
            'eventTime': '2024-01-01T12:00:00Z',
            'data': {
                'from': {'phoneNumber': 'whatsapp:+1234567890'},
                'message': {'text': 'Test message'}
            }
        }
        
        # Mock processor response
        with patch.object(self.handler.processor, 'process_event') as mock_process:
            mock_process.return_value = {'success': True, 'message_processed': True}
            
            result = self.handler.handle_single_event(event_data)
            
            self.assertTrue(result['success'])
            self.assertTrue(result['message_processed'])
    
    def test_parse_event_grid_events_single(self):
        """Test parsing single event."""
        event_data = {'id': 'test-event', 'eventType': 'Test.Event'}
        request_body = json.dumps(event_data)
        
        events = self.handler._parse_event_grid_events(request_body)
        
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['id'], 'test-event')
    
    def test_parse_event_grid_events_multiple(self):
        """Test parsing multiple events."""
        events_data = [
            {'id': 'event-1', 'eventType': 'Test.Event.1'},
            {'id': 'event-2', 'eventType': 'Test.Event.2'}
        ]
        request_body = json.dumps(events_data)
        
        events = self.handler._parse_event_grid_events(request_body)
        
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]['id'], 'event-1')
        self.assertEqual(events[1]['id'], 'event-2')


class WhatsAppMessageTest(unittest.TestCase):
    """Test cases for WhatsApp message data class."""
    
    def test_whatsapp_message_creation(self):
        """Test WhatsApp message creation."""
        message = WhatsAppMessage(
            from_number='+1234567890',
            to_number='+0987654321',
            message_text='Test message',
            timestamp=datetime.utcnow(),
            message_id='test-message-id',
            channel_registration_id='test-channel-id'
        )
        
        self.assertEqual(message.from_number, '+1234567890')
        self.assertEqual(message.to_number, '+0987654321')
        self.assertEqual(message.message_text, 'Test message')
        self.assertEqual(message.message_id, 'test-message-id')
        self.assertEqual(message.channel_registration_id, 'test-channel-id')


class DeliveryReportTest(unittest.TestCase):
    """Test cases for delivery report data class."""
    
    def test_delivery_report_creation(self):
        """Test delivery report creation."""
        report = DeliveryReport(
            message_id='test-message-id',
            status='Delivered',
            timestamp=datetime.utcnow(),
            recipient_number='+1234567890',
            channel_registration_id='test-channel-id',
            error_details={'code': 'test-error'}
        )
        
        self.assertEqual(report.message_id, 'test-message-id')
        self.assertEqual(report.status, 'Delivered')
        self.assertEqual(report.recipient_number, '+1234567890')
        self.assertEqual(report.channel_registration_id, 'test-channel-id')
        self.assertEqual(report.error_details['code'], 'test-error')


class EventGridIntegrationTest(unittest.TestCase):
    """Integration tests for Event Grid handler."""
    
    def setUp(self):
        """Set up test data."""
        self.user_service = Mock()
        self.template_service = Mock()
        self.logging_service = Mock()
        self.storage_service = Mock()
        
        self.handler = EventGridHandler(
            user_service=self.user_service,
            template_service=self.template_service,
            logging_service=self.logging_service,
            storage_service=self.storage_service
        )
    
    def test_full_message_processing_flow(self):
        """Test full message processing flow."""
        # Mock service responses
        self.user_service.register_or_update_user.return_value = True
        self.template_service.process_message.return_value = {
            'success': True,
            'response_type': 'template',
            'response_id': 'msg-123',
            'intent_detected': 'donations',
            'response_text': 'Template response',
            'parameters': {'customer_name': 'Test User'},
            'processing_time_ms': 150.5
        }
        self.logging_service.update_context.return_value = True
        self.logging_service.log_interaction.return_value = Mock()
        
        # Create test event
        event_data = {
            'id': 'test-event-id',
            'eventType': EventType.MESSAGE_RECEIVED.value,
            'eventTime': '2024-01-01T12:00:00Z',
            'data': {
                'from': {'phoneNumber': 'whatsapp:+1234567890'},
                'to': {'phoneNumber': 'whatsapp:+0987654321'},
                'message': {'text': 'I need donation information'},
                'receivedTimestamp': '2024-01-01T12:00:00Z',
                'id': 'test-message-id',
                'channelRegistrationId': 'test-channel-id'
            }
        }
        
        # Process event
        result = self.handler.handle_single_event(event_data)
        
        # Verify results
        self.assertTrue(result['success'])
        self.assertTrue(result['message_processed'])
        
        # Verify service calls
        self.user_service.register_or_update_user.assert_called_once_with('+1234567890')
        self.template_service.process_message.assert_called_once_with('+1234567890', 'I need donation information')
        self.logging_service.update_context.assert_called_once()
        self.logging_service.log_interaction.assert_called_once()
    
    def test_full_delivery_report_flow(self):
        """Test full delivery report processing flow."""
        # Mock service responses
        self.storage_service.save_delivery_report.return_value = True
        self.logging_service.update_message_status.return_value = True
        
        # Create test event
        event_data = {
            'id': 'test-event-id',
            'eventType': EventType.DELIVERY_REPORT.value,
            'eventTime': '2024-01-01T12:00:00Z',
            'data': {
                'messageId': 'test-message-id',
                'status': 'Delivered',
                'receivedTimestamp': '2024-01-01T12:00:00Z',
                'to': {'phoneNumber': 'whatsapp:+1234567890'},
                'channelRegistrationId': 'test-channel-id'
            }
        }
        
        # Process event
        result = self.handler.handle_single_event(event_data)
        
        # Verify results
        self.assertTrue(result['success'])
        self.assertTrue(result['report_processed'])
        
        # Verify service calls
        self.storage_service.save_delivery_report.assert_called_once()
        self.logging_service.update_message_status.assert_called_once()


class EventGridErrorHandlingTest(unittest.TestCase):
    """Test cases for error handling in Event Grid handler."""
    
    def setUp(self):
        """Set up test data."""
        self.user_service = Mock()
        self.template_service = Mock()
        self.logging_service = Mock()
        self.storage_service = Mock()
        
        self.handler = EventGridHandler(
            user_service=self.user_service,
            template_service=self.template_service,
            logging_service=self.logging_service,
            storage_service=self.storage_service
        )
    
    def test_service_failure_handling(self):
        """Test handling of service failures."""
        # Mock service failures
        self.user_service.register_or_update_user.return_value = False
        self.template_service.process_message.return_value = {
            'success': False,
            'error': 'Service unavailable'
        }
        self.logging_service.update_context.return_value = False
        self.logging_service.log_interaction.return_value = None
        
        # Create test event
        event_data = {
            'id': 'test-event-id',
            'eventType': EventType.MESSAGE_RECEIVED.value,
            'eventTime': '2024-01-01T12:00:00Z',
            'data': {
                'from': {'phoneNumber': 'whatsapp:+1234567890'},
                'message': {'text': 'Test message'},
                'receivedTimestamp': '2024-01-01T12:00:00Z'
            }
        }
        
        # Process event
        result = self.handler.handle_single_event(event_data)
        
        # Should still return success to prevent Event Grid retries
        self.assertTrue(result['success'])
        self.assertFalse(result['user_registered'])
        self.assertFalse(result['response_generated'])
    
    def test_malformed_event_handling(self):
        """Test handling of malformed events."""
        # Create malformed event
        event_data = {
            'id': 'test-event-id',
            'eventType': EventType.MESSAGE_RECEIVED.value,
            'eventTime': '2024-01-01T12:00:00Z',
            'data': {
                # Missing required fields
            }
        }
        
        # Process event
        result = self.handler.handle_single_event(event_data)
        
        # Should handle gracefully
        self.assertTrue(result['success'])
        self.assertFalse(result['message_processed'])
    
    def test_exception_handling(self):
        """Test handling of exceptions."""
        # Mock service to raise exception
        self.user_service.register_or_update_user.side_effect = Exception("Database error")
        
        # Create test event
        event_data = {
            'id': 'test-event-id',
            'eventType': EventType.MESSAGE_RECEIVED.value,
            'eventTime': '2024-01-01T12:00:00Z',
            'data': {
                'from': {'phoneNumber': 'whatsapp:+1234567890'},
                'message': {'text': 'Test message'},
                'receivedTimestamp': '2024-01-01T12:00:00Z'
            }
        }
        
        # Process event
        result = self.handler.handle_single_event(event_data)
        
        # Should handle exception gracefully
        self.assertTrue(result['success'])
        self.assertIn('error', result)


if __name__ == '__main__':
    unittest.main() 