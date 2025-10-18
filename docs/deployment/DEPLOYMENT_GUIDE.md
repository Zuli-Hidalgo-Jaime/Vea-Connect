# VeaConnect Deployment Guide

## Overview

This document provides comprehensive deployment procedures for the VeaConnect application on Microsoft Azure, following enterprise security standards and best practices for production environments.

## Prerequisites

### Azure Resources Required

- **Azure Subscription**: Active subscription with appropriate permissions
- **Resource Group**: Dedicated resource group for the application
- **Service Principal**: For automated deployments and service authentication
- **Key Vault**: For secure secrets management

### Development Environment

- **Python 3.10+**: Required for application development
- **Azure CLI**: Latest version for resource management
- **Docker**: For containerized deployments (optional)
- **Git**: Version control system

### Security Requirements

- **SSL Certificates**: Valid certificates for HTTPS enforcement
- **Network Security**: VNet configuration for resource isolation
- **Access Control**: RBAC implementation for resource access
- **Monitoring**: Application Insights and Log Analytics workspace

## Infrastructure Deployment

### Resource Group Creation

```bash
# Create resource group
az group create \
  --name vea-connect-rg \
  --location eastus \
  --tags Environment=Production Project=VeaConnect
```

### Network Security Configuration

```bash
# Create virtual network
az network vnet create \
  --name vea-connect-vnet \
  --resource-group vea-connect-rg \
  --subnet-name default \
  --address-prefix 10.0.0.0/16 \
  --subnet-prefix 10.0.1.0/24

# Create network security group
az network nsg create \
  --name vea-connect-nsg \
  --resource-group vea-connect-rg

# Configure NSG rules
az network nsg rule create \
  --name allow-https \
  --nsg-name vea-connect-nsg \
  --resource-group vea-connect-rg \
  --protocol tcp \
  --priority 100 \
  --destination-port-range 443 \
  --access allow
```

### Database Deployment

```bash
# Create PostgreSQL server
az postgres flexible-server create \
  --name vea-postgresql-server \
  --resource-group vea-connect-rg \
  --location eastus \
  --admin-user vea_admin \
  --admin-password <secure_password> \
  --sku-name Standard_B1ms \
  --version 13 \
  --storage-size 32 \
  --vnet vea-connect-vnet \
  --subnet default

# Create database
az postgres flexible-server db create \
  --name vea_database \
  --server-name vea-postgresql-server \
  --resource-group vea-connect-rg
```

### Storage Account Configuration

```bash
# Create storage account
az storage account create \
  --name veastorageaccount \
  --resource-group vea-connect-rg \
  --location eastus \
  --sku Standard_LRS \
  --kind StorageV2 \
  --https-only true \
  --min-tls-version TLS1_2

# Create containers
az storage container create \
  --name static \
  --account-name veastorageaccount

az storage container create \
  --name media \
  --account-name veastorageaccount

az storage container create \
  --name documents \
  --account-name veastorageaccount
```

## Application Deployment

### Django App Service Configuration

```bash
# Create App Service Plan
az appservice plan create \
  --name vea-app-service-plan \
  --resource-group vea-connect-rg \
  --sku B1 \
  --is-linux

# Create Web App
az webapp create \
  --name vea-webapp-process-botconnect \
  --resource-group vea-connect-rg \
  --plan vea-app-service-plan \
  --runtime "PYTHON|3.10" \
  --deployment-local-git

# Configure environment variables
az webapp config appsettings set \
  --name vea-webapp-process-botconnect \
  --resource-group vea-connect-rg \
  --settings \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    SECRET_KEY=<django_secret_key> \
    DEBUG=False \
    ALLOWED_HOSTS=*.azurewebsites.net \
    AZURE_POSTGRESQL_NAME=vea_database \
    AZURE_POSTGRESQL_USERNAME=vea_admin@vea-postgresql-server \
    AZURE_POSTGRESQL_PASSWORD=<database_password> \
    AZURE_POSTGRESQL_HOST=vea-postgresql-server.postgres.database.azure.com \
    AZURE_STORAGE_CONNECTION_STRING=<storage_connection_string>
```

### Azure Functions Deployment

```bash
# Create Function App
az functionapp create \
  --name vea-embedding-api \
  --resource-group vea-connect-rg \
  --consumption-plan-location eastus \
  --runtime python \
  --runtime-version 3.10 \
  --functions-version 4 \
  --storage-account veastorageaccount

# Configure Function App settings
az functionapp config appsettings set \
  --name vea-embedding-api \
  --resource-group vea-connect-rg \
  --settings \
    FUNCTIONS_WORKER_RUNTIME=python \
    FUNCTIONS_EXTENSION_VERSION=~4 \
    AZURE_OPENAI_ENDPOINT=<openai_endpoint> \
    AZURE_OPENAI_API_KEY=<openai_api_key> \
    ACS_CONNECTION_STRING=<acs_connection_string>
```

## Security Configuration

### Key Vault Integration

```bash
# Create Key Vault
az keyvault create \
  --name vea-connect-kv \
  --resource-group vea-connect-rg \
  --location eastus \
  --sku standard \
  --enabled-for-deployment true \
  --enabled-for-disk-encryption true \
  --enabled-for-template-deployment true

# Store secrets
az keyvault secret set \
  --vault-name vea-connect-kv \
  --name django-secret-key \
  --value <django_secret_key>

az keyvault secret set \
  --vault-name vea-connect-kv \
  --name database-password \
  --value <database_password>
```

### Network Security Implementation

```bash
# Configure private endpoints
az network private-endpoint create \
  --name postgres-private-endpoint \
  --resource-group vea-connect-rg \
  --vnet-name vea-connect-vnet \
  --subnet default \
  --private-connection-resource-id <postgres_resource_id> \
  --group-id postgresqlServer \
  --connection-name postgres-connection

# Configure service endpoints
az network vnet subnet update \
  --name default \
  --resource-group vea-connect-rg \
  --vnet-name vea-connect-vnet \
  --service-endpoints Microsoft.Web Microsoft.Storage
```

## Monitoring and Logging

### Application Insights Setup

```bash
# Create Application Insights
az monitor app-insights component create \
  --app vea-connect-insights \
  --location eastus \
  --resource-group vea-connect-rg \
  --application-type web

# Configure monitoring
az webapp config appsettings set \
  --name vea-webapp-process-botconnect \
  --resource-group vea-connect-rg \
  --settings \
    APPLICATIONINSIGHTS_CONNECTION_STRING=<app_insights_connection_string>
```

### Log Analytics Configuration

```bash
# Create Log Analytics workspace
az monitor log-analytics workspace create \
  --resource-group vea-connect-rg \
  --workspace-name vea-connect-logs \
  --location eastus

# Configure diagnostic settings
az monitor diagnostic-settings create \
  --name vea-connect-diagnostics \
  --resource <webapp_resource_id> \
  --workspace <log_analytics_workspace_id> \
  --logs '[{"category": "AppServiceHTTPLogs", "enabled": true}, {"category": "AppServiceConsoleLogs", "enabled": true}]'
```

## Deployment Pipeline

### GitHub Actions Configuration

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Azure

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        python manage.py test
    
    - name: Deploy to Azure Web App
      uses: azure/webapps-deploy@v2
      with:
        app-name: 'vea-webapp-process-botconnect'
        publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
```

### Environment-Specific Configurations

#### Development Environment

```bash
# Development-specific settings
az webapp config appsettings set \
  --name vea-webapp-dev \
  --resource-group vea-connect-rg \
  --settings \
    DEBUG=True \
    ENVIRONMENT=development \
    LOG_LEVEL=DEBUG
```

#### Staging Environment

```bash
# Staging-specific settings
az webapp config appsettings set \
  --name vea-webapp-staging \
  --resource-group vea-connect-rg \
  --settings \
    DEBUG=False \
    ENVIRONMENT=staging \
    LOG_LEVEL=INFO
```

#### Production Environment

```bash
# Production-specific settings
az webapp config appsettings set \
  --name vea-webapp-process-botconnect \
  --resource-group vea-connect-rg \
  --settings \
    DEBUG=False \
    ENVIRONMENT=production \
    LOG_LEVEL=WARNING
```

## Post-Deployment Verification

### Health Checks

```bash
# Verify application health
curl -f https://vea-webapp-process-botconnect.azurewebsites.net/health/

# Verify database connectivity
python manage.py check --deploy

# Verify static files
python manage.py collectstatic --noinput
```

### Security Validation

```bash
# Verify HTTPS enforcement
curl -I http://vea-webapp-process-botconnect.azurewebsites.net/
# Should redirect to HTTPS

# Verify security headers
curl -I https://vea-webapp-process-botconnect.azurewebsites.net/
# Check for security headers in response
```

### Performance Testing

```bash
# Run load tests
ab -n 1000 -c 10 https://vea-webapp-process-botconnect.azurewebsites.net/

# Monitor application performance
az monitor metrics list \
  --resource <webapp_resource_id> \
  --metric "Requests" \
  --interval PT1M
```

## Maintenance Procedures

### Backup Procedures

```bash
# Database backup
az postgres flexible-server backup create \
  --name vea-postgresql-server \
  --resource-group vea-connect-rg

# Storage account backup
az storage account blob-service-properties update \
  --account-name veastorageaccount \
  --enable-delete-retention true \
  --delete-retention-days 30
```

### Update Procedures

```bash
# Application updates
git pull origin main
python manage.py migrate
python manage.py collectstatic --noinput

# Dependency updates
pip install --upgrade -r requirements.txt
python manage.py check --deploy
```

### Monitoring and Alerting

```bash
# Configure alerts
az monitor metrics alert create \
  --name "High CPU Usage" \
  --resource-group vea-connect-rg \
  --scopes <webapp_resource_id> \
  --condition "avg Percentage CPU > 80" \
  --description "Alert when CPU usage exceeds 80%"
```

## Troubleshooting

### Common Issues

1. **Database Connection Failures**
   - Verify network security group rules
   - Check connection string configuration
   - Validate database server status

2. **Application Startup Failures**
   - Review application logs in Azure Portal
   - Verify environment variable configuration
   - Check Python runtime compatibility

3. **Performance Issues**
   - Monitor Application Insights metrics
   - Review database query performance
   - Check resource utilization

### Log Analysis

```bash
# View application logs
az webapp log tail \
  --name vea-webapp-process-botconnect \
  --resource-group vea-connect-rg

# Download logs for analysis
az webapp log download \
  --name vea-webapp-process-botconnect \
  --resource-group vea-connect-rg
```

## Security Considerations

### Access Control

- Implement least privilege access
- Regular access reviews
- Multi-factor authentication enforcement
- Service principal rotation

### Data Protection

- Encryption at rest and in transit
- Regular security assessments
- Vulnerability scanning
- Compliance monitoring

### Incident Response

- Automated alerting for security events
- Incident response procedures
- Forensic analysis capabilities
- Communication protocols

---

**Document Version**: 2.0  
**Last Updated**: December 2024  
**Next Review**: March 2025  
**Classification**: Internal Use Only 