"""
Django views for WhatsApp Bot API endpoints.

This module provides REST API endpoints for WhatsApp bot functionality,
including message processing, statistics, and webhook handling.
"""

import json
import logging
from typing import Dict, Any
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .handlers import WhatsAppBotHandler
from .models import WhatsAppInteraction, WhatsAppTemplate
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def webhook_handler(request):
    """
    Webhook handler for incoming WhatsApp messages from ACS.
    
    This endpoint receives webhook notifications from Azure Communication Services
    when users send messages to the WhatsApp bot.
    
    Expected payload:
    {
        "from": "whatsapp:+1234567890",
        "to": "whatsapp:+0987654321",
        "message": {
            "text": "Hello, I need information about donations"
        },
        "timestamp": "2024-01-01T12:00:00Z"
    }
    
    Returns:
        JSON response with processing status
    """
    try:
        # Parse request body
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Invalid content type. Expected application/json'
            }, status=400)
        
        logger.info(f"Webhook received: {json.dumps(data, indent=2)}")
        
        # Extract message data
        from_number = data.get('from', '').replace('whatsapp:', '')
        message_data = data.get('message', {})
        message_text = message_data.get('text', '')
        timestamp = data.get('timestamp', '')
        
        if not from_number or not message_text:
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields: from or message.text'
            }, status=400)
        
        # Process message with bot handler
        bot_handler = WhatsAppBotHandler()
        result = bot_handler.process_message(from_number, message_text)
        
        # Log webhook processing
        logger.info(f"Webhook processed for {from_number}: {result['success']}")
        
        return JsonResponse({
            'success': True,
            'message_processed': result['success'],
            'response_type': result.get('response_type', 'unknown'),
            'processing_time_ms': result.get('processing_time_ms', 0)
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in webhook: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON payload'
        }, status=400)
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request):
    """
    Send a message to a WhatsApp user via the bot.
    
    This endpoint allows authenticated users to send messages through the bot
    and get responses processed by the bot handler.
    
    Expected payload:
    {
        "phone_number": "+1234567890",
        "message": "Hello, I need information about donations",
        "context": {
            "user_id": "123",
            "session_id": "abc123"
        }
    }
    
    Returns:
        JSON response with bot processing result
    """
    try:
        phone_number = request.data.get('phone_number')
        message = request.data.get('message')
        context = request.data.get('context', {})
        
        if not phone_number or not message:
            return Response({
                'success': False,
                'error': 'Missing required fields: phone_number or message'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Process message with bot handler
        bot_handler = WhatsAppBotHandler()
        result = bot_handler.process_message(phone_number, message, context)
        
        logger.info(f"Message sent via API for {phone_number}: {result['success']}")
        
        return Response({
            'success': result['success'],
            'response_type': result.get('response_type', 'unknown'),
            'response_id': result.get('response_id', ''),
            'processing_time_ms': result.get('processing_time_ms', 0),
            'intent_detected': result.get('intent_detected', 'unknown'),
            'error_message': result.get('error_message', '')
        })
        
    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}")
        return Response({
            'success': False,
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_interaction_history(request):
    """
    Get interaction history for a specific phone number.
    
    Query parameters:
    - phone_number: User's phone number
    - limit: Maximum number of interactions to return (default: 10)
    
    Returns:
        JSON response with interaction history
    """
    try:
        phone_number = request.query_params.get('phone_number')
        limit = int(request.query_params.get('limit', 10))
        
        if not phone_number:
            return Response({
                'success': False,
                'error': 'Missing required parameter: phone_number'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get interaction history
        bot_handler = WhatsAppBotHandler()
        interactions = bot_handler.get_interaction_history(phone_number, limit)
        
        # Serialize interactions
        interaction_data = []
        for interaction in interactions:
            interaction_data.append({
                'id': str(interaction.id),
                'phone_number': interaction.phone_number,
                'message_text': interaction.message_text,
                'intent_detected': interaction.intent_detected,
                'template_used': interaction.template_used.template_name if interaction.template_used else None,
                'response_text': interaction.response_text,
                'response_id': interaction.response_id,
                'fallback_used': interaction.fallback_used,
                'processing_time_ms': interaction.processing_time_ms,
                'success': interaction.success,
                'error_message': interaction.error_message,
                'created_at': interaction.created_at.isoformat()
            })
        
        return Response({
            'success': True,
            'phone_number': phone_number,
            'interactions': interaction_data,
            'total_count': len(interaction_data)
        })
        
    except ValueError as e:
        return Response({
            'success': False,
            'error': 'Invalid limit parameter'
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error getting interaction history: {str(e)}")
        return Response({
            'success': False,
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_bot_statistics(request):
    """
    Get WhatsApp bot usage statistics.
    
    Returns:
        JSON response with bot statistics
    """
    try:
        bot_handler = WhatsAppBotHandler()
        stats = bot_handler.get_statistics()
        
        return Response({
            'success': True,
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting bot statistics: {str(e)}")
        return Response({
            'success': False,
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_templates(request):
    """
    Get list of available WhatsApp templates.
    
    Query parameters:
    - category: Filter by template category
    - active_only: Return only active templates (default: true)
    
    Returns:
        JSON response with template list
    """
    try:
        category = request.query_params.get('category')
        active_only = request.query_params.get('active_only', 'true').lower() == 'true'
        
        # Build query
        queryset = WhatsAppTemplate.objects.all()
        
        if category:
            queryset = queryset.filter(category=category)
        
        if active_only:
            queryset = queryset.filter(is_active=True)
        
        # Serialize templates
        templates = []
        for template in queryset:
            templates.append({
                'id': str(template.id),
                'template_name': template.template_name,
                'template_id': template.template_id,
                'language': template.language,
                'category': template.category,
                'parameters': template.parameters,
                'is_active': template.is_active,
                'created_at': template.created_at.isoformat(),
                'updated_at': template.updated_at.isoformat()
            })
        
        return Response({
            'success': True,
            'templates': templates,
            'total_count': len(templates)
        })
        
    except Exception as e:
        logger.error(f"Error getting templates: {str(e)}")
        return Response({
            'success': False,
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_template(request):
    """
    Test a WhatsApp template with provided parameters.
    
    This endpoint allows testing templates without sending actual messages.
    
    Expected payload:
    {
        "template_name": "vea_info_donativos",
        "parameters": {
            "customer_name": "Juan Pérez",
            "bank_name": "Banco Azteca",
            "beneficiary_name": "Juan Pérez",
            "account_number": "1234567890",
            "clabe_number": "012345678901234567",
            "contact_name": "Juan Pérez",
            "contact_phone": "+525512345678"
        },
        "phone_number": "+1234567890"
    }
    
    Returns:
        JSON response with template test result
    """
    try:
        template_name = request.data.get('template_name')
        parameters = request.data.get('parameters', {})
        phone_number = request.data.get('phone_number')
        
        if not template_name:
            return Response({
                'success': False,
                'error': 'Missing required field: template_name'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get template
        try:
            template = WhatsAppTemplate.objects.get(
                template_name=template_name,
                is_active=True
            )
        except WhatsAppTemplate.DoesNotExist:
            return Response({
                'success': False,
                'error': f'Template not found: {template_name}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Validate parameters
        missing_params = [
            param for param in template.parameters
            if param not in parameters or not parameters[param]
        ]
        
        if missing_params:
            return Response({
                'success': False,
                'error': f'Missing required parameters: {missing_params}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Test template (without sending actual message)
        test_result = {
            'template_name': template.template_name,
            'template_id': template.template_id,
            'language': template.language,
            'category': template.category,
            'parameters': parameters,
            'parameter_count': len(parameters),
            'required_parameters': template.parameters,
            'validation_passed': True
        }
        
        # If phone number provided, simulate sending
        if phone_number:
            try:
                from .services import ACSService
                acs_service = ACSService()
                
                # Note: This would actually send a message in production
                # For testing, we just validate the request
                test_result['message_simulation'] = {
                    'to_phone': phone_number,
                    'template_name': template_name,
                    'parameters': parameters,
                    'status': 'validated'
                }
                
            except Exception as e:
                test_result['message_simulation'] = {
                    'error': str(e),
                    'status': 'failed'
                }
        
        return Response({
            'success': True,
            'test_result': test_result
        })
        
    except Exception as e:
        logger.error(f"Error testing template: {str(e)}")
        return Response({
            'success': False,
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint for WhatsApp bot service.
    
    Returns:
        JSON response with service health status
    """
    try:
        # Check database connection
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Check cache connection (local memory cache, no Redis)
        from django.core.cache import cache
        try:
            cache.set('health_check', 'ok', 60)
            cache_ok = cache.get('health_check') == 'ok'
        except Exception:
            cache_ok = False
        
        # Check ACS configuration
        acs_configured = all([
            hasattr(settings, 'ACS_WHATSAPP_ENDPOINT'),
            hasattr(settings, 'ACS_WHATSAPP_API_KEY'),
            hasattr(settings, 'ACS_PHONE_NUMBER'),
            hasattr(settings, 'WHATSAPP_CHANNEL_ID_GUID')
        ])
        
        health_status = {
            'service': 'whatsapp_bot',
            'status': 'healthy',
            'database': 'connected',
            'cache': 'connected' if cache_ok else 'disconnected',
            'acs_configured': acs_configured,
            'timestamp': timezone.now().isoformat()
        }
        
        return Response(health_status)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return Response({
            'service': 'whatsapp_bot',
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE) 