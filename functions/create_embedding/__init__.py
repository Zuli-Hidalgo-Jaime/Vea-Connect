"""
Create embedding function for Azure Functions v3
"""

import azure.functions as func
import logging
import json
import os
from openai import AzureOpenAI
from utils.responses import create_response

logger = logging.getLogger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Create a new embedding using Azure OpenAI."""
    logger.info("Función create_embedding iniciada")
    
    try:
        # Parse request body
        body = req.get_json()
        logger.info(f"Request body recibido: {json.dumps(body, ensure_ascii=False)}")
        
        # Validate required fields
        if "text" not in body:
            logger.error("Campo 'text' faltante")
            return create_response({"error": "Missing required field: text"}, 400)
        
        text = body["text"]
        metadata = body.get("metadata", {})
        
        logger.info(f"Creando embedding para texto de {len(text)} caracteres")
        
        # Create OpenAI client
        try:
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_version = os.getenv("AZURE_OPENAI_EMBEDDINGS_API_VERSION", "2023-05-15")
            
            if not api_key or not azure_endpoint:
                logger.error("Variables de entorno de OpenAI no configuradas")
                return create_response({"error": "OpenAI environment variables not configured"}, 500)
            
            openai_client = AzureOpenAI(
                api_key=api_key,
                azure_endpoint=azure_endpoint,
                api_version=api_version,
            )
        except Exception as e:
            logger.error(f"Error creando cliente OpenAI: {str(e)}")
            return create_response({"error": f"OpenAI client error: {str(e)}"}, 500)
        
        # Create embedding
        try:
            response = openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            
            embedding = response.data[0].embedding
            
            result = {
                "success": True,
                "embedding_length": len(embedding),
                "text_length": len(text),
                "model": "text-embedding-ada-002",
                "metadata": metadata
            }
            
            logger.info("Embedding creado exitosamente")
            return create_response({"message": "Embedding created successfully", "data": result}, 201)
            
        except Exception as e:
            logger.error(f"Error creando embedding: {str(e)}")
            return create_response({"error": f"Embedding creation error: {str(e)}"}, 500)
        
    except json.JSONDecodeError as e:
        logger.error(f"Error decodificando JSON: {str(e)}")
        return create_response({"error": "Invalid JSON in request body"}, 400)
    except Exception as e:
        logger.exception(f"Error inesperado: {str(e)}")
        return create_response({"error": str(e)}, 500)
