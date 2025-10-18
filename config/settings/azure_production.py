# Configuración específica para Azure App Service
# Este archivo deshabilita completamente django-storages para evitar errores

import os
import sys

# Deshabilitar django-storages completamente
os.environ['DISABLE_DJANGO_STORAGES'] = 'True'

# Importar configuración base pero sin django-storages
from .base import *

# Configuración de producción para Azure
DEBUG = False

# Configuración de seguridad para producción
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Configuración HTTPS
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Configuración de CORS
CORS_ALLOWED_ORIGINS = [
    "https://veaconnect-webapp-prod.azurewebsites.net",
    "https://veaconnect-webapp-prod-c7aaezbce3ftacdp.centralus-01.azurewebsites.net",
]
CORS_ALLOW_CREDENTIALS = True

# Configuración de seguridad
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Configuración de base de datos para producción
# Usar variables de entorno de Azure App Service
db_name = os.environ.get('AZURE_POSTGRESQL_NAME')
db_user = os.environ.get('AZURE_POSTGRESQL_USERNAME')
db_password = os.environ.get('AZURE_POSTGRESQL_PASSWORD')
db_host = os.environ.get('AZURE_POSTGRESQL_HOST')
db_port = os.environ.get('DB_PORT', '5432')

# Verificar que todas las variables de base de datos estén configuradas
if not all([db_name, db_user, db_password, db_host]):
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

# Azure OpenAI Configuration for production
AZURE_OPENAI_ENDPOINT = os.environ.get('AZURE_OPENAI_ENDPOINT')
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

# Importar las clases de Azure Storage personalizadas
from config.azure_storage import AzureMediaStorage, is_azure_storage_configured

# Configuración de archivos de media - usar Azure Storage si está configurado
if is_azure_storage_configured():
    # Usar Azure Storage personalizado si está configurado
    DEFAULT_FILE_STORAGE = 'config.azure_storage.AzureMediaStorage'
    print("✅ Azure Storage configurado para archivos multimedia")
else:
    # Fallback a almacenamiento local
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    print("⚠️ Azure Storage no configurado, usando almacenamiento local")

# Configuración de archivos estáticos
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# Configuración de archivos media
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Configuración de caché con Redis para conversaciones de WhatsApp
REDIS_URL = os.environ.get('AZURE_REDIS_URL')
REDIS_TTL_SECS = int(os.environ.get('REDIS_TTL_SECS', '86400'))  # 24 horas por defecto

if REDIS_URL:
    # Usar Redis si está configurado
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "CONNECTION_POOL_KWARGS": {
                    "max_connections": 50,
                    "retry_on_timeout": True,
                },
                "SOCKET_CONNECT_TIMEOUT": 5,
                "SOCKET_TIMEOUT": 5,
                "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
                "IGNORE_EXCEPTIONS": True,
            },
            "KEY_PREFIX": "vea_connect",
            "TIMEOUT": REDIS_TTL_SECS,
        }
    }
    print("Redis cache configurado para conversaciones de WhatsApp")
else:
    # Fallback a LocMemCache si Redis no está disponible
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-snowflake",
            "TIMEOUT": 3600,  # 1 hora para cache local
        }
    }
    print("Redis no configurado, usando LocMemCache (no persistente para conversaciones)")

# Configuración de sesiones
SESSION_ENGINE = "django.contrib.sessions.backends.db"

# Configuración de logging para Azure con Application Insights
import logging

# Configurar logger para cache
logger = logging.getLogger(__name__)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'level': 'INFO',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'formatter': 'verbose',
            'level': 'INFO',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.whatsapp_bot': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'utils.redis_cache': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}

# Security: Restrict allowed hosts to actual domains
ALLOWED_HOSTS = [
    os.environ.get('WEBSITE_HOSTNAME', 'veaconnect-webapp-prod-c7aaezbce3ftacdp.centralus-01.azurewebsites.net'),
    'veaconnect-webapp-prod-c7aaezbce3ftacdp.centralus-01.azurewebsites.net',
    'veaconnect-webapp-prod.azurewebsites.net',
    '*.azurewebsites.net',  # Permitir todos los subdominios de Azure
    '169.254.130.2',  # IP interna de Azure App Service
    '169.254.130.4',  # IP específica del error en logs
    '169.254.0.0/16',  # Rango de IPs internas de Azure
] + (os.environ.get('ALLOWED_HOSTS', '').split(',') if os.environ.get('ALLOWED_HOSTS') else [])

# Configurar CSRF_TRUSTED_ORIGINS de manera segura
website_hostname = os.environ.get('WEBSITE_HOSTNAME', 'veaconnect-webapp-prod-c7aaezbce3ftacdp.centralus-01.azurewebsites.net')
if website_hostname:
    CSRF_TRUSTED_ORIGINS = [f'https://{website_hostname}']
else:
    CSRF_TRUSTED_ORIGINS = ['https://localhost', 'https://127.0.0.1']

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
] + MIDDLEWARE[1:] 