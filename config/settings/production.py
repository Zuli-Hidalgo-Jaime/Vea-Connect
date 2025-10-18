# pyright: reportMissingImports=false, reportAttributeAccessIssue=false, reportCallIssue=false

import os
from .base import *

# Configuración de producción para Azure
DEBUG = False

# Security Configuration
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
# SECURE_SSL_REDIRECT = True  # Comentado para evitar bucle de redirección en Azure
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Configuración de base de datos para producción
# Usar variables de entorno de Azure App Service
db_name = os.environ.get('AZURE_POSTGRESQL_NAME')
db_user = os.environ.get('AZURE_POSTGRESQL_USERNAME')
db_password = os.environ.get('AZURE_POSTGRESQL_PASSWORD')
db_host = os.environ.get('AZURE_POSTGRESQL_HOST')
db_port = os.environ.get('DB_PORT', '5432')

# Debug sanitizado: solo mostrar estado de configuración
print(f"DEBUG: AZURE_POSTGRESQL_NAME = {'SET' if db_name else 'NOT SET'}")
print(f"DEBUG: AZURE_POSTGRESQL_USERNAME = {'SET' if db_user else 'NOT SET'}")
print(f"DEBUG: AZURE_POSTGRESQL_HOST = {'SET' if db_host else 'NOT SET'}")
print(f"DEBUG: AZURE_POSTGRESQL_PASSWORD = {'SET' if db_password else 'NOT SET'}")

# Verificar que todas las variables de base de datos estén configuradas
if not all([db_name, db_user, db_password, db_host]):
    print("ERROR: Variables de base de datos faltantes:")
    print(f"  db_name: {'SET' if db_name else 'NOT SET'}")
    print(f"  db_user: {'SET' if db_user else 'NOT SET'}")
    print(f"  db_password: {'SET' if db_password else 'NOT SET'}")
    print(f"  db_host: {'SET' if db_host else 'NOT SET'}")
    raise ValueError(
        "Las variables de entorno de base de datos no están configuradas. "
        "Configure AZURE_POSTGRESQL_NAME, AZURE_POSTGRESQL_USERNAME, "
        "AZURE_POSTGRESQL_PASSWORD, y AZURE_POSTGRESQL_HOST en Azure App Service."
    )

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': db_name,
        'USER': db_user,
        'PASSWORD': db_password,
        'HOST': db_host,
        'PORT': db_port,
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# Configuración de Azure Blob Storage para producción
AZURE_STORAGE_ACCOUNT_NAME = os.environ.get('AZURE_STORAGE_ACCOUNT_NAME')
AZURE_STORAGE_ACCOUNT_KEY = os.environ.get('AZURE_STORAGE_ACCOUNT_KEY')
AZURE_ACCOUNT_NAME = os.environ.get('AZURE_ACCOUNT_NAME')
AZURE_ACCOUNT_KEY = os.environ.get('AZURE_ACCOUNT_KEY')
AZURE_CONTAINER = os.environ.get('AZURE_CONTAINER')
AZURE_STORAGE_CONNECTION_STRING = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')

# Variables de compatibilidad (fallback)
BLOB_ACCOUNT_NAME = os.environ.get('BLOB_ACCOUNT_NAME')
BLOB_ACCOUNT_KEY = os.environ.get('BLOB_ACCOUNT_KEY')
BLOB_CONTAINER_NAME = os.environ.get('BLOB_CONTAINER_NAME')

# Azure OpenAI Configuration para producción
AZURE_OPENAI_ENDPOINT = os.environ.get('AZURE_OPENAI_ENDPOINT', 'https://openai-veaconnect.openai.azure.com/')

# Azure AI Search Configuration
AZURE_SEARCH_ENDPOINT = os.environ.get('AZURE_SEARCH_ENDPOINT', 'https://ai-search-veaconnect-prod.search.windows.net')
AZURE_SEARCH_API_KEY = os.environ.get('AZURE_SEARCH_API_KEY')
AZURE_SEARCH_INDEX_NAME = os.environ.get('AZURE_SEARCH_INDEX_NAME', 'vea-connect-index')

# Azure Computer Vision Configuration for production
VISION_ENDPOINT = os.environ.get('VISION_ENDPOINT')
VISION_KEY = os.environ.get('VISION_KEY')
AZURE_OPENAI_CHAT_DEPLOYMENT = os.environ.get('AZURE_OPENAI_CHAT_DEPLOYMENT', 'gpt-35-turbo')
AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT = os.environ.get('AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT', 'text-embedding-ada-002')
AZURE_OPENAI_CHAT_API_VERSION = os.environ.get('AZURE_OPENAI_CHAT_API_VERSION', '2025-01-01-preview')
AZURE_OPENAI_EMBEDDINGS_API_VERSION = os.environ.get('AZURE_OPENAI_EMBEDDINGS_API_VERSION', '2023-05-15')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

# Azure Communication Services Configuration for production
ACS_CONNECTION_STRING = os.environ.get('ACS_CONNECTION_STRING')
ACS_EVENT_GRID_TOPIC_ENDPOINT = os.environ.get('ACS_EVENT_GRID_TOPIC_ENDPOINT')
ACS_EVENT_GRID_TOPIC_KEY = os.environ.get('ACS_EVENT_GRID_TOPIC_KEY')
ACS_PHONE_NUMBER = os.environ.get('ACS_PHONE_NUMBER')
ACS_WHATSAPP_API_KEY = os.environ.get('ACS_WHATSAPP_API_KEY')
ACS_WHATSAPP_ENDPOINT = os.environ.get('ACS_WHATSAPP_ENDPOINT')
WHATSAPP_ACCESS_TOKEN = os.environ.get('WHATSAPP_ACCESS_TOKEN')
WHATSAPP_CHANNEL_ID_GUID = os.environ.get('WHATSAPP_CHANNEL_ID_GUID')

# Azure Key Vault Configuration
AZURE_KEYVAULT_RESOURCEENDPOINT = os.environ.get('AZURE_KEYVAULT_RESOURCEENDPOINT', 'https://kv-vea-connect.vault.azure.net/')
AZURE_KEYVAULT_SCOPE = os.environ.get('AZURE_KEYVAULT_SCOPE', 'https://vault.azure.net/.default')

# Application Insights Configuration
APPLICATIONINSIGHTS_CONNECTION_STRING = os.environ.get('APPLICATIONINSIGHTS_CONNECTION_STRING')
ApplicationInsightsAgent_EXTENSION_VERSION = os.environ.get('ApplicationInsightsAgent_EXTENSION_VERSION', '~3')

# Queue Configuration
QUEUE_NAME = os.environ.get('QUEUE_NAME', 'doc-processing')

# Build Configuration
BUILD_FLAGS = os.environ.get('BUILD_FLAGS', 'UseExpressBuild')
SCM_DO_BUILD_DURING_DEPLOYMENT = os.environ.get('SCM_DO_BUILD_DURING_DEPLOYMENT', 'true')
XDT_MicrosoftApplicationInsights_Mode = os.environ.get('XDT_MicrosoftApplicationInsights_Mode', 'default')

# Configuración de archivos estáticos para producción
# Usar WhiteNoise para archivos estáticos en producción
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Configuración de Azure Blob Storage para archivos de media
AZURE_OVERWRITE_FILES = False
AZURE_URL_EXPIRATION_SECONDS = 259200  # 72 horas

# Configuración de archivos multimedia
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configuración de archivos estáticos
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# Configuración de caché local (sin Redis)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
        "TIMEOUT": 300,  # 5 minutos
    }
}

# Configuración de Celery
# Comentado temporalmente hasta que Celery esté disponible en Azure
# CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
# CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
# CELERY_ACCEPT_CONTENT = ['json']
# CELERY_TASK_SERIALIZER = 'json'
# CELERY_RESULT_SERIALIZER = 'json'
# CELERY_TIMEZONE = 'UTC'
# CELERY_TASK_TRACK_STARTED = True
# CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutos

# Configuración de sesiones
# Temporarily using database sessions instead of cache
SESSION_ENGINE = "django.contrib.sessions.backends.db"
# SESSION_CACHE_ALIAS = "default"

# Configuración de logging para Azure
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# No usar dotenv en producción

# Security: Restrict allowed hosts to actual domains
ALLOWED_HOSTS = [
    os.environ.get('WEBSITE_HOSTNAME', 'veaconnect-webapp-prod-c7aaezbce3ftacdp.centralus-01.azurewebsites.net'),
    '*.azurewebsites.net',  # Allow all Azure subdomains
] + (os.environ.get('ALLOWED_HOSTS', '').split(',') if os.environ.get('ALLOWED_HOSTS') else [])

# Configurar CSRF_TRUSTED_ORIGINS de manera segura
website_hostname = os.environ.get('WEBSITE_HOSTNAME', 'veaconnect-webapp-prod-c7aaezbce3ftacdp.centralus-01.azurewebsites.net')
if website_hostname:
    CSRF_TRUSTED_ORIGINS = [
        f'https://{website_hostname}',
        'https://vea-connect-g5dje9eba9bscnb6.centralus-01.azurewebsites.net',
        'https://*.azurewebsites.net'
    ]
else:
    # Fallback para desarrollo o cuando WEBSITE_HOSTNAME no está configurado
    CSRF_TRUSTED_ORIGINS = [
        'https://localhost', 
        'https://127.0.0.1',
        'https://vea-connect-g5dje9eba9bscnb6.centralus-01.azurewebsites.net',
        'https://*.azurewebsites.net'
    ]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
] + MIDDLEWARE[1:]

# MEDIA_URL ya está definido arriba como '/media/'