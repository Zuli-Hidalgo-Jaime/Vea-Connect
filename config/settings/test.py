import os

# Cargar variables de entorno desde el archivo .env (solo en desarrollo local)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("python-dotenv no está instalado, continuando sin .env")

# Configuración de debug sanitizada - no exponer secretos
print('DEBUG AZURE_SEARCH_ENDPOINT:', 'SET' if os.getenv('AZURE_SEARCH_ENDPOINT') else 'NOT SET')
print('DEBUG AZURE_SEARCH_KEY:', 'SET' if os.getenv('AZURE_SEARCH_KEY') else 'NOT SET')
print('DEBUG AZURE_SEARCH_INDEX_NAME:', 'SET' if os.getenv('AZURE_SEARCH_INDEX_NAME') else 'NOT SET')
print('DEBUG AZURE_OPENAI_ENDPOINT:', 'SET' if os.getenv('AZURE_OPENAI_ENDPOINT') else 'NOT SET')
print('DEBUG OPENAI_API_KEY:', 'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET')

from .base import *

# Configuración específica para pruebas
DEBUG = False

# Configuración de base de datos para pruebas
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3_test',
        'OPTIONS': {
            'timeout': 20,
        }
    }
}

# Configuración de caché para pruebas
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}

# Configuración de sesiones para pruebas
SESSION_ENGINE = "django.contrib.sessions.backends.db"

# Configuración de archivos estáticos para pruebas
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles_test'

# Configuración de archivos multimedia para pruebas
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media_test'

# Configuración de seguridad para pruebas
SECRET_KEY = 'test-secret-key-for-testing-only'
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

# Configuración de logging para pruebas
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

# Configuración de archivos para pruebas
FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]

# Configuración de correo para pruebas
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Configuración de timezone para pruebas
USE_TZ = False
TIME_ZONE = 'UTC'

# Configuración de Azure Blob Storage para pruebas (deshabilitado)
AZURE_STORAGE_ACCOUNT_NAME = None
AZURE_STORAGE_ACCOUNT_KEY = None
AZURE_ACCOUNT_NAME = None
AZURE_ACCOUNT_KEY = None
AZURE_CONTAINER = None
AZURE_STORAGE_CONNECTION_STRING = None

# Variables de compatibilidad (fallback)
BLOB_ACCOUNT_NAME = None
BLOB_ACCOUNT_KEY = None
BLOB_CONTAINER_NAME = None

# Configuración para deshabilitar signals de Azure durante pruebas
DISABLE_AZURE_SIGNALS = True 