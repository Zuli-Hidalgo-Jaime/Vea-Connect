"""
Health check function for Azure Functions v3
"""

import azure.functions as func
import logging
import json
import os
from datetime import datetime
from typing import Dict, Any

# Import utilities
import sys
sys.path.append('..')
from utils.responses import create_response

logger = logging.getLogger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Main health check endpoint for the function app."""
    try:
        # Basic function list
        functions_list = [
            "health",
            "embeddings/create",
            "embeddings/search", 
            "embeddings/health",
            "embeddings/stats",
            "whatsapp_event_grid_trigger"
        ]
        
        # Extended health checks
        health_checks = {
            "eventgrid_ready": _check_eventgrid_ready(),
            "acs_outbound_ready": _check_acs_outbound_ready(),
            "openai_configured": _check_openai_configured(),
            "ai_search_ready": _check_ai_search_ready(),
            "redis_connected": _check_redis_connected(),
            "build_version": _get_build_version()
        }
        
        # Overall status
        all_healthy = all(health_checks.values())
        status = "healthy" if all_healthy else "degraded"
        
        return create_response({
            "status": status,
            "message": "Azure Functions are running",
            "functions": functions_list,
            "health_checks": health_checks,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return create_response({"error": str(e)}, 500)


def _check_eventgrid_ready() -> bool:
    """Check if Event Grid is properly configured."""
    try:
        # Check if Event Grid webhook function exists
        function_path = os.path.join(os.path.dirname(__file__), '..', 'whatsapp_event_grid_trigger')
        if os.path.exists(function_path):
            return True
        return False
    except Exception:
        return False


def _check_acs_outbound_ready() -> bool:
    """Check if ACS outbound messaging is configured."""
    try:
        required_vars = [
            'ACS_WHATSAPP_ENDPOINT',
            'ACS_WHATSAPP_API_KEY',
            'ACS_PHONE_NUMBER',
            'WHATSAPP_CHANNEL_ID_GUID'
        ]
        
        for var in required_vars:
            if not os.environ.get(var):
                return False
        return True
    except Exception:
        return False


def _check_openai_configured() -> bool:
    """Check if Azure OpenAI is properly configured."""
    try:
        required_vars = [
            'AZURE_OPENAI_ENDPOINT',
            'AZURE_OPENAI_API_KEY',
            'AZURE_OPENAI_CHAT_DEPLOYMENT'
        ]
        
        for var in required_vars:
            if not os.environ.get(var):
                return False
        return True
    except Exception:
        return False


def _check_ai_search_ready() -> bool:
    """Check if Azure AI Search is configured."""
    try:
        required_vars = [
            'AZURE_SEARCH_ENDPOINT',
            'AZURE_SEARCH_API_KEY',
            'AZURE_SEARCH_INDEX_NAME'
        ]
        
        for var in required_vars:
            if not os.environ.get(var):
                return False
        return True
    except Exception:
        return False


def _check_redis_connected() -> bool:
    """Check if Redis connection is available."""
    try:
        # Check if Redis connection string is configured
        redis_conn = os.environ.get('AZURE_REDIS_CONNECTIONSTRING')
        if not redis_conn:
            return False
        
        # Try to import and test Redis service
        try:
            import sys
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            from services.redis_cache import WhatsAppCacheService
            
            cache_service = WhatsAppCacheService()
            # Simple test - try to store a test value
            test_key = "health_check_test"
            test_value = {"test": True, "timestamp": datetime.utcnow().isoformat()}
            
            success = cache_service.store_temporary_data("health", test_key, test_value, ttl=60)
            if success:
                # Clean up test data
                cache_service.get_temporary_data("health", test_key)
                return True
            return False
            
        except Exception as e:
            logger.warning(f"Redis connection test failed: {e}")
            return False
            
    except Exception:
        return False


def _get_build_version() -> str:
    """Get build version information."""
    try:
        # Try to get version from environment or use default
        version = os.environ.get('BUILD_VERSION', '1.0.0')
        
        # Add build timestamp if available
        build_date = os.environ.get('BUILD_DATE', datetime.utcnow().strftime('%Y-%m-%d'))
        
        return f"{version}-{build_date}"
    except Exception:
        return "1.0.0-unknown"
