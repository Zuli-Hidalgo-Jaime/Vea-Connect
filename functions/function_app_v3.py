"""
Azure Functions v3 - Main Application Entry Point (LEGACY MODEL)
Este archivo NO debe contener decoradores para el modelo v3
"""
import azure.functions as func
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Este archivo debe estar VACÍO para el modelo v3
# Las funciones se definen en sus respectivas carpetas con function.json
# y el archivo __init__.py de cada función

logger.info("Azure Functions v3 (Legacy Model) iniciado")
logger.info("Las funciones se cargan desde sus carpetas individuales")
