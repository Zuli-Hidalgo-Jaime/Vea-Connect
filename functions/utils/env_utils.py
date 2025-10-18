import os
import logging

def get_env(name: str) -> str:
    """
    Obtiene una variable de entorno y valida que exista
    
    Args:
        name: Nombre de la variable de entorno
        
    Returns:
        Valor de la variable de entorno
        
    Raises:
        EnvironmentError: Si la variable no está definida
    """
    value = os.getenv(name)
    if not value:
        logging.error("ENV-VAR %s is missing", name)
        raise EnvironmentError(f"{name} is required")
    return value
