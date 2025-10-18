"""
Embeddings health check function for Azure Functions v3
"""

import azure.functions as func
import logging
import json
from datetime import datetime

# Import utilities
import sys
sys.path.append('..')
from utils.responses import create_response

logger = logging.getLogger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint for embedding functions."""
    try:
        return create_response({
            "message": "Embedding functions are healthy",
            "service": "embeddings",
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in embedding health check: {e}")
        return create_response({"error": str(e)}, 500)
