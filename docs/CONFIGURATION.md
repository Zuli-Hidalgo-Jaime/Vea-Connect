# VEA Connect Configuration Guide

This document lists all required environment variables for the VEA Connect application.

## Environment Variables Overview

All sensitive configuration values must be set as environment variables. Never hardcode credentials in the source code.

## Database Configuration

### PostgreSQL (Production)
```bash
# Required for production
AZURE_POSTGRESQL_NAME=your_database_name
AZURE_POSTGRESQL_USERNAME=your_database_user
AZURE_POSTGRESQL_PASSWORD=your_database_password
AZURE_POSTGRESQL_HOST=your_database_host
DB_PORT=5432

# Alternative: Use DATABASE_URL
DATABASE_URL=postgresql://user:password@host:port/dbname
```

### SQLite (Development)
```bash
# For local development
DATABASE_URL=sqlite:///db.sqlite3
```

## Django Configuration

### Core Settings
```bash
# Required
SECRET_KEY=your_django_secret_key_here
DEBUG=False  # Set to True only for development
DJANGO_SETTINGS_MODULE=config.settings.production

# Optional
ALLOWED_HOSTS=domain1.com,domain2.com
CSRF_TRUSTED_ORIGINS=https://domain1.com,https://domain2.com
```

## Azure Services Configuration

### Azure OpenAI
```bash
# Required
AZURE_OPENAI_ENDPOINT=https://your-openai-service.openai.azure.com/
AZURE_OPENAI_API_KEY=your_openai_api_key
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-35-turbo
AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT=text-embedding-ada-002
AZURE_OPENAI_CHAT_API_VERSION=2025-01-01-preview
AZURE_OPENAI_EMBEDDINGS_API_VERSION=2023-05-15
```

### Azure Computer Vision
```bash
# Required
VISION_ENDPOINT=https://your-vision-service.cognitiveservices.azure.com/
VISION_KEY=your_vision_api_key
```

### Azure AI Search
```bash
# Required
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_API_KEY=your_search_api_key
AZURE_SEARCH_INDEX_NAME=vea-connect-index
```

### Azure Storage
```bash
# Required - Choose one approach
# Option 1: Connection String
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=your_account;AccountKey=your_key;EndpointSuffix=core.windows.net

# Option 2: Individual values
AZURE_STORAGE_ACCOUNT_NAME=your_storage_account
AZURE_STORAGE_ACCOUNT_KEY=your_storage_key
AZURE_CONTAINER=your_container_name

# Legacy compatibility
BLOB_ACCOUNT_NAME=your_storage_account
BLOB_ACCOUNT_KEY=your_storage_key
BLOB_CONTAINER_NAME=your_container_name
```

### Azure Communication Services (WhatsApp)
```bash
# Required
ACS_CONNECTION_STRING=endpoint=https://your-acs-service.communication.azure.com/;accesskey=your_access_key
ACS_EVENT_GRID_TOPIC_ENDPOINT=https://your-acs-service.communication.azure.com/
ACS_EVENT_GRID_TOPIC_KEY=your_event_grid_topic_key
ACS_PHONE_NUMBER=+1234567890
ACS_WHATSAPP_API_KEY=your_whatsapp_api_key
ACS_WHATSAPP_ENDPOINT=https://your-acs-service.communication.azure.com/
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token
WHATSAPP_CHANNEL_ID_GUID=your_channel_id_guid
```

### Azure Key Vault (Optional)
```bash
# For enhanced security
AZURE_KEYVAULT_RESOURCEENDPOINT=https://your-keyvault.vault.azure.net/
AZURE_KEYVAULT_SCOPE=https://vault.azure.net/.default
AZURE_TENANT_ID=your_tenant_id
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret
```

### Application Insights
```bash
# Required for monitoring
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=your_key;IngestionEndpoint=https://your_endpoint/;LiveEndpoint=https://your_live_endpoint/;ApplicationId=your_app_id
ApplicationInsightsAgent_EXTENSION_VERSION=~3
```

## Azure Functions Configuration

### Function App Settings
```bash
# Required
FUNCTION_APP_URL=https://your-function-app.azurewebsites.net
FUNCTION_APP_KEY=your_function_app_key
```

### Queue Configuration
```bash
# Optional
QUEUE_NAME=doc-processing
```

## Build and Deployment Configuration

### Azure App Service
```bash
# Build settings
BUILD_FLAGS=UseExpressBuild
SCM_DO_BUILD_DURING_DEPLOYMENT=true
XDT_MicrosoftApplicationInsights_Mode=default
```

## Security Configuration

### SSL and Security Headers
```bash
# These are automatically configured in production settings
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

## Development Configuration

### Local Development
```bash
# For local development only
DEBUG=True
DJANGO_SETTINGS_MODULE=config.settings.development
ALLOWED_HOSTS=localhost,127.0.0.1
```

## Environment Setup Instructions

### 1. Azure App Service Configuration
1. Go to Azure Portal > App Service > Configuration
2. Add each environment variable under "Application settings"
3. Ensure all sensitive values are marked as "Slot setting" if using deployment slots

### 2. Local Development
1. Copy `env.example` to `.env`
2. Fill in the required values for your local environment
3. Never commit `.env` files to version control

### 3. Azure Key Vault Integration (Recommended)
1. Store sensitive values in Azure Key Vault
2. Configure managed identity for the App Service
3. Update the application to use Key Vault references

## Validation

### Required Variables Check
The application will validate that all required environment variables are present on startup. Missing variables will cause startup failures.

### Security Validation
- All credentials must be provided via environment variables
- No hardcoded secrets in source code
- SSL/TLS encryption enabled in production
- Proper CORS and CSRF configuration

## Troubleshooting

### Common Issues
1. **Missing SECRET_KEY**: Application will not start
2. **Invalid database credentials**: Database connection errors
3. **Missing Azure service keys**: Service integration failures
4. **Incorrect ALLOWED_HOSTS**: 400 Bad Request errors

### Debug Mode
For troubleshooting, temporarily set:
```bash
DEBUG=True
DJANGO_SETTINGS_MODULE=config.settings.development
```

## Security Best Practices

1. **Never hardcode credentials** in source code
2. **Use Azure Key Vault** for production secrets
3. **Rotate credentials regularly**
4. **Use managed identities** when possible
5. **Enable audit logging** for all Azure services
6. **Monitor for suspicious activity**
7. **Keep dependencies updated**

## Support

For configuration issues, check:
1. Azure App Service logs
2. Application Insights
3. Django error logs
4. Azure service-specific logs
