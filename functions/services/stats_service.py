import os
import logging
from typing import Dict, Any
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from utils.env_utils import get_env

# Variables de entorno obligatorias
ENDPOINT = get_env("AZURE_SEARCH_ENDPOINT")
INDEX = get_env("AZURE_SEARCH_INDEX_NAME")
KEY = get_env("AZURE_SEARCH_KEY")

client = SearchClient(ENDPOINT, INDEX, AzureKeyCredential(KEY))

def collect_stats() -> Dict[str, Any]:
    """
    Recolecta estadísticas del sistema
    
    Returns:
        Diccionario con estadísticas del sistema
    """
    try:
        # Obtener estadísticas básicas del índice
        stats = {
            "total_documents": 0,
            "index_name": INDEX,
            "search_endpoint": ENDPOINT,
            "status": "healthy"
        }
        
        # Contar documentos en el índice
        try:
            result = client.get_document_count()
            stats["total_documents"] = result
        except Exception as e:
            logging.warning(f"No se pudo obtener el conteo de documentos: {str(e)}")
            stats["total_documents"] = -1
            
        return stats
        
    except Exception as e:
        logging.error(f"Error recolectando estadísticas: {str(e)}")
        return {
            "error": str(e),
            "status": "error"
        }
