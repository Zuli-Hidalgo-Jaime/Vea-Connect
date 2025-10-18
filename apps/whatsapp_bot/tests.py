"""
Unit tests for WhatsApp Bot functionality.

This module contains comprehensive tests for all WhatsApp bot components
including handlers, services, views, and models.
"""

import json
import unittest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import WhatsAppTemplate, WhatsAppInteraction, WhatsAppContext, DataSource
from .handlers import WhatsAppBotHandler
from .services import ACSService, DataRetrievalService, TemplateService, LoggingService

User = get_user_model()


class WhatsAppTemplateModelTest(TestCase):
    """Test cases for WhatsAppTemplate model."""
    
    def setUp(self):
        """Set up test data."""
        self.template = WhatsAppTemplate.objects.create(
            template_name='vea_info_donativos',
            template_id='donations_template_001',
            language='es',
            category='donations',
            parameters=['customer_name', 'bank_name', 'beneficiary_name', 'account_number', 'clabe_number', 'contact_name', 'contact_phone'],
            is_active=True
        )
    
    def test_template_creation(self):
        """Test template creation."""
        self.assertEqual(self.template.template_name, 'vea_info_donativos')
        self.assertEqual(self.template.category, 'donations')
        self.assertTrue(self.template.is_active)
    
    def test_template_str_representation(self):
        """Test string representation."""
        expected = 'vea_info_donativos (donations)'
        self.assertEqual(str(self.template), expected)
    
    def test_template_parameters(self):
        """Test template parameters."""
        expected_params = ['customer_name', 'bank_name', 'beneficiary_name', 'account_number', 'clabe_number', 'contact_name', 'contact_phone']
        self.assertEqual(self.template.parameters, expected_params)


class WhatsAppInteractionModelTest(TestCase):
    """Test cases for WhatsAppInteraction model."""
    
    def setUp(self):
        """Set up test data."""
        self.template = WhatsAppTemplate.objects.create(
            template_name='vea_info_donativos',
            template_id='donations_template_001',
            language='es',
            category='donations',
            parameters=['customer_name'],
            is_active=True
        )
        
        self.interaction = WhatsAppInteraction.objects.create(
            phone_number='+1234567890',
            message_text='I need donation information',
            intent_detected='donations',
            template_used=self.template,
            response_text='Template message sent',
            response_id='msg_001',
            parameters_used={'customer_name': 'John Doe'},
            fallback_used=False,
            processing_time_ms=150.5,
            success=True
        )
    
    def test_interaction_creation(self):
        """Test interaction creation."""
        self.assertEqual(self.interaction.phone_number, '+1234567890')
        self.assertEqual(self.interaction.intent_detected, 'donations')
        self.assertTrue(self.interaction.success)
        self.assertFalse(self.interaction.fallback_used)
    
    def test_interaction_str_representation(self):
        """Test string representation."""
        self.assertIn('+1234567890', str(self.interaction))
        self.assertIn('Interaction', str(self.interaction))


class ACSServiceTest(TestCase):
    """Test cases for ACS service."""
    
    def setUp(self):
        """Set up test data."""
        self.acs_service = ACSService()
    
    @patch('apps.whatsapp_bot.services.requests.post')
    def test_send_template_message_success(self, mock_post):
        """Test successful template message sending."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.json.return_value = {'id': 'msg_123'}
        mock_post.return_value = mock_response
        
        result = self.acs_service.send_template_message(
            to_phone='+1234567890',
            template_name='vea_info_donativos',
            parameters={'customer_name': 'John Doe'}
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message_id'], 'msg_123')
        self.assertEqual(result['status'], 'accepted')
    
    @patch('apps.whatsapp_bot.services.requests.post')
    def test_send_template_message_failure(self, mock_post):
        """Test failed template message sending."""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = 'Bad Request'
        mock_post.return_value = mock_response
        
        with self.assertRaises(Exception):
            self.acs_service.send_template_message(
                to_phone='+1234567890',
                template_name='vea_info_donativos',
                parameters={'customer_name': 'John Doe'}
            )
    
    @patch('apps.whatsapp_bot.services.requests.post')
    def test_send_text_message_success(self, mock_post):
        """Test successful text message sending."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.json.return_value = {'id': 'msg_456'}
        mock_post.return_value = mock_response
        
        result = self.acs_service.send_text_message(
            to_phone='+1234567890',
            text='Hello, how can I help you?'
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message_id'], 'msg_456')
        self.assertEqual(result['status'], 'accepted')


class DataRetrievalServiceTest(TestCase):
    """Test cases for data retrieval service."""
    
    def setUp(self):
        """Set up test data."""
        self.data_service = DataRetrievalService()
    
    @patch('apps.whatsapp_bot.services.cache.get')
    @patch('apps.whatsapp_bot.services.cache.set')
    def test_get_donation_info_cached(self, mock_cache_set, mock_cache_get):
        """Test getting donation info from cache."""
        cached_data = {
            'customer_name': 'John Doe',
            'bank_name': 'Banco Azteca',
            'beneficiary_name': 'John Doe',
            'account_number': '1234567890',
            'clabe_number': '012345678901234567',
            'contact_name': 'John Doe',
            'contact_phone': '+525512345678'
        }
        mock_cache_get.return_value = cached_data
        
        result = self.data_service.get_donation_info('John Doe')
        
        self.assertEqual(result, cached_data)
        mock_cache_get.assert_called_once()
    
    @patch('apps.whatsapp_bot.services.cache.get')
    @patch('apps.whatsapp_bot.services.cache.set')
    @patch('apps.whatsapp_bot.services.connection.cursor')
    def test_get_donation_info_database(self, mock_cursor, mock_cache_set, mock_cache_get):
        """Test getting donation info from database."""
        mock_cache_get.return_value = None
        
        # Mock database cursor
        mock_cursor_instance = Mock()
        mock_cursor.return_value.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchone.return_value = (
            'doc_001', 1000.0, '2024-01-01', 'donation', 'Banco Azteca',
            '1234567890', '012345678901234567', 'John Doe', '+525512345678'
        )
        
        result = self.data_service.get_donation_info('John Doe')
        
        self.assertEqual(result['customer_name'], 'John Doe')
        self.assertEqual(result['bank_name'], 'Banco Azteca')
        mock_cache_set.assert_called_once()


class TemplateServiceTest(TestCase):
    """Test cases for template service."""
    
    def setUp(self):
        """Set up test data."""
        self.acs_service = Mock()
        self.data_service = Mock()
        self.template_service = TemplateService(self.acs_service, self.data_service)
        
        # Create test template
        self.template = WhatsAppTemplate.objects.create(
            template_name='vea_info_donativos',
            template_id='donations_template_001',
            language='es',
            category='donations',
            parameters=['customer_name', 'bank_name'],
            is_active=True
        )
    
    def test_detect_intent_donations(self):
        """Test donation intent detection."""
        intent, data = self.template_service.detect_intent('I need donation information')
        self.assertEqual(intent, 'donations')
        self.assertIn('customer_name', data)
    
    def test_detect_intent_ministry(self):
        """Test ministry intent detection."""
        intent, data = self.template_service.detect_intent('I need ministry contact')
        self.assertEqual(intent, 'ministry')
        self.assertIn('ministry_name', data)
    
    def test_detect_intent_events(self):
        """Test events intent detection."""
        intent, data = self.template_service.detect_intent('I need event information')
        self.assertEqual(intent, 'events')
        self.assertIn('event_name', data)
    
    def test_detect_intent_unknown(self):
        """Test unknown intent detection."""
        intent, data = self.template_service.detect_intent('Random message')
        self.assertEqual(intent, 'unknown')
        self.assertEqual(data, {})
    
    def test_get_template_for_intent(self):
        """Test getting template for intent."""
        # Reload templates to include the one we created
        self.template_service.templates = {self.template.template_name: self.template}
        
        template = self.template_service.get_template_for_intent('donations')
        self.assertEqual(template, self.template)
    
    def test_prepare_template_parameters(self):
        """Test parameter preparation."""
        intent_data = {'customer_name': 'John Doe'}
        
        # Mock data service response
        self.data_service.get_donation_info.return_value = {
            'customer_name': 'John Doe',
            'bank_name': 'Banco Azteca',
            'beneficiary_name': 'John Doe',
            'account_number': '1234567890',
            'clabe_number': '012345678901234567',
            'contact_name': 'John Doe',
            'contact_phone': '+525512345678'
        }
        
        parameters = self.template_service.prepare_template_parameters(
            self.template, intent_data
        )
        
        self.assertEqual(parameters['customer_name'], 'John Doe')
        self.assertEqual(parameters['bank_name'], 'Banco Azteca')


class WhatsAppBotHandlerTest(TestCase):
    """Test cases for WhatsApp bot handler."""
    
    def setUp(self):
        """Set up test data."""
        self.handler = WhatsAppBotHandler()
        
        # Create test template
        self.template = WhatsAppTemplate.objects.create(
            template_name='vea_info_donativos',
            template_id='donations_template_001',
            language='es',
            category='donations',
            parameters=['customer_name', 'bank_name'],
            is_active=True
        )
    
    @patch.object(WhatsAppBotHandler, '_try_template_response')
    @patch.object(WhatsAppBotHandler, '_try_openai_fallback')
    def test_process_message_template_success(self, mock_fallback, mock_template):
        """Test successful template message processing."""
        # Mock successful template response
        mock_template.return_value = {
            'success': True,
            'template': self.template,
            'template_name': 'vea_info_donativos',
            'response_id': 'msg_123',
            'response_text': 'Template message sent',
            'parameters': {'customer_name': 'John Doe'}
        }
        
        result = self.handler.process_message('+1234567890', 'I need donation information')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['response_type'], 'template')
        self.assertEqual(result['response_id'], 'msg_123')
        mock_template.assert_called_once()
        mock_fallback.assert_not_called()
    
    @patch.object(WhatsAppBotHandler, '_try_template_response')
    @patch.object(WhatsAppBotHandler, '_try_openai_fallback')
    def test_process_message_fallback_success(self, mock_fallback, mock_template):
        """Test successful fallback message processing."""
        # Mock failed template response
        mock_template.return_value = {'success': False, 'error': 'No template available'}
        
        # Mock successful fallback response
        mock_fallback.return_value = {
            'success': True,
            'response_id': 'msg_456',
            'response_text': 'Fallback response'
        }
        
        result = self.handler.process_message('+1234567890', 'Random message')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['response_type'], 'fallback')
        self.assertEqual(result['response_id'], 'msg_456')
        mock_template.assert_called_once()
        mock_fallback.assert_called_once()
    
    def test_process_message_error(self):
        """Test error handling in message processing."""
        # process_message espera un str, no None
        result = self.handler.process_message('+1234567890', '')
        if result is None:
            self.fail("process_message devolvió None")
            return
        self.assertFalse(result['success'])
        self.assertEqual(result['response_type'], 'error')
        self.assertIn('error_message', result)


class WhatsAppBotViewsTest(APITestCase):
    """Test cases for WhatsApp bot views."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_user(username="testuser", password="testpass")
        
        # Create test template
        self.template = WhatsAppTemplate.objects.create(
            template_name='vea_info_donativos',
            template_id='donations_template_001',
            language='es',
            category='donations',
            parameters=['customer_name', 'bank_name'],
            is_active=True
        )
    
    def test_webhook_handler_success(self):
        """Test successful webhook handling."""
        from apps.whatsapp_bot.views import webhook_handler
        
        webhook_data = {
            'from': 'whatsapp:+1234567890',
            'to': 'whatsapp:+0987654321',
            'message': {
                'text': 'I need donation information'
            },
            'timestamp': '2024-01-01T12:00:00Z'
        }
        
        request = self.factory.post(
            '/webhook/',
            data=json.dumps(webhook_data),
            content_type='application/json'
        )
        
        with patch.object(WhatsAppBotHandler, 'process_message') as mock_process:
            mock_process.return_value = {
                'success': True,
                'response_type': 'template',
                'processing_time_ms': 150.5
            }
            
            response = webhook_handler(request)
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(data['success'])
            self.assertTrue(data['message_processed'])
    
    def test_webhook_handler_invalid_json(self):
        """Test webhook handling with invalid JSON."""
        from apps.whatsapp_bot.views import webhook_handler
        
        request = self.factory.post(
            '/webhook/',
            data='invalid json',
            content_type='application/json'
        )
        
        response = webhook_handler(request)
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Invalid JSON', data['error'])
    
    def test_health_check(self):
        """Test health check endpoint."""
        from apps.whatsapp_bot.views import health_check
        
        request = self.factory.get('/health/')
        response = health_check(request)
        
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(data['service'], 'whatsapp_bot')
        self.assertIn('status', data)
    
    def test_send_message_authenticated(self):
        """Test authenticated send message endpoint."""
        self.client.force_authenticate(user=self.user)
        
        message_data = {
            'phone_number': '+1234567890',
            'message': 'I need donation information',
            'context': {'user_id': '123'}
        }
        
        with patch.object(WhatsAppBotHandler, 'process_message') as mock_process:
            mock_process.return_value = {
                'success': True,
                'response_type': 'template',
                'response_id': 'msg_123',
                'processing_time_ms': 150.5,
                'intent_detected': 'donations'
            }
            
            response = self.client.post('/api/v1/whatsapp/send/', message_data)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            data = response.data
            self.assertTrue(data['success'])
            self.assertEqual(data['response_type'], 'template')
    
    def test_send_message_unauthenticated(self):
        """Test unauthenticated send message endpoint."""
        message_data = {
            'phone_number': '+1234567890',
            'message': 'I need donation information'
        }
        
        response = self.client.post('/api/v1/whatsapp/send/', message_data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_templates_authenticated(self):
        """Test authenticated get templates endpoint."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/v1/whatsapp/templates/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertTrue(data['success'])
        self.assertEqual(data['total_count'], 1)
        self.assertEqual(data['templates'][0]['template_name'], 'vea_info_donativos')
    
    def test_get_bot_statistics_authenticated(self):
        """Test authenticated get statistics endpoint."""
        self.client.force_authenticate(user=self.user)
        
        with patch.object(WhatsAppBotHandler, 'get_statistics') as mock_stats:
            mock_stats.return_value = {
                'total_interactions': 100,
                'successful_interactions': 95,
                'success_rate': 95.0,
                'template_usage': 80,
                'fallback_usage': 20
            }
            
            response = self.client.get('/api/v1/whatsapp/statistics/')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            data = response.data
            self.assertTrue(data['success'])
            self.assertEqual(data['statistics']['total_interactions'], 100)


class LoggingServiceTest(TestCase):
    """Test cases for logging service."""
    
    def setUp(self):
        """Set up test data."""
        self.logging_service = LoggingService()
        self.template = WhatsAppTemplate.objects.create(
            template_name='vea_info_donativos',
            template_id='donations_template_001',
            language='es',
            category='donations',
            parameters=['customer_name'],
            is_active=True
        )
    
    def test_log_interaction(self):
        """Test logging interaction."""
        interaction = self.logging_service.log_interaction(
            phone_number='+1234567890',
            message_text='I need donation information',
            intent_detected='donations',
            template_used=self.template,
            response_text='Template message sent',
            response_id='msg_123',
            parameters_used={'customer_name': 'John Doe'},
            fallback_used=False,
            processing_time_ms=150.5,
            success=True,
            context_data={'user_id': '123'}
        )
        
        self.assertIsInstance(interaction, WhatsAppInteraction)
        self.assertEqual(interaction.phone_number, '+1234567890')
        self.assertEqual(interaction.intent_detected, 'donations')
        self.assertTrue(interaction.success)
        self.assertFalse(interaction.fallback_used)
    
    @patch('apps.whatsapp_bot.services.cache.set')
    @patch('apps.whatsapp_bot.services.cache.get')
    def test_save_and_get_context(self, mock_cache_get, mock_cache_set):
        """Test saving and getting context from Redis."""
        context_data = {'user_id': '123', 'session_id': 'abc123'}
        
        # Test saving context
        result = self.logging_service.save_context_to_redis('+1234567890', context_data)
        self.assertTrue(result)
        mock_cache_set.assert_called_once()
        
        # Test getting context
        mock_cache_get.return_value = context_data
        retrieved_context = self.logging_service.get_context_from_redis('+1234567890')
        self.assertEqual(retrieved_context, context_data)
    
    @patch('apps.whatsapp_bot.services.cache.set')
    @patch('apps.whatsapp_bot.services.cache.get')
    def test_update_context(self, mock_cache_get, mock_cache_set):
        """Test updating context."""
        existing_context = {'user_id': '123', 'interaction_count': 5}
        new_data = {'last_intent': 'donations', 'template_used': 'vea_info_donativos'}
        
        mock_cache_get.return_value = existing_context
        
        result = self.logging_service.update_context('+1234567890', new_data)
        
        self.assertTrue(result)
        mock_cache_set.assert_called_once()
        
        # Verify the updated context
        call_args = mock_cache_set.call_args
        updated_context = call_args[0][1]  # Second argument is the context data
        self.assertEqual(updated_context['user_id'], '123')
        self.assertEqual(updated_context['last_intent'], 'donations')
        self.assertEqual(updated_context['template_used'], 'vea_info_donativos')
        self.assertEqual(updated_context['interaction_count'], 5)
        self.assertIn('last_updated', updated_context)


if __name__ == '__main__':
    unittest.main() 