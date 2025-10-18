"""
Azure Function Example for WhatsApp Event Grid Handler.

This module provides an example implementation of the WhatsApp Event Grid
handler as an Azure Function with both Event Grid Trigger and HTTP Trigger.
"""

import azure.functions as func
import logging
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime

# Import our custom modules
from .event_grid_handler import EventGridHandler
from .user_service import UserService
from .storage_service import StorageService
from .services import TemplateService, LoggingService
from .handlers import WhatsAppBotHandler

logger = logging.getLogger(__name__)


def create_handler() -> EventGridHandler:
    """
    Create and configure the Event Grid handler.
    
    Returns:
        Configured EventGridHandler instance
    """
    # Initialize services
    user_service = UserService()
    storage_service = StorageService()
    
    # Initialize bot handler (which contains template and logging services)
    bot_handler = WhatsAppBotHandler()
    
    # Create Event Grid handler
    handler = EventGridHandler(
        user_service=user_service,
        template_service=bot_handler.template_service,
        logging_service=bot_handler.logging_service,
        storage_service=storage_service,
        validation_key=os.getenv('EVENT_GRID_VALIDATION_KEY')
    )
    
    return handler


# Azure Function with Event Grid Trigger
def event_grid_trigger(event: func.EventGridEvent) -> None:
    """
    Azure Function with Event Grid Trigger.
    
    This function is triggered by Event Grid events from ACS WhatsApp.
    
    Args:
        event: Event Grid event object
    """
    try:
        logger.info(f"Event Grid trigger received: {event.event_type}")
        
        # Create handler
        handler = create_handler()
        
        # Convert event to dictionary
        event_data = {
            'id': event.id,
            'eventType': event.event_type,
            'eventTime': event.event_time.isoformat(),
            'data': event.get_json()
        }
        
        # Process the event
        result = handler.handle_single_event(event_data)
        
        if result.get('success'):
            logger.info(f"Event processed successfully: {event.event_type}")
        else:
            logger.error(f"Event processing failed: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error in Event Grid trigger: {e}")
        # Don't raise exception to prevent Event Grid retries


# Azure Function with HTTP Trigger (alternative implementation)
def http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function with HTTP Trigger for Event Grid events.
    
    This function can handle Event Grid events via HTTP POST requests.
    
    Args:
        req: HTTP request object
        
    Returns:
        HTTP response
    """
    try:
        logger.info("HTTP trigger received")
        
        # Get request body and headers
        request_body = req.get_body().decode('utf-8')
        headers = dict(req.headers)
        
        # Create handler
        handler = create_handler()
        
        # Process Event Grid request
        status_code, response_body = handler.handle_event_grid_request(request_body, headers)
        
        # Return HTTP response
        return func.HttpResponse(
            body=json.dumps(response_body),
            status_code=status_code,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error in HTTP trigger: {e}")
        # Return 200 to prevent Event Grid retries
        return func.HttpResponse(
            body=json.dumps({'error': 'Internal processing error'}),
            status_code=200,
            mimetype="application/json"
        )


# Azure Function with Event Grid Trigger (alternative implementation)
def event_grid_trigger_alternative(events: func.EventGridEvent) -> None:
    """
    Alternative Azure Function with Event Grid Trigger.
    
    This function handles multiple events in a single trigger.
    
    Args:
        events: List of Event Grid events
    """
    try:
        logger.info(f"Event Grid trigger received {len(events)} events")
        
        # Create handler
        handler = create_handler()
        
        # Process each event
        for event in events:
            try:
                # Convert event to dictionary
                event_data = {
                    'id': event.id,
                    'eventType': event.event_type,
                    'eventTime': event.event_time.isoformat(),
                    'data': event.get_json()
                }
                
                # Process the event
                result = handler.handle_single_event(event_data)
                
                if result.get('success'):
                    logger.info(f"Event {event.id} processed successfully")
                else:
                    logger.error(f"Event {event.id} processing failed: {result.get('error')}")
                    
            except Exception as e:
                logger.error(f"Error processing event {event.id}: {e}")
                # Continue processing other events
                
    except Exception as e:
        logger.error(f"Error in Event Grid trigger: {e}")


# Health check function
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """
    Health check function for the Azure Function.
    
    Args:
        req: HTTP request object
        
    Returns:
        HTTP response with health status
    """
    try:
        # Create handler to test services
        handler = create_handler()
        
        # Get storage health status
        storage_service = handler.processor.storage_service
        health_status = storage_service.get_storage_health_status()
        
        # Add function-specific health info
        health_status.update({
            'function_name': 'whatsapp_event_grid_handler',
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'healthy' if health_status['database_healthy'] and health_status['cache_healthy'] else 'unhealthy'
        })
        
        status_code = 200 if health_status['status'] == 'healthy' else 503
        
        return func.HttpResponse(
            body=json.dumps(health_status),
            status_code=status_code,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return func.HttpResponse(
            body=json.dumps({
                'function_name': 'whatsapp_event_grid_handler',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }),
            status_code=503,
            mimetype="application/json"
        )


# Test function for development
def test_function(req: func.HttpRequest) -> func.HttpResponse:
    """
    Test function for development and debugging.
    
    Args:
        req: HTTP request object
        
    Returns:
        HTTP response with test results
    """
    try:
        # Create handler
        handler = create_handler()
        
        # Test event data
        test_event = {
            'id': 'test-event-id',
            'eventType': 'Microsoft.Communication.AdvancedMessageReceived',
            'eventTime': datetime.utcnow().isoformat(),
            'data': {
                'from': {'phoneNumber': 'whatsapp:+1234567890'},
                'to': {'phoneNumber': 'whatsapp:+0987654321'},
                'message': {'text': 'Test message'},
                'receivedTimestamp': datetime.utcnow().isoformat(),
                'id': 'test-message-id',
                'channelRegistrationId': 'test-channel-id'
            }
        }
        
        # Process test event
        result = handler.handle_single_event(test_event)
        
        return func.HttpResponse(
            body=json.dumps({
                'test_event': test_event,
                'result': result,
                'timestamp': datetime.utcnow().isoformat()
            }),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Test function failed: {e}")
        return func.HttpResponse(
            body=json.dumps({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }),
            status_code=500,
            mimetype="application/json"
        )


# Example function.json configuration for Event Grid Trigger
FUNCTION_JSON_EVENT_GRID = {
    "scriptFile": "azure_function_example.py",
    "bindings": [
        {
            "type": "eventGridTrigger",
            "name": "event",
            "direction": "in"
        }
    ]
}

# Example function.json configuration for HTTP Trigger
FUNCTION_JSON_HTTP = {
    "scriptFile": "azure_function_example.py",
    "bindings": [
        {
            "authLevel": "anonymous",
            "type": "httpTrigger",
            "direction": "in",
            "name": "req",
            "methods": ["POST"],
            "route": "whatsapp/webhook"
        },
        {
            "type": "http",
            "direction": "out",
            "name": "$return"
        }
    ]
}

# Example host.json configuration
HOST_JSON = {
    "version": "2.0",
    "logging": {
        "applicationInsights": {
            "samplingSettings": {
                "isEnabled": True,
                "excludedTypes": "Request"
            }
        }
    },
    "extensionBundle": {
        "id": "Microsoft.Azure.Functions.ExtensionBundle",
        "version": "[3.*, 4.0.0)"
    }
}

# Example local.settings.json configuration
LOCAL_SETTINGS_JSON = {
    "IsEncrypted": False,
    "Values": {
        "AzureWebJobsStorage": "UseDevelopmentStorage=true",
        "FUNCTIONS_WORKER_RUNTIME": "python",
        "ACS_WHATSAPP_ENDPOINT": "https://your-acs-resource.communication.azure.com",
        "ACS_WHATSAPP_API_KEY": "your-acs-access-key",
        "ACS_PHONE_NUMBER": "whatsapp:+1234567890",
        "WHATSAPP_CHANNEL_ID_GUID": "your-channel-registration-id",
        "DATABASE_URL": "postgresql://user:password@localhost:5432/vea_webapp",

        "OPENAI_API_KEY": "your-openai-api-key",
        "EVENT_GRID_VALIDATION_KEY": "your-validation-key"
    }
} 