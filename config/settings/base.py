from pathlib import Path
import os
import dj_database_url
import sys

# BASE_DIR apunta a la raíz del proyecto (vea-connect-website/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Configuración de SECRET_KEY
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    if os.getenv("DJANGO_ENV") == "production":
        raise ValueError("SECRET_KEY debe estar configurada en producción")
    else:
        SECRET_KEY = "django-insecure-dev-secret-key-change-in-production"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Feature Flags
CONFIG_ADAPTER_ENABLED = os.environ.get('CONFIG_ADAPTER_ENABLED', 'False') == 'True'
CACHE_LAYER_ENABLED = os.environ.get('CACHE_LAYER_ENABLED', 'False') == 'True'
CANARY_INGEST_ENABLED = os.environ.get('CANARY_INGEST_ENABLED', 'False') == 'True'

# Azure Function App Settings
FUNCTION_APP_URL = os.environ.get('FUNCTION_APP_URL') # ej: https://func-vea-connect-dev.azurewebsites.net/api/FunctionName
FUNCTION_APP_KEY = os.environ.get('FUNCTION_APP_KEY') # La clave 'default' de tus Host Keys



# Azure Storage Configuration (variables de entorno)
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

# Azure Computer Vision Configuration
VISION_ENDPOINT = os.environ.get('VISION_ENDPOINT')
VISION_KEY = os.environ.get('VISION_KEY')

# Azure AI Search Configuration
# Este cambio se realizó basado en un análisis de costos y mantenimiento. 
# Azure AI Search ofrece un menor costo operativo y mayor facilidad de gestión 
# para escenarios de búsqueda semántica.
AZURE_SEARCH_ENDPOINT = os.environ.get('AZURE_SEARCH_ENDPOINT')
AZURE_SEARCH_KEY = os.environ.get('AZURE_SEARCH_KEY')
AZURE_SEARCH_INDEX_NAME = os.environ.get('AZURE_SEARCH_INDEX_NAME', 'vea-connect-index')

# -------------------------
# Base de Datos
# -------------------------
# Configuración de base de datos según el entorno
if os.getenv('CI_ENVIRONMENT') == 'true':
    # Entorno de CI/CD - PostgreSQL local
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DBNAME', 'postgres'),
            'USER': os.environ.get('DBUSER', 'postgres'),
            'PASSWORD': os.environ.get('DBPASS', 'postgres'),
            'HOST': os.environ.get('DBHOST', 'localhost'),
            'PORT': os.environ.get('DBPORT', '5432'),
        }
    }
elif 'test' in sys.argv:
    # Modo de prueba - SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3_test',
        }
    }
else:
    # Desarrollo local y producción - usar dj_database_url
    database_url = os.getenv('DATABASE_URL')
    if database_url and database_url.startswith('sqlite'):
        # Si es SQLite, no usar parámetros de PostgreSQL
        DATABASES = {
            'default': dj_database_url.config(
                default=database_url,
                conn_max_age=600
            )
        }
    else:
        # Para PostgreSQL, incluir parámetros SSL
        DATABASES = {
            'default': dj_database_url.config(
                default=database_url,
                conn_max_age=600,
                ssl_require=True
            )
        }

# -------------------------
# Aplicaciones instaladas
# -------------------------
INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Terceros
    'widget_tweaks',
    'rest_framework',
    'drf_yasg',

    # Apps del proyecto
    'apps.core',
    'apps.dashboard',
    'apps.documents.apps.DocumentsConfig',
    'apps.events',
    'apps.directory',
    'apps.donations',
    'apps.user_settings',
    'apps.embeddings',
    'apps.vision',
    'apps.whatsapp_bot',  # WhatsApp Bot Handler
]

# -------------------------
# Middleware
# -------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Soporte para archivos estáticos en producción
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# -------------------------
# Enrutamiento principal
# -------------------------
ROOT_URLCONF = 'config.urls'

# -------------------------
# Configuración de templates
# -------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Plantillas globales
        'APP_DIRS': True,                  # Habilita templates por app
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# -------------------------
# WSGI
# -------------------------
WSGI_APPLICATION = 'config.wsgi.application'

# -------------------------
# Internacionalización
# -------------------------
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Lima'
USE_I18N = True
USE_TZ = True

# -------------------------
# Archivos estáticos
# -------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# -------------------------
# Archivos multimedia
# -------------------------
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# -------------------------
# Autenticación personalizada
# -------------------------
AUTH_USER_MODEL = 'core.CustomUser'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

# -------------------------
# Llave primaria por defecto
# -------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# -------------------------
# Django REST Framework
# -------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
}

# JWT Settings
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# WhatsApp Bot Configuration
ACS_CONNECTION_STRING = os.environ.get('ACS_CONNECTION_STRING', '')
ACS_EVENT_GRID_TOPIC_ENDPOINT = os.environ.get('ACS_EVENT_GRID_TOPIC_ENDPOINT', '')
ACS_EVENT_GRID_TOPIC_KEY = os.environ.get('ACS_EVENT_GRID_TOPIC_KEY', '')
ACS_PHONE_NUMBER = os.environ.get('ACS_PHONE_NUMBER', '')
ACS_WHATSAPP_API_KEY = os.environ.get('ACS_WHATSAPP_API_KEY', '')
ACS_WHATSAPP_ENDPOINT = os.environ.get('ACS_WHATSAPP_ENDPOINT', '')
WHATSAPP_ACCESS_TOKEN = os.environ.get('WHATSAPP_ACCESS_TOKEN', '')
WHATSAPP_CHANNEL_ID_GUID = os.environ.get('WHATSAPP_CHANNEL_ID_GUID', 'c3dd072b-9283-4812-8ed0-10b1d3a45da1')

# WhatsApp Bot Templates Configuration
WHATSAPP_TEMPLATES = {
    'vea_info_donativos': {
        'parameters': [
            'customer_name',
            'ministry_name',
            'bank_name',
            'beneficiary_name',
            'account_number',
            'clabe_number',
            'contact_name',
            'contact_phone'
        ],
        'category': 'donations'
    },
    'vea_contacto_ministerio': {
        'parameters': [
            'customer_name',
            'ministry_name',
            'contact_name',
            'contact_phone'
        ],
        'category': 'ministry'
    },
    'vea_event_info': {
        'parameters': [
            'customer_name',
            'event_name',
            'event_date',
            'event_location'
        ],
        'category': 'events'
    },
    'vea_request_received': {
        'parameters': [
            'customer_name',
            'request_summary'
        ],
        'category': 'general'
    }
}
