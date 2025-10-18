# WhatsApp Bot Handler for ACS

A comprehensive WhatsApp bot implementation for Azure Communication Services (ACS) with template-based messaging, PostgreSQL data integration, Redis caching, and OpenAI fallback responses.

## Features

- **Template-Based Priority Responses**: Uses registered WhatsApp templates with dynamic data injection
- **PostgreSQL Integration**: Retrieves dynamic information from database
- **Redis Caching**: Caches frequently accessed data and conversation context
- **OpenAI RAG Fallback**: Intelligent fallback responses using OpenAI with RAG
- **Structured Logging**: Comprehensive logging of all interactions
- **Admin Interface**: Django admin for managing templates and viewing interactions
- **REST API**: Full API for message processing and administration
- **Unit Tests**: Comprehensive test coverage

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WhatsApp      │    │   ACS Service   │    │   PostgreSQL    │
│   User          │───▶│   (Azure)       │───▶│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Redis Cache   │◀───│  Bot Handler    │───▶│   OpenAI API    │
│   (Context)     │    │   (Django)      │    │   (Fallback)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Installation

### 1. Add to Django Settings

Add the WhatsApp bot app to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ... other apps
    'apps.whatsapp_bot',
]
```

### 2. Environment Variables

Add the following environment variables to your `.env` file:

```bash
# Azure Communication Services (ACS)
ACS_WHATSAPP_ENDPOINT=https://your-acs-resource.communication.azure.com
ACS_WHATSAPP_API_KEY=your-acs-access-key
ACS_PHONE_NUMBER=whatsapp:+1234567890
WHATSAPP_CHANNEL_ID_GUID=your-channel-registration-id

# Database and Redis (if not already configured)
DATABASE_URL=postgresql://user:password@localhost:5432/vea_webapp
AZURE_REDIS_CONNECTIONSTRING=localhost
AZURE_REDIS_CONNECTIONSTRING=6379
AZURE_REDIS_CONNECTIONSTRING=
AZURE_REDIS_CONNECTIONSTRING=0

# OpenAI (for fallback responses)
OPENAI_API_KEY=your-openai-api-key
```

### 3. Run Migrations

```bash
python manage.py makemigrations whatsapp_bot
python manage.py migrate
```

### 4. Create Initial Templates

Create the required WhatsApp templates in your Django admin or via management command:

```python
from apps.whatsapp_bot.models import WhatsAppTemplate

# Donations template
WhatsAppTemplate.objects.create(
    template_name='vea_info_donativos',
    template_id='donations_template_001',
    language='es',
    category='donations',
    parameters=[
        'customer_name', 'ministry_name', 'bank_name', 'beneficiary_name',
        'account_number', 'clabe_number', 'contact_name', 'contact_phone'
    ],
    is_active=True
)

# Ministry contact template
WhatsAppTemplate.objects.create(
    template_name='vea_contacto_ministerio',
    template_id='ministry_template_001',
    language='es',
    category='ministry',
    parameters=['customer_name', 'ministry_name', 'contact_name', 'contact_phone'],
    is_active=True
)

# Event information template
WhatsAppTemplate.objects.create(
    template_name='vea_event_info',
    template_id='event_template_001',
    language='es',
    category='events',
    parameters=['customer_name', 'event_name', 'event_date', 'event_location'],
    is_active=True
)

# General request template
WhatsAppTemplate.objects.create(
    template_name='vea_request_received',
    template_id='general_template_001',
    language='es',
    category='general',
    parameters=['customer_name', 'request_summary'],
    is_active=True
)
```

## Usage

### 1. Webhook Endpoint

The bot receives messages via webhook from ACS:

```
POST /api/v1/whatsapp/webhook/
```

Expected payload:
```json
{
    "from": "whatsapp:+1234567890",
    "to": "whatsapp:+0987654321",
    "message": {
        "text": "I need donation information"
    },
    "timestamp": "2024-01-01T12:00:00Z"
}
```

### 2. API Endpoints

#### Send Message (Authenticated)
```
POST /api/v1/whatsapp/send/
```

```json
{
    "phone_number": "+1234567890",
    "message": "I need donation information",
    "context": {
        "user_id": "123",
        "session_id": "abc123"
    }
}
```

#### Get Interaction History
```
GET /api/v1/whatsapp/history/?phone_number=+1234567890&limit=10
```

#### Get Bot Statistics
```
GET /api/v1/whatsapp/statistics/
```

#### Get Templates
```
GET /api/v1/whatsapp/templates/?category=donations&active_only=true
```

#### Test Template
```
POST /api/v1/whatsapp/templates/test/
```

```json
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
    }
}
```

#### Health Check
```
GET /api/v1/whatsapp/health/
```

### 3. Template Parameters

#### vea_info_donativos
- `customer_name`: Customer's name
- `ministry_name`: Ministry name
- `bank_name`: Bank name
- `beneficiary_name`: Beneficiary name
- `account_number`: Bank account number
- `clabe_number`: CLABE number
- `contact_name`: Contact person name
- `contact_phone`: Contact phone number

#### vea_contacto_ministerio
- `customer_name`: Customer's name
- `ministry_name`: Ministry name
- `contact_name`: Ministry contact name
- `contact_phone`: Ministry contact phone

#### vea_event_info
- `customer_name`: Customer's name
- `event_name`: Event name
- `event_date`: Event date
- `event_location`: Event location

#### vea_request_received
- `customer_name`: Customer's name
- `request_summary`: Summary of the request

## Data Integration

### PostgreSQL Queries

The bot automatically queries PostgreSQL for dynamic data:

#### Donation Information
```sql
SELECT 
    d.id, d.amount, d.donation_date, d.donation_type,
    b.name as bank_name, b.account_number, b.clabe_number,
    c.first_name || ' ' || c.last_name as beneficiary_name,
    c.phone as contact_phone
FROM donations_donation d
LEFT JOIN donations_donationtype dt ON d.donation_type_id = dt.id
LEFT JOIN directory_contact c ON d.beneficiary_id = c.id
LEFT JOIN (
    SELECT 
        'Banco Azteca' as name,
        '1234567890' as account_number,
        '012345678901234567' as clabe_number
) b ON true
WHERE c.first_name ILIKE %s OR c.last_name ILIKE %s
ORDER BY d.donation_date DESC
LIMIT 1
```

#### Ministry Contact
```sql
SELECT 
    c.first_name || ' ' || c.last_name as contact_name,
    c.phone as contact_phone, c.email
FROM directory_contact c
WHERE c.role = 'ministry_contact' 
AND (c.first_name ILIKE %s OR c.last_name ILIKE %s)
LIMIT 1
```

#### Event Information
```sql
SELECT 
    e.title, e.date, e.location, e.description
FROM events_event e
WHERE e.title ILIKE %s
ORDER BY e.date DESC
LIMIT 1
```

### Redis Caching

The bot uses Redis for:
- Caching frequently accessed data (TTL: 1 hour)
- Storing conversation context
- Session management

## Intent Detection

The bot detects user intent using keyword matching:

- **Donations**: "donativo", "donación", "donar", "apoyo"
- **Ministry**: "ministerio", "contacto", "pastor", "líder"
- **Events**: "evento", "actividad", "reunión", "conferencia"
- **General**: "información", "ayuda", "soporte", "consulta"

## Fallback Responses

When no template matches or intent is unknown, the bot uses OpenAI with RAG:

1. Generates embedding for user message
2. Finds similar content using EmbeddingManager
3. Creates context-aware prompt
4. Generates structured fallback response
5. Sends via ACS text message

## Logging and Monitoring

### Interaction Logging

All interactions are logged to the database with:
- Phone number
- Message text
- Detected intent
- Template used
- Response sent
- Processing time
- Success/failure status
- Error messages
- Context data

### Redis Context Storage

Conversation context is stored in Redis with:
- User session data
- Interaction history
- Last intent
- Template usage
- Session duration

### Admin Interface

Access the Django admin at `/admin/` to:
- View and manage WhatsApp templates
- Monitor interactions
- View conversation contexts
- Configure data sources
- Generate reports

## Testing

Run the comprehensive test suite:

```bash
python manage.py test apps.whatsapp_bot.tests
```

### Test Coverage

- Model creation and validation
- Service functionality
- API endpoints
- Intent detection
- Template processing
- Error handling
- Redis operations
- ACS integration

## Deployment

### Azure App Service

1. Configure environment variables in Azure App Service
2. Set up ACS webhook URL: `https://your-app.azurewebsites.net/api/v1/whatsapp/webhook/`
3. Configure CORS if needed
4. Set up monitoring and logging

### Environment Variables for Production

```bash
# Production settings
DEBUG=False
ALLOWED_HOSTS=your-app.azurewebsites.net

# ACS Configuration
ACS_WHATSAPP_ENDPOINT=https://your-acs-resource.communication.azure.com
ACS_WHATSAPP_API_KEY=your-production-access-key
ACS_PHONE_NUMBER=whatsapp:+1234567890
WHATSAPP_CHANNEL_ID_GUID=your-production-channel-id

# Database
DATABASE_URL=postgresql://user:password@your-db-host:5432/vea_webapp

# Redis
AZURE_REDIS_CONNECTIONSTRING=your-redis-host
AZURE_REDIS_CONNECTIONSTRING=6379
AZURE_REDIS_CONNECTIONSTRING=your-redis-password
AZURE_REDIS_CONNECTIONSTRING=true

# OpenAI
OPENAI_API_KEY=your-openai-api-key
```

## Security Considerations

1. **Webhook Authentication**: Implement webhook signature verification
2. **Rate Limiting**: Add rate limiting to prevent abuse
3. **Input Validation**: Validate all incoming messages
4. **Error Handling**: Don't expose sensitive information in error messages
5. **Logging**: Avoid logging sensitive data
6. **CORS**: Configure CORS properly for production

## Troubleshooting

### Common Issues

1. **ACS Connection Failed**
   - Verify ACS endpoint and access key
   - Check network connectivity
   - Validate phone number format

2. **Template Not Found**
   - Ensure template is registered in ACS
   - Check template name and parameters
   - Verify template is active in database

3. **Database Connection Issues**
   - Check DATABASE_URL configuration
   - Verify database permissions
   - Check network connectivity

4. **Redis Connection Issues**
   - Verify Redis host and port
   - Check authentication credentials
   - Ensure Redis is running

5. **OpenAI Fallback Not Working**
   - Verify OpenAI API key
   - Check API quota and limits
   - Validate prompt formatting

### Debug Mode

Enable debug logging:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'apps.whatsapp_bot': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## Contributing

1. Follow the existing code style
2. Add comprehensive tests for new features
3. Update documentation
4. Ensure all tests pass
5. Add type hints and docstrings

## License

This project is licensed under the MIT License - see the LICENSE file for details. 