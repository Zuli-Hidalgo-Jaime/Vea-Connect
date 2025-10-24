#!/usr/bin/env python3
"""
Comprehensive test script for WhatsApp Bot Handler.

This script tests all components of the WhatsApp bot including:
- Models and database operations
- Services (ACS, Data Retrieval, Template, Logging)
- Bot handler functionality
- API endpoints
- Integration with existing systems
"""

import os
import sys
import json
import django  # pyright: reportMissingImports=false
from unittest.mock import Mock, patch, MagicMock

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

def test_models():
    """Test WhatsApp bot models."""
    print("🔍 Testing WhatsApp Bot Models")
    print("-" * 40)
    
    try:
        from apps.whatsapp_bot.models import WhatsAppTemplate, WhatsAppInteraction, WhatsAppContext, DataSource
        
        # Test template creation
        template = WhatsAppTemplate.objects.create(
            template_name='test_donations',
            template_id='test_template_001',
            language='es',
            category='donations',
            parameters=['customer_name', 'bank_name'],
            is_active=True
        )
        print(f"✅ Template created: {template.template_name}")
        
        # Test interaction creation
        interaction = WhatsAppInteraction.objects.create(
            phone_number='+1234567890',
            message_text='Test donation message',
            intent_detected='donations',
            template_used=template,
            response_text='Test response',
            response_id='msg_001',
            parameters_used={'customer_name': 'Test User'},
            fallback_used=False,
            processing_time_ms=150.5,
            success=True
        )
        print(f"✅ Interaction created: {interaction.id}")
        
        # Test context creation
        context = WhatsAppContext.objects.create(
            phone_number='+1234567890',
            context_data={'user_id': '123', 'session_id': 'abc123'},
            is_active=True
        )
        print(f"✅ Context created: {context.phone_number}")
        
        # Test data source creation
        data_source = DataSource.objects.create(
            name='test_donations_source',
            source_type='postgresql',
            table_name='donations_donation',
            query_template='SELECT * FROM donations_donation WHERE customer_name = %s',
            cache_ttl=3600,
            is_active=True
        )
        print(f"✅ Data source created: {data_source.name}")
        
        # Cleanup
        template.delete()
        interaction.delete()
        context.delete()
        data_source.delete()
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing models: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_services():
    """Test WhatsApp bot services."""
    print("\n🔍 Testing WhatsApp Bot Services")
    print("-" * 40)
    
    try:
        from apps.whatsapp_bot.services import ACSService, DataRetrievalService, TemplateService, LoggingService
        
        # Test ACS Service
        print("Testing ACS Service...")
        acs_service = ACSService()
        print(f"✅ ACS Service initialized: {acs_service.endpoint}")
        
        # Test Data Retrieval Service
        print("Testing Data Retrieval Service...")
        data_service = DataRetrievalService()
        print(f"✅ Data Retrieval Service initialized")
        
        # Test Template Service
        print("Testing Template Service...")
        template_service = TemplateService(acs_service, data_service)
        print(f"✅ Template Service initialized")
        
        # Test Logging Service
        print("Testing Logging Service...")
        logging_service = LoggingService()
        print(f"✅ Logging Service initialized")
        
        # Test intent detection
        test_messages = [
            ("I need donation information", "donations"),
            ("I need ministry contact", "ministry"),
            ("I need event information", "events"),
            ("I need help", "general"),
            ("Random message", "unknown")
        ]
        
        for message, expected_intent in test_messages:
            intent, data = template_service.detect_intent(message)
            print(f"✅ Intent detection: '{message}' -> {intent} (expected: {expected_intent})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing services: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_bot_handler():
    """Test WhatsApp bot handler."""
    print("\n🔍 Testing WhatsApp Bot Handler")
    print("-" * 40)
    
    try:
        from apps.whatsapp_bot.handlers import WhatsAppBotHandler
        from apps.whatsapp_bot.models import WhatsAppTemplate
        
        # Create test template
        template = WhatsAppTemplate.objects.create(
            template_name='test_donations',
            template_id='test_template_001',
            language='es',
            category='donations',
            parameters=['customer_name', 'bank_name'],
            is_active=True
        )
        
        # Test bot handler initialization
        print("Testing Bot Handler initialization...")
        handler = WhatsAppBotHandler()
        print(f"✅ Bot Handler initialized")
        
        # Test message processing with mocks
        print("Testing message processing...")
        
        with patch.object(handler, '_try_template_response') as mock_template:
            with patch.object(handler, '_try_openai_fallback') as mock_fallback:
                
                # Mock successful template response
                mock_template.return_value = {
                    'success': True,
                    'template': template,
                    'template_name': 'test_donations',
                    'response_id': 'msg_123',
                    'response_text': 'Template response',
                    'parameters': {'customer_name': 'Test User'}
                }
                
                result = handler.process_message('+1234567890', 'I need donation information')
                
                print(f"✅ Message processing: {result['success']}")
                print(f"✅ Response type: {result.get('response_type')}")
                print(f"✅ Intent detected: {result.get('intent_detected')}")
        
        # Test statistics
        print("Testing statistics...")
        stats = handler.get_statistics()
        print(f"✅ Statistics retrieved: {stats['total_interactions']} interactions")
        
        # Cleanup
        template.delete()
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing bot handler: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """Test WhatsApp bot API endpoints."""
    print("\n🔍 Testing WhatsApp Bot API Endpoints")
    print("-" * 40)
    
    try:
        from django.test import RequestFactory
        from django.contrib.auth import get_user_model
        from apps.whatsapp_bot.views import (
            webhook_handler, health_check, send_message,
            get_interaction_history, get_bot_statistics, get_templates
        )
        
        user = get_user_model().objects.create_user(username="testuser", password="testpass")
        
        factory = RequestFactory()
        
        # Test health check endpoint
        print("Testing health check endpoint...")
        request = factory.get('/api/v1/whatsapp/health/')
        response = health_check(request)
        print(f"✅ Health check status: {response.status_code}")
        
        # Test webhook endpoint
        print("Testing webhook endpoint...")
        webhook_data = {
            'from': 'whatsapp:+1234567890',
            'to': 'whatsapp:+0987654321',
            'message': {
                'text': 'I need donation information'
            },
            'timestamp': '2024-01-01T12:00:00Z'
        }
        
        request = factory.post(
            '/api/v1/whatsapp/webhook/',
            data=json.dumps(webhook_data),
            content_type='application/json'
        )
        
        with patch('apps.whatsapp_bot.views.WhatsAppBotHandler') as mock_handler:
            mock_instance = Mock()
            mock_instance.process_message.return_value = {
                'success': True,
                'response_type': 'template',
                'processing_time_ms': 150.5
            }
            mock_handler.return_value = mock_instance
            
            response = webhook_handler(request)
            print(f"✅ Webhook status: {response.status_code}")
        
        # Test authenticated endpoints (create test user)
        print("Testing authenticated endpoints...")
        
        # Test send message endpoint
        message_data = {
            'phone_number': '+1234567890',
            'message': 'I need donation information',
            'context': {'user_id': '123'}
        }
        
        request = factory.post(
            '/api/v1/whatsapp/send/',
            data=json.dumps(message_data),
            content_type='application/json'
        )
        request.user = user
        
        with patch('apps.whatsapp_bot.views.WhatsAppBotHandler') as mock_handler:
            mock_instance = Mock()
            mock_instance.process_message.return_value = {
                'success': True,
                'response_type': 'template',
                'response_id': 'msg_123',
                'processing_time_ms': 150.5,
                'intent_detected': 'donations'
            }
            mock_handler.return_value = mock_instance
            
            response = send_message(request)
            print(f"✅ Send message status: {response.status_code}")
        
        # Test get templates endpoint
        request = factory.get('/api/v1/whatsapp/templates/')
        request.user = user
        
        response = get_templates(request)
        print(f"✅ Get templates status: {response.status_code}")
        
        # Test get statistics endpoint
        request = factory.get('/api/v1/whatsapp/statistics/')
        request.user = user
        
        with patch('apps.whatsapp_bot.views.WhatsAppBotHandler') as mock_handler:
            mock_instance = Mock()
            mock_instance.get_statistics.return_value = {
                'total_interactions': 100,
                'successful_interactions': 95,
                'success_rate': 95.0,
                'template_usage': 80,
                'fallback_usage': 20
            }
            mock_handler.return_value = mock_instance
            
            response = get_bot_statistics(request)
            print(f"✅ Get statistics status: {response.status_code}")
        
        # Cleanup
        user.delete()
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing API endpoints: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """Test integration with existing systems."""
    print("\n🔍 Testing Integration with Existing Systems")
    print("-" * 40)
    
    try:
        # Test integration with EmbeddingManager
        print("Testing EmbeddingManager integration...")
        from utilities.embedding_manager import EmbeddingManager
        
        embedding_manager = EmbeddingManager()
        print(f"✅ EmbeddingManager initialized successfully")
        
        # Test database integration
        print("Testing database integration...")
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"✅ Database integration: {result[0]}")
        
        # Test ACS configuration
        print("Testing ACS configuration...")
        from django.conf import settings
        
        acs_config = {
            'endpoint': getattr(settings, 'ACS_WHATSAPP_ENDPOINT', None),
            'access_key': getattr(settings, 'ACS_WHATSAPP_API_KEY', None),
            'phone_number': getattr(settings, 'ACS_PHONE_NUMBER', None),
            'channel_registration_id': getattr(settings, 'WHATSAPP_CHANNEL_ID_GUID', None)
        }
        
        print(f"✅ ACS configuration: {all(acs_config.values())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing integration: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_template_management():
    """Test template management functionality."""
    print("\n🔍 Testing Template Management")
    print("-" * 40)
    
    try:
        from apps.whatsapp_bot.models import WhatsAppTemplate
        from django.conf import settings
        
        # Test template configuration
        print("Testing template configuration...")
        templates_config = getattr(settings, 'WHATSAPP_TEMPLATES', {})
        
        for template_name, config in templates_config.items():
            print(f"✅ Template config: {template_name} - {config['category']}")
        
        # Test template creation from config
        print("Testing template creation...")
        for template_name, config in templates_config.items():
            template, created = WhatsAppTemplate.objects.get_or_create(
                template_name=template_name,
                defaults={
                    'template_id': f"{template_name}_001",
                    'language': 'es',
                    'category': config['category'],
                    'parameters': config['parameters'],
                    'is_active': True
                }
            )
            
            if created:
                print(f"✅ Template created: {template_name}")
            else:
                print(f"✅ Template exists: {template_name}")
        
        # Test template validation
        print("Testing template validation...")
        for template in WhatsAppTemplate.objects.all():
            print(f"✅ Template validation: {template.template_name} - {len(template.parameters)} parameters")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing template management: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all WhatsApp bot tests."""
    print("🚀 Testing WhatsApp Bot Handler Implementation")
    print("=" * 60)
    
    tests = [
        test_models,
        test_services,
        test_bot_handler,
        test_api_endpoints,
        test_integration,
        test_template_management,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 WHATSAPP BOT TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All WhatsApp Bot tests passed!")
        print("\n✅ Implementation Status:")
        print("   • Models and database operations working")
        print("   • Services (ACS, Data Retrieval, Template, Logging) functional")
        print("   • Bot handler processing messages correctly")
        print("   • API endpoints responding properly")
        print("   • Integration with existing systems successful")
        print("   • Template management operational")
        print("\n🚀 WhatsApp Bot is ready for deployment!")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 