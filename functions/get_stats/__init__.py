import json
import logging
import os
import azure.functions as func
from services.stats_service import collect_stats

logger = logging.getLogger(__name__)

def main(req: func.HttpRequest) -> func.HttpResponse:
    """Endpoint para obtener estadísticas del sistema."""
    logger.info("Función get_stats iniciada")
    
    try:
        logger.info("Recopilando estadísticas...")
        data = collect_stats()
        logger.info(f"Estadísticas recopiladas exitosamente: {len(data)} elementos")
        
        return func.HttpResponse(
            json.dumps(data, ensure_ascii=False),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logger.exception(f"Error en get_stats: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Error interno del servidor"}),
            mimetype="application/json",
            status_code=500
        )
