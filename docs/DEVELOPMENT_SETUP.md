# Development Setup Guide

This guide provides step-by-step instructions for setting up the VEA Connect WebApp development environment.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Configuration](#database-configuration)
4. [Azure Services Setup](#azure-services-setup)
5. [Application Configuration](#application-configuration)
6. [Running the Application](#running-the-application)
7. [Testing Setup](#testing-setup)
8. [Development Tools](#development-tools)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

- **Python 3.10+** - [Download from python.org](https://www.python.org/downloads/)
- **Git** - [Download from git-scm.com](https://git-scm.com/downloads)
- **Docker Desktop** - [Download from docker.com](https://www.docker.com/products/docker-desktop)
- **Azure CLI** - [Installation guide](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)

### Recommended Tools

- **VS Code** - [Download from code.visualstudio.com](https://code.visualstudio.com/)
- **PostgreSQL** - [Download from postgresql.org](https://www.postgresql.org/download/)
- **Redis** - [Download from redis.io](https://redis.io/download)

### VS Code Extensions

Install the following extensions for optimal development experience:

```json
{
    "recommendations": [
        "ms-python.python",
        "ms-python.black-formatter",
        "ms-python.flake8",
        "ms-python.isort",
        "ms-python.pylint",
        "ms-python.pytest-adapter",
        "ms-vscode.vscode-json",
        "ms-azuretools.vscode-docker",
        "ms-vscode.powershell"
    ]
}
```

## Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/vea-connect-webapp.git
cd vea-connect-webapp
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install Development Dependencies

```bash
pip install -r requirements-dev.txt
```

### 5. Install Pre-commit Hooks

```bash
pre-commit install
```

## Database Configuration

### Option 1: Local PostgreSQL

1. **Install PostgreSQL** (if not already installed)
2. **Create Database**:

```sql
CREATE DATABASE vea_connect_dev;
CREATE USER vea_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE vea_connect_dev TO vea_user;
```

3. **Configure Environment Variables**:

```bash
# .env
DATABASE_URL=postgresql://vea_user:your_password@localhost:5432/vea_connect_dev
```

### Option 2: Docker PostgreSQL

```bash
docker run --name vea-postgres \
  -e POSTGRES_DB=vea_connect_dev \
  -e POSTGRES_USER=vea_user \
  -e POSTGRES_PASSWORD=your_password \
  -p 5432:5432 \
  -d postgres:15
```

### Option 3: Azure Database for PostgreSQL

1. **Create Azure Database**:
```bash
az postgres flexible-server create \
  --resource-group your-rg \
  --name vea-db-dev \
  --admin-user vea_admin \
  --admin-password "YourSecurePassword123!" \
  --sku-name Standard_B1ms \
  --version 15
```

2. **Configure Firewall**:
```bash
az postgres flexible-server firewall-rule create \
  --resource-group your-rg \
  --name vea-db-dev \
  --rule-name allow-dev \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 255.255.255.255
```

## Azure Services Setup

### 1. Azure Storage Account

```bash
# Create storage account
az storage account create \
  --name veastorage \
  --resource-group your-rg \
  --location eastus \
  --sku Standard_LRS

# Get connection string
az storage account show-connection-string \
  --name veastorage \
  --resource-group your-rg
```

### 2. Azure AI Search

```bash
# Create search service
az search service create \
  --name vea-search \
  --resource-group your-rg \
  --location eastus \
  --sku basic

# Get admin key
az search admin-key show \
  --resource-group your-rg \
  --service-name vea-search
```

### 3. Azure OpenAI

```bash
# Create OpenAI resource
az cognitiveservices account create \
  --name vea-openai \
  --resource-group your-rg \
  --location eastus \
  --kind OpenAI \
  --sku S0

# Get endpoint and key
az cognitiveservices account show \
  --name vea-openai \
  --resource-group your-rg
```

### 4. Azure Communication Services

```bash
# Create communication service
az communication create \
  --name vea-communication \
  --resource-group your-rg \
  --location eastus \
  --data-location UnitedStates

# Get connection string
az communication list-key \
  --name vea-communication \
  --resource-group your-rg
```

## Application Configuration

### 1. Environment Variables

Create a `.env` file in the project root:

```bash
# Django Configuration
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DATABASE_URL=postgresql://vea_user:your_password@localhost:5432/vea_connect_dev

# Azure Storage
AZURE_STORAGE_ACCOUNT_NAME=veastorage
AZURE_STORAGE_ACCOUNT_KEY=your-storage-key
AZURE_CONTAINER=vea-container

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://vea-search.search.windows.net
AZURE_SEARCH_API_KEY=your-search-key
AZURE_SEARCH_INDEX_NAME=vea-index

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://vea-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=your-openai-key
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-35-turbo

# Azure Communication Services
ACS_CONNECTION_STRING=your-acs-connection-string
ACS_PHONE_NUMBER=whatsapp:+1234567890

# Redis Cache (Optional for development)
REDIS_URL=redis://localhost:6379/0

# Email Configuration (Optional)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### 2. Django Settings

The application uses different settings for different environments:

- `config.settings.development` - Local development
- `config.settings.test` - Testing environment
- `config.settings.production` - Production environment

### 3. Run Migrations

```bash
python manage.py migrate
```

### 4. Create Superuser

```bash
python manage.py createsuperuser
```

### 5. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

## Running the Application

### Development Server

```bash
# Run Django development server
python manage.py runserver

# Run with specific settings
python manage.py runserver --settings=config.settings.development
```

### Docker Development

```bash
# Build and run with Docker Compose
docker-compose up --build

# Run specific services
docker-compose up db redis
```

### Background Services

```bash
# Run Celery worker (if using background tasks)
celery -A config worker --loglevel=info

# Run Celery beat (for scheduled tasks)
celery -A config beat --loglevel=info
```

## Testing Setup

### 1. Test Database

The application automatically uses a test database for running tests.

### 2. Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_models.py

# Run with coverage
pytest --cov=apps --cov-report=html

# Run with verbose output
pytest -v

# Run tests in parallel
pytest -n auto
```

### 3. Test Configuration

Create `pytest.ini` for test configuration:

```ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = config.settings.test
python_files = tests.py test_*.py *_tests.py
addopts = --strict-markers --disable-warnings
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

### 4. Test Data

```bash
# Load test fixtures
python manage.py loaddata tests/fixtures/test_data.json

# Create test data
python manage.py shell
```

```python
# In Django shell
from apps.donations.models import Donation
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.create_user('testuser', 'test@example.com', 'testpass123')
Donation.objects.create(title='Test Donation', amount=100.00, created_by=user)
```

## Development Tools

### 1. Code Quality Tools

```bash
# Format code with Black
black .

# Sort imports with isort
isort .

# Lint code with flake8
flake8

# Type checking with pyright
pyright

# Security scanning with bandit
bandit -r .
```

### 2. Database Tools

```bash
# Generate migration files
python manage.py makemigrations

# Show migration status
python manage.py showmigrations

# Reset database (development only)
python manage.py flush

# Create database backup
python manage.py dumpdata > backup.json

# Load database backup
python manage.py loaddata backup.json
```

### 3. Management Commands

```bash
# Check system health
python manage.py check

# Validate models
python manage.py validate

# Show URL patterns
python manage.py show_urls

# Create custom management command
python manage.py startapp myapp
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Issues

```bash
# Check database connection
python manage.py dbshell

# Test connection
python manage.py check --database default
```

#### 2. Azure Services Issues

```bash
# Test Azure Storage connection
python scripts/diagnostics/test_storage_only.py

# Test Azure AI Search
python scripts/diagnostics/test_search_service.py
```

#### 3. Environment Variable Issues

```bash
# Check environment variables
python manage.py shell
```

```python
import os
print(os.environ.get('DATABASE_URL'))
print(os.environ.get('AZURE_STORAGE_ACCOUNT_NAME'))
```

#### 4. Dependency Issues

```bash
# Update pip
pip install --upgrade pip

# Reinstall dependencies
pip uninstall -r requirements.txt -y
pip install -r requirements.txt

# Check for conflicts
pip check
```

#### 5. Migration Issues

```bash
# Reset migrations (development only)
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete
python manage.py makemigrations
python manage.py migrate
```

### Performance Issues

#### 1. Slow Database Queries

```python
# Enable query logging
import logging
l = logging.getLogger('django.db.backends')
l.setLevel(logging.DEBUG)
l.addHandler(logging.StreamHandler())
```

#### 2. Memory Issues

```bash
# Monitor memory usage
python -m memory_profiler manage.py runserver

# Check for memory leaks
pip install memory-profiler
```

### Debugging

#### 1. Django Debug Toolbar

Add to `INSTALLED_APPS` in development settings:

```python
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1']
```

#### 2. Logging Configuration

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'DEBUG',
    },
}
```

## Next Steps

1. **Read the Code Standards**: Review [CODE_STANDARDS.md](CODE_STANDARDS.md)
2. **Explore the API**: Check [API Documentation](api_documentation.md)
3. **Set up Monitoring**: Configure Application Insights
4. **Join the Team**: Review contribution guidelines

## Support

- **Documentation**: Check the [docs/](docs/) directory
- **Issues**: Create an issue on GitHub
- **Discussions**: Use GitHub Discussions for questions
- **Team Chat**: Join the development team chat

---

**Last Updated**: December 2024  
**Maintained By**: Development Team
