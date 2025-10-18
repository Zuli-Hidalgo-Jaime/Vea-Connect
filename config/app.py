#!/usr/bin/env python
"""
Flask API for Embedding operations.

This is an alternative to Azure Functions that provides the same HTTP endpoints
for embedding CRUD operations and semantic search.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Flask imports - these may not be available in all environments
# but the app will handle this gracefully
from flask import Flask, request, jsonify  # type: ignore
from flask_cors import CORS  # type: ignore

# Add the project directory to the path
import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utilities.embedding_manager import EmbeddingManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def create_response(status_code: int, message: str, data: Any = None, error: Optional[str] = None) -> tuple:
    """
    Create standardized HTTP response.
    
    Args:
        status_code: HTTP status code
        message: Response message
        data: Response data (optional)
        error: Error details (optional)
        
    Returns:
        tuple: Flask response tuple (json, status_code)
    """
    response_data = {
        "status": "success" if status_code < 400 else "error",
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if data is not None:
        response_data["data"] = data
    
    if error is not None:
        response_data["error"] = str(error) if error else ""
    
    return jsonify(response_data), status_code

def validate_required_fields(data: Dict[str, Any], required_fields: list) -> Optional[str]:
    """
    Validate required fields in request data.
    
    Args:
        data: Request data dictionary
        required_fields: List of required field names
        
    Returns:
        Optional[str]: Error message if validation fails, None if valid
    """
    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    if missing_fields:
        return f"Missing required fields: {', '.join(missing_fields)}"
    return None

@app.route('/api/embeddings/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        manager = EmbeddingManager()
        
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        status_code = 200
        return create_response(status_code, "Health check completed", health_data)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return create_response(503, "Health check failed", error=str(e))

@app.route('/api/embeddings/create', methods=['POST'])
def create_embedding():
    """Create a new embedding."""
    try:
        # Parse request body
        request_data = request.get_json()
        if not request_data:
            return create_response(400, "Invalid JSON in request body")
        
        # Validate required fields
        validation_error = validate_required_fields(request_data, ["document_id", "text"])
        if validation_error:
            return create_response(400, validation_error)
        
        # Get EmbeddingManager
        manager = EmbeddingManager()
        
        # Check if embedding already exists
        if manager.exists(request_data["document_id"]):
            return create_response(409, f"Embedding with ID '{request_data['document_id']}' already exists")
        
        # Create embedding
        success = manager.create_embedding(
            document_id=request_data["document_id"],
            text=request_data["text"],
            metadata=request_data.get("metadata", {})
        )
        
        if success:
            logger.info(f"Created embedding: {request_data['document_id']}")
            return create_response(201, "Embedding created successfully", {
                "document_id": request_data["document_id"],
                "created_at": datetime.utcnow().isoformat()
            })
        else:
            return create_response(500, "Failed to create embedding")
            
    except Exception as e:
        logger.error(f"Error creating embedding: {e}")
        return create_response(500, "Internal server error", error=str(e))

@app.route('/api/embeddings/get', methods=['GET'])
def get_embedding():
    """Retrieve an embedding by ID."""
    try:
        # Get document ID from query parameters
        document_id = request.args.get("id")
        if not document_id:
            return create_response(400, "Missing required parameter: id")
        
        # Get EmbeddingManager
        manager = EmbeddingManager()
        
        # Check if embedding exists
        if not manager.exists(document_id):
            return create_response(404, f"Embedding with ID '{document_id}' not found")
        
        # Get embedding
        embedding_data = manager.get_embedding(document_id)
        
        if embedding_data:
            # Remove embedding vector from response for security
            response_data = {
                "document_id": embedding_data["document_id"],
                "text": embedding_data["text"],
                "metadata": embedding_data["metadata"],
                "created_at": embedding_data.get("created_at"),
                "updated_at": embedding_data.get("updated_at")
            }
            
            logger.info(f"Retrieved embedding: {document_id}")
            return create_response(200, "Embedding retrieved successfully", response_data)
        else:
            return create_response(404, f"Embedding with ID '{document_id}' not found")
            
    except Exception as e:
        logger.error(f"Error retrieving embedding: {e}")
        return create_response(500, "Internal server error", error=str(e))

@app.route('/api/embeddings/update', methods=['PUT'])
def update_embedding():
    """Update an existing embedding."""
    try:
        # Parse request body
        request_data = request.get_json()
        if not request_data:
            return create_response(400, "Invalid JSON in request body")
        
        # Validate required fields
        validation_error = validate_required_fields(request_data, ["document_id", "text"])
        if validation_error:
            return create_response(400, validation_error)
        
        # Get EmbeddingManager
        manager = EmbeddingManager()
        
        # Check if embedding exists
        if not manager.exists(request_data["document_id"]):
            return create_response(404, f"Embedding with ID '{request_data['document_id']}' not found")
        
        # Update embedding
        success = manager.update_embedding(
            document_id=request_data["document_id"],
            new_text=request_data["text"],
            metadata=request_data.get("metadata", {})
        )
        
        if success:
            logger.info(f"Updated embedding: {request_data['document_id']}")
            return create_response(200, "Embedding updated successfully", {
                "document_id": request_data["document_id"],
                "updated_at": datetime.utcnow().isoformat()
            })
        else:
            return create_response(500, "Failed to update embedding")
            
    except Exception as e:
        logger.error(f"Error updating embedding: {e}")
        return create_response(500, "Internal server error", error=str(e))

@app.route('/api/embeddings/delete', methods=['DELETE'])
def delete_embedding():
    """Delete an embedding by ID."""
    try:
        # Get document ID from query parameters
        document_id = request.args.get("id")
        if not document_id:
            return create_response(400, "Missing required parameter: id")
        
        # Get EmbeddingManager
        manager = EmbeddingManager()
        
        # Check if embedding exists
        if not manager.exists(document_id):
            return create_response(404, f"Embedding with ID '{document_id}' not found")
        
        # Delete embedding
        success = manager.delete_embedding(document_id)
        
        if success:
            logger.info(f"Deleted embedding: {document_id}")
            return create_response(200, "Embedding deleted successfully", {
                "document_id": document_id,
                "deleted_at": datetime.utcnow().isoformat()
            })
        else:
            return create_response(500, "Failed to delete embedding")
            
    except Exception as e:
        logger.error(f"Error deleting embedding: {e}")
        return create_response(500, "Internal server error", error=str(e))

@app.route('/api/embeddings/search', methods=['POST'])
def search_similar():
    """Search for similar documents using semantic search."""
    try:
        # Parse request body
        request_data = request.get_json()
        if not request_data:
            return create_response(400, "Invalid JSON in request body")
        
        # Validate required fields
        validation_error = validate_required_fields(request_data, ["query"])
        if validation_error:
            return create_response(400, validation_error)
        
        # Get parameters
        query = request_data["query"]
        top_k = request_data.get("top_k", 3)
        
        # Validate top_k
        if not isinstance(top_k, int) or top_k < 1 or top_k > 50:
            return create_response(400, "top_k must be an integer between 1 and 50")
        
        # Get EmbeddingManager
        manager = EmbeddingManager()
        
        # Perform semantic search
        results = manager.find_similar(query, top_k=top_k)
        
        # Prepare response data
        response_data = {
            "query": query,
            "top_k": top_k,
            "results_count": len(results),
            "results": []
        }
        
        for result in results:
            # Remove embedding vector from response for security
            safe_result = {
                "document_id": result["document_id"],
                "text": result["text"],
                "metadata": result["metadata"],
                "similarity_score": result["similarity_score"],
                "created_at": result.get("created_at"),
                "updated_at": result.get("updated_at")
            }
            response_data["results"].append(safe_result)
        
        logger.info(f"Semantic search completed: '{query[:50]}{'...' if len(query) > 50 else ''}' - {len(results)} results")
        return create_response(200, "Semantic search completed successfully", response_data)
        
    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        return create_response(500, "Internal server error", error=str(e))

@app.route('/api/embeddings/stats', methods=['GET'])
def get_stats():
    """Get EmbeddingManager statistics."""
    try:
        # Get EmbeddingManager
        manager = EmbeddingManager()
        
        # Get statistics
        stats = manager.get_stats()
        
        logger.info("Retrieved embedding manager statistics")
        return create_response(200, "Statistics retrieved successfully", stats)
        
    except Exception as e:
        logger.error(f"Error retrieving statistics: {e}")
        return create_response(500, "Internal server error", error=str(e))

@app.route('/api/embeddings/<path:path>', methods=['OPTIONS'])
def handle_cors(path):
    """Handle CORS preflight requests."""
    response = jsonify({})
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

if __name__ == '__main__':
    print("🚀 Starting Flask Embedding API...")
    print("📡 API will be available at: http://localhost:5000")
    print("🔗 Health check: http://localhost:5000/api/embeddings/health")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True) 