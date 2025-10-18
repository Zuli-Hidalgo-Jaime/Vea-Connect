"""
Constants for VEA Connect application.
"""

# Application constants
APP_NAME = "VEA Connect"
APP_VERSION = "1.0.0"

# Cache constants
CACHE_TIMEOUT = 3600  # 1 hour
CACHE_PREFIX = "vea_connect"

# WhatsApp constants
WHATSAPP_MESSAGE_MAX_LENGTH = 4096
WHATSAPP_RATE_LIMIT_PER_SECOND = 5

# Azure constants
AZURE_MAX_RETRIES = 3
AZURE_RETRY_DELAY = 1  # seconds

# API constants
API_RATE_LIMIT = 100  # requests per minute
API_TIMEOUT = 30  # seconds

# File upload constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_TYPES = [
    'image/jpeg',
    'image/png',
    'image/gif',
    'application/pdf',
    'text/plain',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
]

# Pagination constants
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Security constants
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128

# Time constants
DEFAULT_TIMEZONE = "America/Mexico_City"
