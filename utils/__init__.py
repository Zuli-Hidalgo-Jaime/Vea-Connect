"""
Utils package for VEA Connect application.

This package contains utility functions and constants used throughout the application.
"""

from .constants import *
from .helpers import *

__version__ = "1.0.0"
__author__ = "VEA Connect Team"

# Export commonly used functions
__all__ = [
    # Constants
    'APP_NAME',
    'APP_VERSION',
    'CACHE_TIMEOUT',
    'CACHE_PREFIX',
    'WHATSAPP_MESSAGE_MAX_LENGTH',
    'AZURE_MAX_RETRIES',
    'API_RATE_LIMIT',
    'MAX_FILE_SIZE',
    'ALLOWED_FILE_TYPES',
    'DEFAULT_PAGE_SIZE',
    'MAX_PAGE_SIZE',
    'PASSWORD_MIN_LENGTH',
    'DEFAULT_TIMEZONE',
    
    # Helper functions
    'generate_cache_key',
    'safe_json_loads',
    'normalize_phone_number',
    'validate_email',
    'truncate_text',
    'get_cache_or_set',
    'format_datetime',
    'sanitize_filename',
    'chunk_list',
    'is_valid_uuid',
    'get_setting_or_default',
]
