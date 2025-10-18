"""
Django Integration Module for Azure Functions

This module provides integration between Azure Functions and Azure Search directly
to avoid dependency on Django services.
"""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime

from utils.clients import get_openai_client, get_search_client

logger = logging.getLogger(__name__)

class AzureSearchIntegration:
    """
    Integration class for using Azure Search directly from Azure Functions.
    """
    
    def __init__(self):
        """
        Initialize Azure Search integration.
        """
        # Initialize clients using utilities
        self.openai_client = get_openai_client()
        self.search_client = get_search_client("documents")
    
    def create_embedding(self, text: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create embedding using Azure OpenAI and store in Azure Search.
        """
        try:
            if not self.openai_client:
                return {"success": False, "error": "OpenAI client not configured"}
            
            if not self.search_client:
                return {"success": False, "error": "Search client not configured"}
            
            # Create embedding
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            
            embedding = response.data[0].embedding
            
            # Prepare document for Azure Search (only existing fields)
            document = {
                "id": f"doc_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
                "content": text,
                "embedding": embedding,
                "created_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            }
            
            # Upload to Azure Search
            result = self.search_client.upload_documents([document])
            
            if result[0].succeeded:
                return {
                    "success": True,
                    "document_id": document["id"],
                    "embedding_length": len(embedding),
                    "message": "Embedding created and stored successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to store document: {result[0].errors}"
                }
                
        except Exception as e:
            logger.error(f"Error creating embedding: {e}")
            return {"success": False, "error": str(e)}
    
    def search_embeddings(self, query_text: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Search for similar embeddings using Azure Search.
        """
        try:
            if not self.openai_client:
                return {"success": False, "error": "OpenAI client not configured"}
            
            if not self.search_client:
                return {"success": False, "error": "Search client not configured"}
            
            # Create query embedding
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=query_text
            )
            
            query_embedding = response.data[0].embedding
            
            # Search in Azure Search
            search_results = self.search_client.search(
                search_text=query_text,
                top=top_k,
                include_total_count=True
            )
            
            results = []
            for result in search_results:
                results.append({
                    "id": result["id"],
                    "content": result["content"],
                    "score": result.get("@search.score", 0),
                    "created_at": result.get("created_at", "")
                })
            
            return {
                "success": True,
                "query": query_text,
                "total_count": search_results.get_count(),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error searching embeddings: {e}")
            return {"success": False, "error": str(e)}
    
    def process_whatsapp_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process WhatsApp event (placeholder for future implementation).
        """
        try:
            event_type = event.get("eventType", "unknown")
            logger.info(f"Processing WhatsApp event: {event_type}")
            
            # For now, just log the event
            return {
                "success": True,
                "event_type": event_type,
                "processed_at": datetime.utcnow().isoformat(),
                "message": "Event logged successfully"
            }
            
        except Exception as e:
            logger.error(f"Error processing WhatsApp event: {e}")
            return {"success": False, "error": str(e)}

# Create global instance
azure_search_integration = AzureSearchIntegration()

# Alias for backward compatibility
django_integration = azure_search_integration 