"""
VEA Connect - Rutas de Búsqueda
Endpoints para funcionalidades de búsqueda
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from ..search.search_service import SearchService

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear router
router = APIRouter(prefix="/search", tags=["search"])

# Inicializar servicio de búsqueda
search_service = SearchService()

@router.get("/")
async def search_all(
    q: str = Query(..., description="Términos de búsqueda"),
    top: int = Query(20, description="Número máximo de resultados")
):
    """
    Buscar en todos los módulos
    
    Args:
        q: Términos de búsqueda
        top: Número máximo de resultados
        
    Returns:
        Resultados de búsqueda organizados por módulo
    """
    try:
        logger.info(f"Búsqueda general: '{q}'")
        results = search_service.search_all(q, top)
        return results
    except Exception as e:
        logger.error(f"Error en búsqueda general: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/module/{module}")
async def search_by_module(
    module: str,
    q: str = Query(..., description="Términos de búsqueda"),
    top: int = Query(20, description="Número máximo de resultados")
):
    """
    Buscar en un módulo específico
    
    Args:
        module: Nombre del módulo
        q: Términos de búsqueda
        top: Número máximo de resultados
        
    Returns:
        Resultados de búsqueda del módulo
    """
    try:
        logger.info(f"Búsqueda en módulo '{module}': '{q}'")
        results = search_service.search_by_module(module, q, top)
        return results
    except ValueError as e:
        logger.error(f"Módulo no encontrado: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error en búsqueda por módulo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents")
async def search_documents(
    q: str = Query(..., description="Términos de búsqueda"),
    document_type: Optional[str] = Query(None, description="Tipo de documento"),
    top: int = Query(20, description="Número máximo de resultados")
):
    """
    Buscar documentos específicos
    
    Args:
        q: Términos de búsqueda
        document_type: Tipo de documento (opcional)
        top: Número máximo de resultados
        
    Returns:
        Resultados de búsqueda de documentos
    """
    try:
        logger.info(f"Búsqueda de documentos: '{q}'")
        results = search_service.search_documents(q, document_type, top)
        return results
    except Exception as e:
        logger.error(f"Error en búsqueda de documentos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events")
async def search_events(
    q: str = Query(..., description="Términos de búsqueda"),
    top: int = Query(20, description="Número máximo de resultados")
):
    """
    Buscar eventos específicamente
    
    Args:
        q: Términos de búsqueda
        top: Número máximo de resultados
        
    Returns:
        Resultados de búsqueda de eventos
    """
    try:
        logger.info(f"Búsqueda de eventos: '{q}'")
        results = search_service.search_events(q, top)
        return results
    except Exception as e:
        logger.error(f"Error en búsqueda de eventos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/donations")
async def search_donations(
    q: str = Query(..., description="Términos de búsqueda"),
    top: int = Query(20, description="Número máximo de resultados")
):
    """
    Buscar donaciones específicamente
    
    Args:
        q: Términos de búsqueda
        top: Número máximo de resultados
        
    Returns:
        Resultados de búsqueda de donaciones
    """
    try:
        logger.info(f"Búsqueda de donaciones: '{q}'")
        results = search_service.search_donations(q, top)
        return results
    except Exception as e:
        logger.error(f"Error en búsqueda de donaciones: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/directory")
async def search_directory(
    q: str = Query(..., description="Términos de búsqueda"),
    top: int = Query(20, description="Número máximo de resultados")
):
    """
    Buscar en el directorio específicamente
    
    Args:
        q: Términos de búsqueda
        top: Número máximo de resultados
        
    Returns:
        Resultados de búsqueda del directorio
    """
    try:
        logger.info(f"Búsqueda en directorio: '{q}'")
        results = search_service.search_directory(q, top)
        return results
    except Exception as e:
        logger.error(f"Error en búsqueda del directorio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/document/{document_id}")
async def get_document_details(document_id: str):
    """
    Obtener detalles completos de un documento
    
    Args:
        document_id: ID del documento
        
    Returns:
        Detalles del documento
    """
    try:
        logger.info(f"Obteniendo detalles del documento: {document_id}")
        document = search_service.get_document_details(document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        return document
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener detalles del documento: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/facets")
async def get_facets(q: str = Query("*", description="Consulta de búsqueda")):
    """
    Obtener facetas disponibles
    
    Args:
        q: Consulta de búsqueda
        
    Returns:
        Facetas disponibles
    """
    try:
        logger.info(f"Obteniendo facetas para: '{q}'")
        facets = search_service.get_facets(q)
        return facets
    except Exception as e:
        logger.error(f"Error al obtener facetas: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/modules")
async def get_available_modules():
    """
    Obtener módulos disponibles
    
    Returns:
        Módulos disponibles
    """
    try:
        logger.info("Obteniendo módulos disponibles")
        modules = search_service.get_available_modules()
        return modules
    except Exception as e:
        logger.error(f"Error al obtener módulos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """
    Verificar salud del servicio de búsqueda
    
    Returns:
        Estado del servicio
    """
    try:
        logger.info("Verificando salud del servicio de búsqueda")
        health = search_service.health_check()
        return health
    except Exception as e:
        logger.error(f"Error en health check: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))




