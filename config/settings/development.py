import os

# Cargar variables de entorno desde el archivo .env (solo en desarrollo local)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("python-dotenv no está instalado, continuando sin .env")

from .base import *

# Feature Flags para desarrollo
CACHE_LAYER_ENABLED = True  # Habilitar cache layer en desarrollo para testing
CONFIG_ADAPTER_ENABLED = False
CANARY_INGEST_ENABLED = False

# Configuración de base de datos
if os.getenv('CI_ENVIRONMENT') == 'true':
    # Configuración para CI/CD - usar SQLite para evitar dependencias externas
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3_test',
            'OPTIONS': {
                'timeout': 20,
            }
        }
    }
else:
    # Configuración para desarrollo local
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Variables específicas de Azure Blob Storage (opcionales en desarrollo)
AZURE_STORAGE_ACCOUNT_NAME = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
AZURE_STORAGE_ACCOUNT_KEY = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
AZURE_ACCOUNT_NAME = os.getenv('AZURE_ACCOUNT_NAME')
AZURE_ACCOUNT_KEY = os.getenv('AZURE_ACCOUNT_KEY')
AZURE_CONTAINER = os.getenv('AZURE_CONTAINER')
AZURE_STORAGE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
AZURE_STORAGE_CONTAINER_NAME = os.getenv('AZURE_STORAGE_CONTAINER_NAME') or os.getenv('AZURE_CONTAINER') or 'documents'

# Variables de compatibilidad (fallback)
BLOB_ACCOUNT_NAME = os.getenv('BLOB_ACCOUNT_NAME')
BLOB_ACCOUNT_KEY = os.getenv('BLOB_ACCOUNT_KEY')
BLOB_CONTAINER_NAME = os.getenv('BLOB_CONTAINER_NAME')

# Configuración de Azure Blob Storage (solo si las variables están disponibles)

# Azure OpenAI Configuration (opcional en desarrollo)
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_CHAT_DEPLOYMENT = os.getenv('AZURE_OPENAI_CHAT_DEPLOYMENT')
AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT = os.getenv('AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT')
AZURE_OPENAI_CHAT_API_VERSION = os.getenv('AZURE_OPENAI_CHAT_API_VERSION')
AZURE_OPENAI_EMBEDDINGS_API_VERSION = os.getenv('AZURE_OPENAI_EMBEDDINGS_API_VERSION')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Azure Communication Services Configuration (opcional en desarrollo)
ACS_CONNECTION_STRING = os.getenv('ACS_CONNECTION_STRING')
ACS_EVENT_GRID_TOPIC_ENDPOINT = os.getenv('ACS_EVENT_GRID_TOPIC_ENDPOINT')
ACS_EVENT_GRID_TOPIC_KEY = os.getenv('ACS_EVENT_GRID_TOPIC_KEY')
ACS_PHONE_NUMBER = os.getenv('ACS_PHONE_NUMBER')
ACS_WHATSAPP_API_KEY = os.getenv('ACS_WHATSAPP_API_KEY')
ACS_WHATSAPP_ENDPOINT = os.getenv('ACS_WHATSAPP_ENDPOINT')
WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
WHATSAPP_CHANNEL_ID_GUID = os.getenv('WHATSAPP_CHANNEL_ID_GUID')

# Azure Computer Vision Configuration (opcional en desarrollo)
VISION_ENDPOINT = os.getenv('VISION_ENDPOINT')
VISION_KEY = os.getenv('VISION_KEY')

# Azure AI Search Configuration (opcional en desarrollo)
AZURE_SEARCH_ENDPOINT = os.getenv('AZURE_SEARCH_ENDPOINT')
AZURE_SEARCH_API_KEY = os.getenv('AZURE_SEARCH_API_KEY') or os.getenv('AZURE_SEARCH_KEY')
AZURE_SEARCH_INDEX_NAME = os.getenv('AZURE_SEARCH_INDEX_NAME')

# Azure Redis Cache Configuration (opcional en desarrollo)
AZURE_REDIS_CONNECTIONSTRING = os.getenv('AZURE_REDIS_CONNECTIONSTRING')
REDIS_TTL_SECS = int(os.getenv('REDIS_TTL_SECS', 3600))

# Configuración de Redis para cache layer
REDIS_URL = os.getenv('REDIS_URL') or os.getenv('AZURE_REDIS_URL') or os.getenv('AZURE_REDIS_CONNECTIONSTRING')

# Azure Functions Configuration (opcional en desarrollo)
FUNCTION_APP_URL = os.getenv('FUNCTION_APP_URL')

# Debug settings
DEBUG = True

# Archivos estáticos
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Seguridad para entorno local
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-+p^1$!j%r!@$%^&*(devkeyhere')
ALLOWED_HOSTS = [
    'localhost', 
    '127.0.0.1',
    'testserver',  # Para tests de Django
    'veaconnect-webapp-prod-c7aaezbce3ftacdp.centralus-01.azurewebsites.net',
    '*.azurewebsites.net'  # Permitir todos los subdominios de Azure
]

# Configuración de caché (solo LocMemCache por defecto)
# Redis solo se usa internamente por el WhatsApp Bot para contexto conversacional
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}

# Sesiones en caché (opcional)
SESSION_ENGINE = "django.contrib.sessions.backends.cache"

# Configuración de Azure Blob Storage (solo si las variables están disponibles)
if all([AZURE_STORAGE_ACCOUNT_NAME, AZURE_STORAGE_ACCOUNT_KEY, AZURE_CONTAINER]):
    # Usar las variables correctas de Azure Storage
    pass
elif all([BLOB_ACCOUNT_NAME, BLOB_ACCOUNT_KEY, BLOB_CONTAINER_NAME]):
    # Fallback a variables BLOB_* si están disponibles
    pass
else:
    # Usar almacenamiento local si no hay configuración de Azure
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

# Deshabilitar Azure signals si no hay configuración completa
if not all([AZURE_STORAGE_ACCOUNT_NAME, AZURE_STORAGE_ACCOUNT_KEY, AZURE_CONTAINER]) and not all([BLOB_ACCOUNT_NAME, BLOB_ACCOUNT_KEY, BLOB_CONTAINER_NAME]):
    DISABLE_AZURE_SIGNALS = True
    print("Azure Blob Storage no configurado. Usando almacenamiento local.")
