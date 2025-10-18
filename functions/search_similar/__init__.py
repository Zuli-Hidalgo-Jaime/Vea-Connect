import json
import logging
import os
import azure.functions as func
from services.search_index_service import search

logger = logging.getLogger(__name__)

def main(req: func.HttpRequest) -> func.HttpResponse:
    """Endpoint para búsqueda de documentos similares."""
    logger.info("Función search_similar iniciada")
    
    try:
        body = req.get_json()
        query = body.get("query")
        top = int(body.get("top", 10))
        
        if not query:
            logger.error("Campo 'query' requerido no encontrado")
            return func.HttpResponse(
                json.dumps({"error": "Campo 'query' es requerido"}),
                mimetype="application/json",
                status_code=400
            )
        
        logger.info(f"Buscando documentos similares para: '{query}' (top: {top})")
        result = search(query, top)
        logger.info(f"Búsqueda completada: {len(result)} resultados encontrados")
        
        return func.HttpResponse(
            json.dumps(result, ensure_ascii=False),
            mimetype="application/json",
            status_code=200
        )
    except ValueError as e:
        logger.error(f"Error de validación en search_similar: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Parámetro 'top' debe ser un número válido"}),
            mimetype="application/json",
            status_code=400
        )
    except Exception as e:
        logger.exception(f"Error en search_similar: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Error interno del servidor"}),
            mimetype="application/json",
            status_code=500
        )
