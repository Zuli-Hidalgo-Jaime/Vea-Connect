"""
Helper functions for VEA Connect application.
"""

import hashlib
import json
import logging
import re
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


def generate_cache_key(prefix: str, *args) -> str:
    """
    Generate a consistent cache key from prefix and arguments.
    
    Args:
        prefix: Key prefix
        *args: Arguments to include in the key
        
    Returns:
        Generated cache key
    """
    key_parts = [prefix] + [str(arg) for arg in args]
    key_string = ":".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def safe_json_loads(data: str, default: Any = None) -> Any:
    """
    Safely load JSON data with error handling.
    
    Args:
        data: JSON string to parse
        default: Default value if parsing fails
        
    Returns:
        Parsed JSON data or default value
    """
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse JSON: {e}")
        return default


def normalize_phone_number(phone: str) -> str:
    """
    Normalize phone number to international format.
    
    Args:
        phone: Phone number to normalize
        
    Returns:
        Normalized phone number
    """
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Handle Mexican numbers
    if len(digits) == 10 and digits.startswith('55'):
        return f"+52{digits}"
    elif len(digits) == 10:
        return f"+52{digits}"
    elif len(digits) == 12 and digits.startswith('52'):
        return f"+{digits}"
    elif len(digits) == 11 and digits.startswith('1'):
        return f"+{digits}"
    
    return f"+{digits}" if digits else phone


def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email to validate
        
    Returns:
        True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def get_cache_or_set(key: str, default_func, timeout: int = 3600) -> Any:
    """
    Get value from cache or set it using default function.
    
    Args:
        key: Cache key
        default_func: Function to call if key not found
        timeout: Cache timeout in seconds
        
    Returns:
        Cached value or result of default_func
    """
    value = cache.get(key)
    if value is None:
        try:
            value = default_func()
            cache.set(key, value, timeout)
        except Exception as e:
            logger.error(f"Error in cache default function: {e}")
            return None
    return value


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime to string.
    
    Args:
        dt: Datetime object
        format_str: Format string
        
    Returns:
        Formatted datetime string
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime(format_str)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple underscores
    filename = re.sub(r'_+', '_', filename)
    # Remove leading/trailing underscores
    filename = filename.strip('_')
    return filename


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks of specified size.
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def is_valid_uuid(uuid_string: str) -> bool:
    """
    Check if string is a valid UUID.
    
    Args:
        uuid_string: String to validate
        
    Returns:
        True if valid UUID, False otherwise
    """
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(pattern, uuid_string.lower()))


def get_setting_or_default(setting_name: str, default: Any = None) -> Any:
    """
    Get Django setting with fallback to default.
    
    Args:
        setting_name: Name of the setting
        default: Default value if setting not found
        
    Returns:
        Setting value or default
    """
    return getattr(settings, setting_name, default)
