# WhatsApp Event Grid Handler

A comprehensive Event Grid handler for processing WhatsApp events from Azure Communication Services (ACS) with clean business logic, framework-agnostic design, and production-ready Azure Function deployment.

## Features

- **Event Grid Integration**: Handles ACS WhatsApp events via Azure Event Grid
- **Framework Agnostic**: Clean business logic without web framework dependencies
- **Azure Function Ready**: Complete Azure Function implementation examples
- **Comprehensive Logging**: Structured logging for all events and interactions
- **Error Handling**: Robust error handling with Event Grid retry prevention
- **User Management**: Automatic user registration and interaction tracking
- **Template Processing**: Reuses existing template and OpenAI services
- **Delivery Reports**: Handles message delivery status tracking
- **Unit Testing**: Comprehensive test coverage with mocks

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Azure Event   │    │   Event Grid    │    │   Business      │
│   Grid          │───▶│   Handler       │───▶│   Logic         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │◀───│   Services      │───▶│   Redis Cache   │
│   (Users/Logs)  │    │   (User/Storage)│    │   (Context)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Supported Event Types

### 1. Microsoft.Communication.AdvancedMessageReceived
Handles incoming WhatsApp messages with:
- Message content extraction
- User registration/update
- Intent detection
- Template-based response generation
- OpenAI fallback processing
- Context management
- Interaction logging

### 2. Microsoft.Communication.AdvancedMessageDeliveryReportReceived
Handles message delivery reports with:
- Delivery status tracking
- Error details logging
- Message status updates
- Report storage

## Installation

### 1. Database Setup

Run the migrations to create required tables:

```bash
python manage.py makemigrations whatsapp_bot
python manage.py migrate
```

### 2. Environment Variables

Add the following environment variables:

```bash
# Event Grid Configuration
EVENT_GRID_VALIDATION_KEY=your-validation-key

# ACS Configuration (if not already set)
ACS_WHATSAPP_ENDPOINT=https://your-acs-resource.communication.azure.com
ACS_WHATSAPP_API_KEY=your-acs-access-key
ACS_PHONE_NUMBER=whatsapp:+1234567890
WHATSAPP_CHANNEL_ID_GUID=your-channel-registration-id

# Database and Redis (if not already set)
DATABASE_URL=postgresql://user:password@localhost:5432/vea_webapp
AZURE_REDIS_CONNECTIONSTRING=localhost
AZURE_REDIS_CONNECTIONSTRING=6379
AZURE_REDIS_CONNECTIONSTRING=
AZURE_REDIS_CONNECTIONSTRING=0

# OpenAI (for fallback responses)
OPENAI_API_KEY=your-openai-api-key
```

## Usage

### 1. Event Grid Handler

```python
from apps.whatsapp_bot.event_grid_handler import EventGridHandler
from apps.whatsapp_bot.user_service import UserService
from apps.whatsapp_bot.storage_service import StorageService
from apps.whatsapp_bot.handlers import WhatsAppBotHandler

# Initialize services
user_service = UserService()
storage_service = StorageService()
bot_handler = WhatsAppBotHandler()

# Create Event Grid handler
handler = EventGridHandler(
    user_service=user_service,
    template_service=bot_handler.template_service,
    logging_service=bot_handler.logging_service,
    storage_service=storage_service,
    validation_key='your-validation-key'
)

# Handle Event Grid request
status_code, response = handler.handle_event_grid_request(request_body, headers)
```

### 2. Single Event Processing

```python
# Process a single event
event_data = {
    'id': 'event-id',
    'eventType': 'Microsoft.Communication.AdvancedMessageReceived',
    'eventTime': '2024-01-01T12:00:00Z',
    'data': {
        'from': {'phoneNumber': 'whatsapp:+1234567890'},
        'to': {'phoneNumber': 'whatsapp:+0987654321'},
        'message': {'text': 'I need donation information'},
        'receivedTimestamp': '2024-01-01T12:00:00Z'
    }
}

result = handler.handle_single_event(event_data)
```

## Azure Function Implementation

### 1. Event Grid Trigger Function

```python
import azure.functions as func
from apps.whatsapp_bot.azure_function_example import create_handler

def event_grid_trigger(event: func.EventGridEvent) -> None:
    """Azure Function with Event Grid Trigger."""
    try:
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
```

### 2. HTTP Trigger Function

```python
def http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    """Azure Function with HTTP Trigger for Event Grid events."""
    try:
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
        return func.HttpResponse(
            body=json.dumps({'error': 'Internal processing error'}),
            status_code=200,
            mimetype="application/json"
        )
```

### 3. Function Configuration

#### function.json for Event Grid Trigger

```json
{
    "scriptFile": "azure_function_example.py",
    "bindings": [
        {
            "type": "eventGridTrigger",
            "name": "event",
            "direction": "in"
        }
    ]
}
```

#### function.json for HTTP Trigger

```json
{
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
```

#### host.json

```json
{
    "version": "2.0",
    "logging": {
        "applicationInsights": {
            "samplingSettings": {
                "isEnabled": true,
                "excludedTypes": "Request"
            }
        }
    },
    "extensionBundle": {
        "id": "Microsoft.Azure.Functions.ExtensionBundle",
        "version": "[3.*, 4.0.0)"
    }
}
```

## Event Processing Flow

### 1. Message Received Event

```
Event Grid Event → Validation → Message Extraction → User Registration → 
Intent Detection → Template Response → OpenAI Fallback → Context Save → 
Interaction Logging → Success Response
```

### 2. Delivery Report Event

```
Event Grid Event → Validation → Report Extraction → Report Storage → 
Status Update → Success Response
```

## Event Payload Examples

### Message Received Event

```json
{
    "id": "event-id",
    "eventType": "Microsoft.Communication.AdvancedMessageReceived",
    "eventTime": "2024-01-01T12:00:00Z",
    "data": {
        "from": {
            "phoneNumber": "whatsapp:+1234567890"
        },
        "to": {
            "phoneNumber": "whatsapp:+0987654321"
        },
        "message": {
            "text": "I need donation information"
        },
        "receivedTimestamp": "2024-01-01T12:00:00Z",
        "id": "message-id",
        "channelRegistrationId": "channel-id"
    }
}
```

### Delivery Report Event

```json
{
    "id": "event-id",
    "eventType": "Microsoft.Communication.AdvancedMessageDeliveryReportReceived",
    "eventTime": "2024-01-01T12:00:00Z",
    "data": {
        "messageId": "message-id",
        "status": "Delivered",
        "receivedTimestamp": "2024-01-01T12:00:00Z",
        "to": {
            "phoneNumber": "whatsapp:+1234567890"
        },
        "channelRegistrationId": "channel-id"
    }
}
```

## Database Schema

### WhatsAppUser Table
- `id`: UUID primary key
- `phone_number`: User's phone number (unique)
- `first_name`, `last_name`: User names
- `email`: User email
- `is_active`: User status
- `last_interaction`: Last interaction timestamp
- `interaction_count`: Total interactions
- `preferred_language`: User language preference

### WhatsAppDeliveryReport Table
- `id`: UUID primary key
- `message_id`: ACS message ID (unique)
- `status`: Delivery status
- `timestamp`: Event timestamp
- `recipient_number`: Recipient phone number
- `channel_registration_id`: ACS channel ID
- `error_details`: JSON error details

### WhatsAppInteractionLog Table
- `id`: UUID primary key
- `phone_number`: User phone number
- `message_text`: Incoming message
- `intent_detected`: Detected intent
- `template_used`: Template name
- `response_text`: Response sent
- `response_id`: ACS response ID
- `parameters_used`: JSON parameters
- `fallback_used`: OpenAI fallback flag
- `processing_time_ms`: Processing time
- `success`: Success status
- `error_message`: Error details
- `context_data`: JSON context data

### WhatsAppEventGridLog Table
- `id`: UUID primary key
- `event_id`: Event Grid event ID
- `event_type`: Event type
- `event_time`: Event timestamp
- `data`: Complete event data (JSON)

## Testing

### 1. Unit Tests

Run the comprehensive test suite:

```bash
python manage.py test apps.whatsapp_bot.tests_event_grid
```

### 2. Test Coverage

- Event Grid validation
- Message processing
- Delivery report processing
- Error handling
- Service integration
- Azure Function integration

### 3. Test Event Examples

```python
# Test message received event
test_event = {
    'id': 'test-event-id',
    'eventType': 'Microsoft.Communication.AdvancedMessageReceived',
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

# Test delivery report event
test_report = {
    'id': 'test-event-id',
    'eventType': 'Microsoft.Communication.AdvancedMessageDeliveryReportReceived',
    'eventTime': '2024-01-01T12:00:00Z',
    'data': {
        'messageId': 'test-message-id',
        'status': 'Delivered',
        'receivedTimestamp': '2024-01-01T12:00:00Z',
        'to': {'phoneNumber': 'whatsapp:+1234567890'},
        'channelRegistrationId': 'test-channel-id'
    }
}
```

## Deployment

### 1. Azure Function Deployment

```bash
# Deploy to Azure Functions
func azure functionapp publish your-function-app-name
```

### 2. Environment Configuration

Configure the following in Azure Function App Settings:

```bash
ACS_WHATSAPP_ENDPOINT=https://your-acs-resource.communication.azure.com
ACS_WHATSAPP_API_KEY=your-acs-access-key
ACS_PHONE_NUMBER=whatsapp:+1234567890
WHATSAPP_CHANNEL_ID_GUID=your-channel-registration-id
DATABASE_URL=postgresql://user:password@host:5432/database
AZURE_REDIS_CONNECTIONSTRING=your-redis-host
AZURE_REDIS_CONNECTIONSTRING=6379
AZURE_REDIS_CONNECTIONSTRING=your-redis-password
AZURE_REDIS_CONNECTIONSTRING=0
OPENAI_API_KEY=your-openai-api-key
EVENT_GRID_VALIDATION_KEY=your-validation-key
```

### 3. Event Grid Subscription

Create Event Grid subscription in Azure:

```bash
# Create Event Grid subscription
az eventgrid event-subscription create \
    --source-resource-id /subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/Microsoft.Communication/communicationServices/{acs-resource} \
    --name whatsapp-events \
    --endpoint-type azurefunction \
    --endpoint /subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/Microsoft.Web/sites/{function-app}/functions/event_grid_trigger \
    --included-event-types Microsoft.Communication.AdvancedMessageReceived Microsoft.Communication.AdvancedMessageDeliveryReportReceived
```

## Monitoring and Logging

### 1. Application Insights

The handler includes comprehensive logging for:
- Event processing status
- Service interactions
- Error details
- Performance metrics
- User interactions

### 2. Health Checks

```python
# Health check endpoint
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    handler = create_handler()
    health_status = handler.processor.storage_service.get_storage_health_status()
    return func.HttpResponse(
        body=json.dumps(health_status),
        status_code=200 if health_status['status'] == 'healthy' else 503
    )
```

### 3. Metrics

Track the following metrics:
- Events processed per minute
- Success/failure rates
- Processing times
- User interaction counts
- Delivery success rates

## Error Handling

### 1. Event Grid Retry Prevention

The handler always returns HTTP 200 to prevent Event Grid retries:
- Successful processing: 200 OK
- Failed processing: 200 OK with error details
- Validation errors: 200 OK with validation response

### 2. Service Failures

Graceful handling of:
- Database connection failures
- Redis connection failures
- ACS service failures
- OpenAI API failures

### 3. Malformed Events

Robust handling of:
- Missing required fields
- Invalid event types
- Malformed JSON payloads
- Timestamp parsing errors

## Security Considerations

### 1. Event Grid Validation

- Implement proper signature validation for production
- Use validation keys for webhook setup
- Validate event source and type

### 2. Data Protection

- Encrypt sensitive data in transit and at rest
- Implement proper access controls
- Log security events

### 3. Input Validation

- Validate all incoming event data
- Sanitize user inputs
- Prevent injection attacks

## Performance Optimization

### 1. Caching

- User data caching with TTL
- Template caching
- Context data caching

### 2. Database Optimization

- Proper indexing on frequently queried fields
- Connection pooling
- Query optimization

### 3. Async Processing

- Non-blocking event processing
- Background task handling
- Efficient resource utilization

## Troubleshooting

### Common Issues

1. **Event Grid Validation Failed**
   - Check validation key configuration
   - Verify webhook endpoint URL
   - Check Event Grid subscription settings

2. **Database Connection Errors**
   - Verify connection string
   - Check network connectivity
   - Ensure database is accessible

3. **Redis Connection Errors**
   - Verify Redis host and port
   - Check authentication credentials
   - Ensure Redis is running

4. **ACS Integration Errors**
   - Verify ACS endpoint and access key
   - Check phone number format
   - Ensure channel registration is active

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('apps.whatsapp_bot').setLevel(logging.DEBUG)
```

## Contributing

1. Follow the existing code style
2. Add comprehensive tests for new features
3. Update documentation
4. Ensure all tests pass
5. Add proper error handling

## License

This project is licensed under the MIT License - see the LICENSE file for details. 