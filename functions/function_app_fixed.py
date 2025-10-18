"""
Azure Functions v4 - Main Application Entry Point (CORREGIDO)
"""
import azure.functions as func
import logging
import json
import os
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import utilities
from utils.responses import create_response
from django_integration import django_integration

# Register function triggers
app = func.FunctionApp()

@app.function_name(name="whatsapp_event_grid_trigger")
@app.event_grid_trigger(arg_name="event")
def whatsapp_event_grid_trigger(event: func.EventGridEvent):
    """Event Grid trigger for WhatsApp messages"""
    logger.info(f"Event Grid trigger recibido: {event.event_type}")
    
    try:
        # Import the function logic
        from whatsapp_event_grid_trigger import main as whatsapp_trigger
        return whatsapp_trigger(event)
    except Exception as e:
        logger.error(f"Error en whatsapp_event_grid_trigger: {e}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)

@app.function_name(name="health")
@app.route(route="health")
def health(request: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint"""
    logger.info("Health check endpoint llamado")
    
    try:
        # Import the function logic
        from health import main as health_check
        return health_check(request)
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)

@app.function_name(name="create_embedding")
@app.route(route="embeddings/create")
def create_embedding_http(request: func.HttpRequest) -> func.HttpResponse:
    """Create embedding endpoint"""
    logger.info("Create embedding endpoint llamado")
    
    try:
        # Import the function logic
        from create_embedding import main as create_embedding
        return create_embedding(request)
    except Exception as e:
        logger.error(f"Error en create_embedding: {e}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)

@app.function_name(name="search_similar")
@app.route(route="search")
def search_similar_http(request: func.HttpRequest) -> func.HttpResponse:
    """Search similar documents endpoint"""
    logger.info("Search similar endpoint llamado")
    
    try:
        # Import the function logic
        from search_similar import main as search_similar
        return search_similar(request)
    except Exception as e:
        logger.error(f"Error en search_similar: {e}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)

@app.function_name(name="get_stats")
@app.route(route="stats")
def get_stats_http(request: func.HttpRequest) -> func.HttpResponse:
    """Get statistics endpoint"""
    logger.info("Get stats endpoint llamado")
    
    try:
        # Import the function logic
        from get_stats import main as get_stats
        return get_stats(request)
    except Exception as e:
        logger.error(f"Error en get_stats: {e}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)

@app.function_name(name="embeddings_health_check")
@app.route(route="embeddings/health")
def embeddings_health_check_http(request: func.HttpRequest) -> func.HttpResponse:
    """Embeddings health check endpoint"""
    logger.info("Embeddings health check endpoint llamado")
    
    try:
        # Import the function logic
        from embeddings_health_check import main as embeddings_health_check
        return embeddings_health_check(request)
    except Exception as e:
        logger.error(f"Error en embeddings_health_check: {e}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)

# Función de inicialización para logging
@app.function_name(name="function_app_startup")
@app.route(route="startup")
def startup(request: func.HttpRequest) -> func.HttpResponse:
    """Startup function to verify all functions are loaded"""
    logger.info("=== AZURE FUNCTIONS STARTUP ===")
    logger.info(f"Python version: {os.sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info("Todas las funciones han sido registradas correctamente")
    
    return create_response({
        "status": "success",
        "message": "Azure Functions v4 iniciadas correctamente",
        "functions": [
            "whatsapp_event_grid_trigger",
            "health", 
            "create_embedding",
            "search_similar",
            "get_stats",
            "embeddings_health_check"
        ],
        "timestamp": datetime.utcnow().isoformat()
    })
