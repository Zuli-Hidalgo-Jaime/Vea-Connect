#!/usr/bin/env python3
"""
Utilitarios para saneamiento de logs y protección de PII
"""

import re
import logging
from typing import Any, Optional, Union
from urllib.parse import urlparse, parse_qs

# Patrones para detectar valores sensibles
SENSITIVE_PATTERNS = [
    # API Keys y tokens
    r'^sk-[a-zA-Z0-9]{20,}$',  # OpenAI API keys
    r'^pk_[a-zA-Z0-9]{20,}$',  # Stripe public keys
    r'^sk_[a-zA-Z0-9]{20,}$',  # Stripe secret keys
    
    # Azure keys (Base64 encoded)
    r'^[a-zA-Z0-9+/]{20,}={0,2}$',
    
    # Connection strings
    r'DefaultEndpointsProtocol=https;AccountName=[^;]+;AccountKey=[^;]+',
    r'endpoint=https://[^;]+;accesskey=[^;]+',
    
    # URLs con tokens
    r'https?://[^\s]+[?&](token|key|secret|password)=[^\s&]+',
    
    # Emails
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    
    # Números de teléfono
    r'^\+?[1-9]\d{1,14}$',
    
    # IPs privadas
    r'^(?:10|127|172\.(?:1[6-9]|2[0-9]|3[01])|192\.168)\.\d{1,3}\.\d{1,3}$',
]

# Palabras clave que indican contenido sensible
SENSITIVE_KEYWORDS = [
    'password', 'secret', 'key', 'token', 'credential', 'auth',
    'api_key', 'access_key', 'private_key', 'secret_key',
    'connection_string', 'connectionstring', 'connstr',
    'authorization', 'bearer', 'basic',
    'ssn', 'social_security', 'credit_card', 'card_number',
    'phone', 'telephone', 'mobile', 'celular',
    'email', 'mail', 'correo',
    'address', 'direccion', 'domicilio',
    'name', 'nombre', 'apellido', 'lastname',
    'dni', 'cedula', 'identification',
]

def safe_value(value: Any) -> str:
    """
    Sanitiza un valor para logging, redactando información sensible.
    
    Args:
        value: El valor a sanitizar
        
    Returns:
        String sanitizado o '[REDACTED]' si contiene información sensible
    """
    if value is None:
        return 'None'
    
    # Convertir a string
    str_value = str(value).strip()
    
    # Si está vacío, devolver tal como está
    if not str_value:
        return str_value
    
    # Verificar si contiene palabras clave sensibles
    lower_value = str_value.lower()
    for keyword in SENSITIVE_KEYWORDS:
        if keyword in lower_value:
            return '[REDACTED]'
    
    # Verificar patrones sensibles
    for pattern in SENSITIVE_PATTERNS:
        if re.match(pattern, str_value, re.IGNORECASE):
            return '[REDACTED]'
    
    # Verificar URLs con parámetros sensibles
    if str_value.startswith(('http://', 'https://')):
        try:
            parsed = urlparse(str_value)
            query_params = parse_qs(parsed.query)
            sensitive_params = ['token', 'key', 'secret', 'password', 'auth']
            for param in sensitive_params:
                if param in query_params:
                    return '[REDACTED_URL]'
        except Exception:
            pass
    
    # Si es muy largo, podría ser un token
    if len(str_value) > 50:
        # Verificar si parece ser un token (muchos caracteres alfanuméricos)
        if re.match(r'^[a-zA-Z0-9+/=_-]{30,}$', str_value):
            return '[REDACTED]'
    
    # Verificar API keys específicas
    if str_value.startswith('sk-') and len(str_value) > 20:
        return '[REDACTED]'
    
    # Verificar tokens largos que parecen ser API keys
    if len(str_value) > 30 and re.match(r'^[a-zA-Z0-9_-]+$', str_value):
        return '[REDACTED]'
    
    return str_value

def safe_dict(data: dict, max_depth: int = 3) -> dict:
    """
    Sanitiza un diccionario recursivamente.
    
    Args:
        data: Diccionario a sanitizar
        max_depth: Profundidad máxima de recursión
        
    Returns:
        Diccionario sanitizado
    """
    if max_depth <= 0:
        return {'[MAX_DEPTH]': '...'}
    
    sanitized = {}
    for key, value in data.items():
        # No sanitizar claves comunes
        safe_key = key if key in ['user_id', 'status', 'host', 'user', 'port', 'name', 'version', 'debug', 'normal_field'] else safe_value(key)
        
        # Sanitizar el valor
        if isinstance(value, dict):
            safe_value_dict = safe_dict(value, max_depth - 1)
            sanitized[safe_key] = safe_value_dict
        elif isinstance(value, list):
            safe_value_list = []
            for item in value:
                if isinstance(item, dict):
                    safe_value_list.append(safe_dict(item, max_depth - 1))
                elif isinstance(item, list):
                    safe_value_list.append(item)  # No procesar listas anidadas por simplicidad
                else:
                    safe_value_list.append(safe_value(item))
            sanitized[safe_key] = safe_value_list
        else:
            safe_value_dict = safe_value(value)
            sanitized[safe_key] = safe_value_dict
    
    return sanitized

class SafeLogger:
    """
    Logger wrapper que sanitiza automáticamente los valores sensibles.
    """
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def _sanitize_args(self, args):
        """Sanitiza los argumentos de logging"""
        sanitized_args = []
        for arg in args:
            if isinstance(arg, dict):
                sanitized_args.append(safe_dict(arg))
            elif isinstance(arg, (int, float, bool)):
                # No sanitizar números y booleanos
                sanitized_args.append(arg)
            else:
                sanitized_args.append(safe_value(arg))
        return sanitized_args
    
    def debug(self, msg, *args, **kwargs):
        sanitized_args = self._sanitize_args(args)
        self.logger.debug(msg, *sanitized_args, **kwargs)
    
    def info(self, msg, *args, **kwargs):
        sanitized_args = self._sanitize_args(args)
        self.logger.info(msg, *sanitized_args, **kwargs)
    
    def warning(self, msg, *args, **kwargs):
        sanitized_args = self._sanitize_args(args)
        self.logger.warning(msg, *sanitized_args, **kwargs)
    
    def error(self, msg, *args, **kwargs):
        sanitized_args = self._sanitize_args(args)
        self.logger.error(msg, *sanitized_args, **kwargs)
    
    def critical(self, msg, *args, **kwargs):
        sanitized_args = self._sanitize_args(args)
        self.logger.critical(msg, *sanitized_args, **kwargs)
    
    def exception(self, msg, *args, **kwargs):
        sanitized_args = self._sanitize_args(args)
        self.logger.exception(msg, *sanitized_args, **kwargs)

def get_safe_logger(name: str) -> SafeLogger:
    """
    Obtiene un logger seguro para el nombre especificado.
    
    Args:
        name: Nombre del logger
        
    Returns:
        SafeLogger instance
    """
    return SafeLogger(logging.getLogger(name))

# Función de conveniencia para uso directo
def safe_log_value(value: Any) -> str:
    """
    Alias para safe_value para compatibilidad con código existente.
    """
    return safe_value(value)
