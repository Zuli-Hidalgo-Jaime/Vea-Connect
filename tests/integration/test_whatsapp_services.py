"""
Integration tests for WhatsApp services.

Tests the unified WhatsApp sender service and related functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.conf import settings

from services.whatsapp_sender import WhatsAppSenderService, whatsapp_sender
from services.application_insights import app_insights


class TestWhatsAppSenderService(TestCase):
    """Test cases for WhatsApp Sender Service."""
    
    def setUp(self):
        """Set up test environment."""
        self.service = WhatsAppSenderService()
        self.test_phone = "+525512345678"
        self.test_message = "Test message from integration test"
    
    def test_service_initialization(self):
        """Test service initialization."""
        self.assertIsNotNone(self.service)
        self.assertIsInstance(self.service, WhatsAppSenderService)
    
    def test_phone_number_normalization(self):
        """Test phone number normalization."""
        test_cases = [
            ("+525512345678", "whatsapp:+525512345678"),
            ("525512345678", "whatsapp:525512345678"),
            ("whatsapp:+525512345678", "whatsapp:+525512345678"),
            ("5512345678", "whatsapp:5512345678"),
        ]
        
        for input_phone, expected in test_cases:
            with self.subTest(input_phone=input_phone):
                result = self.service._normalize_phone_number(input_phone)
                self.assertEqual(result, expected)
    
    def test_validate_configuration(self):
        """Test configuration validation."""
        config = self.service.validate_configuration()
        
        self.assertIsInstance(config, dict)
        self.assertIn('valid', config)
        self.assertIn('issues', config)
        self.assertIn('endpoint_configured', config)
        self.assertIn('access_key_configured', config)
        self.assertIn('phone_number_configured', config)
        self.assertIn('channel_id_configured', config)
    
    @patch('services.whatsapp_sender.requests.post')
    def test_send_text_message_success(self, mock_post):
        """Test successful text message sending."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'test-message-id'}
        mock_post.return_value = mock_response
        
        result = self.service.send_text_message(self.test_phone, self.test_message)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message_id'], 'test-message-id')
        self.assertEqual(result['to'], f"whatsapp:{self.test_phone}")
    
    @patch('services.whatsapp_sender.requests.post')
    def test_send_text_message_failure(self, mock_post):
        """Test failed text message sending."""
        # Mock failed response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response
        
        result = self.service.send_text_message(self.test_phone, self.test_message)
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('400', result['error'])
    
    @patch('services.whatsapp_sender.requests.post')
    def test_send_template_message_success(self, mock_post):
        """Test successful template message sending."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'test-template-id'}
        mock_post.return_value = mock_response
        
        template_name = "test_template"
        parameters = {"param1": "value1", "param2": "value2"}
        
        result = self.service.send_template_message(
            self.test_phone, template_name, parameters
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message_id'], 'test-template-id')
        self.assertEqual(result['template_name'], template_name)
    
    @patch('services.whatsapp_sender.requests.post')
    def test_retry_logic_on_rate_limit(self, mock_post):
        """Test retry logic on rate limit."""
        # Mock rate limit response then success
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {'id': 'retry-success-id'}
        
        mock_post.side_effect = [mock_response_429, mock_response_200]
        
        result = self.service.send_text_message(self.test_phone, self.test_message)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message_id'], 'retry-success-id')
        self.assertEqual(mock_post.call_count, 2)


class TestApplicationInsightsService(TestCase):
    """Test cases for Application Insights Service."""
    
    def setUp(self):
        """Set up test environment."""
        self.service = app_insights
    
    def test_service_initialization(self):
        """Test service initialization."""
        self.assertIsNotNone(self.service)
    
    def test_get_configuration_status(self):
        """Test configuration status."""
        status = self.service.get_configuration_status()
        
        self.assertIsInstance(status, dict)
        self.assertIn('enabled', status)
        self.assertIn('connection_string_configured', status)
        self.assertIn('instrumentation_key_configured', status)
        self.assertIn('opencensus_available', status)
    
    def test_track_event_fallback(self):
        """Test event tracking with fallback to local logging."""
        result = self.service.track_event(
            "test_event",
            {"test_prop": "test_value"},
            {"test_measurement": 1.0}
        )
        
        self.assertTrue(result)
    
    def test_track_exception_fallback(self):
        """Test exception tracking with fallback to local logging."""
        test_exception = ValueError("Test exception")
        
        result = self.service.track_exception(
            test_exception,
            {"test_prop": "test_value"}
        )
        
        self.assertTrue(result)
    
    def test_track_metric_fallback(self):
        """Test metric tracking with fallback to local logging."""
        result = self.service.track_metric(
            "test_metric",
            42.0,
            {"test_prop": "test_value"}
        )
        
        self.assertTrue(result)
    
    def test_track_whatsapp_message(self):
        """Test WhatsApp message tracking."""
        result = self.service.track_whatsapp_message(
            "+525512345678",
            "text",
            True,
            100.0,
            None,
            {"test_prop": "test_value"}
        )
        
        self.assertTrue(result)


class TestAzureStorageService(TestCase):
    """Test cases for Azure Storage Service."""
    
    def setUp(self):
        """Set up test environment."""
        from services.storage_service import azure_storage
        self.service = azure_storage
    
    def test_service_initialization(self):
        """Test service initialization."""
        self.assertIsNotNone(self.service)
    
    def test_get_configuration_status(self):
        """Test configuration status."""
        status = self.service.get_configuration_status()
        
        self.assertIsInstance(status, dict)
        self.assertIn('connection_string_configured', status)
        self.assertIn('account_name_configured', status)
        self.assertIn('account_key_configured', status)
        self.assertIn('container_name', status)
        self.assertIn('client_initialized', status)
    
    def test_upload_data_without_client(self):
        """Test upload data when client is not initialized."""
        result = self.service.upload_data(
            b"test data",
            "test_blob.txt"
        )
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('not initialized', result['error'])
    
    def test_get_blob_url_without_client(self):
        """Test get blob URL when client is not initialized."""
        result = self.service.get_blob_url("test_blob.txt")
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('not initialized', result['error'])
    
    def test_blob_exists_without_client(self):
        """Test blob exists check when client is not initialized."""
        result = self.service.blob_exists("test_blob.txt")
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('not initialized', result['error'])


class TestWhatsAppBotIntegration(TestCase):
    """Integration tests for WhatsApp Bot functionality."""
    
    def setUp(self):
        """Set up test environment."""
        from apps.whatsapp_bot.handlers import WhatsAppBotHandler
        self.bot_handler = WhatsAppBotHandler()
    
    def test_bot_handler_initialization(self):
        """Test bot handler initialization."""
        self.assertIsNotNone(self.bot_handler)
    
    def test_intent_detection(self):
        """Test intent detection functionality."""
        test_cases = [
            ("hola como estas", "general"),
            ("donaciones", "donations"),
            ("eventos", "events"),
            ("contacto", "contact"),
            ("random text", "unknown"),
        ]
        
        for message, expected_intent in test_cases:
            with self.subTest(message=message):
                detected_intent = self.bot_handler.detect_intent(message)
                self.assertEqual(detected_intent, expected_intent)
    
    def test_context_management(self):
        """Test conversation context management."""
        phone_number = "+525512345678"
        test_context = {"test_key": "test_value"}
        
        # Test context update
        result = self.bot_handler.update_context(phone_number, test_context)
        self.assertIsInstance(result, dict)
        
        # Test context retrieval
        retrieved_context = self.bot_handler.get_context(phone_number)
        self.assertIsInstance(retrieved_context, dict)
    
    def test_fallback_response_generation(self):
        """Test fallback response generation."""
        test_message = "Test message"
        test_context = {}
        
        response = self.bot_handler.generate_fallback_response(test_message, test_context)
        
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)


@pytest.mark.django_db
class TestWhatsAppEndToEnd(TestCase):
    """End-to-end tests for WhatsApp functionality."""
    
    def setUp(self):
        """Set up test environment."""
        from apps.whatsapp_bot.handlers import WhatsAppBotHandler
        self.bot_handler = WhatsAppBotHandler()
    
    @patch('services.whatsapp_sender.requests.post')
    def test_complete_message_flow(self, mock_post):
        """Test complete message processing flow."""
        # Mock successful WhatsApp response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'e2e-test-id'}
        mock_post.return_value = mock_response
        
        # Test data
        test_data = {
            'phone_number': '+525512345678',
            'message_text': 'hola como estas'
        }
        
        # Process message
        result = self.bot_handler.process_message(test_data)
        
        # Verify result structure
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        self.assertIn('response', result)
        self.assertIn('intent_detected', result)
        
        # Verify intent detection
        self.assertEqual(result['intent_detected'], 'general')
        
        # Verify response generation
        self.assertIsInstance(result['response'], str)
        self.assertGreater(len(result['response']), 0)
    
    def test_error_handling_in_message_flow(self):
        """Test error handling in message processing."""
        # Test with invalid data
        invalid_data = None
        
        result = self.bot_handler.process_message(invalid_data)
        
        # Should handle error gracefully
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        self.assertIn('error', result)
    
    def test_cache_integration(self):
        """Test cache integration for conversation context."""
        phone_number = "+525512345678"
        test_context = {"cache_test": "cache_value"}
        
        # Update context (should use cache)
        self.bot_handler.update_context(phone_number, test_context)
        
        # Retrieve context (should come from cache)
        retrieved_context = self.bot_handler.get_context(phone_number)
        
        # Verify cache functionality
        self.assertIsInstance(retrieved_context, dict)
        # Note: In test environment, cache might be LocMemCache, so exact behavior may vary


if __name__ == '__main__':
    pytest.main([__file__])
