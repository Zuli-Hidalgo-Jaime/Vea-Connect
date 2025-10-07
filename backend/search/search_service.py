"""
VEA Connect - Servicio de Búsqueda
Servicio de alto nivel para búsquedas en VEA Connect
"""

import logging
from typing import Dict, List, Optional, Any
from .azure_search_client import AzureSearchClient
from config import Config

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchService:
    """Servicio de búsqueda para VEA Connect"""
    
    def __init__(self):
        """Inicializar servicio de búsqueda"""
        self.search_client = AzureSearchClient()
        self.modules = Config.MODULES
        
        logger.info("Servicio de búsqueda inicializado")
    
    def search_all(self, query: str, top: int = 20) -> Dict[str, Any]:
        """
        Buscar en todos los módulos
        
        Args:
            query: Términos de búsqueda
            top: Número máximo de resultados
            
        Returns:
            Resultados de búsqueda organizados por módulo
        """
        try:
            logger.info(f"Búsqueda general: '{query}'")
            
            # Realizar búsqueda general
            results = self.search_client.search_simple(query, top)
            
            # Organizar resultados por módulo
            organized_results = {
                "query": query,
                "total_results": len(results),
                "modules": {}
            }
            
            # Agrupar por categoría
            for result in results:
                category = result.get("category", "general")
                if category not in organized_results["modules"]:
                    organized_results["modules"][category] = []
                organized_results["modules"][category].append(result)
            
            return organized_results
            
        except Exception as e:
            logger.error(f"Error en búsqueda general: {str(e)}")
            raise e
    
    def search_by_module(self, module: str, query: str, top: int = 20) -> Dict[str, Any]:
        """
        Buscar en un módulo específico
        
        Args:
            module: Nombre del módulo
            query: Términos de búsqueda
            top: Número máximo de resultados
            
        Returns:
            Resultados de búsqueda del módulo
        """
        try:
            logger.info(f"Búsqueda en módulo '{module}': '{query}'")
            
            # Verificar que el módulo existe
            if module not in self.modules:
                raise ValueError(f"Módulo '{module}' no encontrado")
            
            # Buscar por categoría del módulo
            results = self.search_client.search_by_category(module, query, top)
            
            return {
                "module": module,
                "query": query,
                "total_results": len(results),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error en búsqueda por módulo: {str(e)}")
            raise e
    
    def search_documents(self, query: str, document_type: Optional[str] = None, top: int = 20) -> Dict[str, Any]:
        """
        Buscar documentos específicos
        
        Args:
            query: Términos de búsqueda
            document_type: Tipo de documento (opcional)
            top: Número máximo de resultados
            
        Returns:
            Resultados de búsqueda de documentos
        """
        try:
            logger.info(f"Búsqueda de documentos: '{query}'")
            
            # Crear filtro por tipo de documento si se especifica
            filter_expression = None
            if document_type:
                filter_expression = f"document_type eq '{document_type}'"
            
            # Realizar búsqueda
            results = self.search_client.search_documents(
                query=query,
                filter_expression=filter_expression,
                top=top
            )
            
            # Convertir resultados
            documents = []
            for result in results:
                doc = {
                    "id": result.get("metadata_storage_path", ""),
                    "name": result.get("metadata_storage_name", ""),
                    "content": result.get("content", ""),
                    "merged_content": result.get("merged_content", ""),
                    "document_type": result.get("document_type", ""),
                    "category": result.get("category", ""),
                    "language": result.get("language", ""),
                    "keyphrases": result.get("keyphrases", []),
                    "locations": result.get("locations", []),
                    "score": result.get("@search.score", 0.0)
                }
                documents.append(doc)
            
            return {
                "query": query,
                "document_type": document_type,
                "total_results": len(documents),
                "documents": documents
            }
            
        except Exception as e:
            logger.error(f"Error en búsqueda de documentos: {str(e)}")
            raise e
    
    def search_events(self, query: str, top: int = 20) -> Dict[str, Any]:
        """
        Buscar eventos específicamente
        
        Args:
            query: Términos de búsqueda
            top: Número máximo de resultados
            
        Returns:
            Resultados de búsqueda de eventos
        """
        return self.search_by_module("eventos", query, top)
    
    def search_donations(self, query: str, top: int = 20) -> Dict[str, Any]:
        """
        Buscar donaciones específicamente
        
        Args:
            query: Términos de búsqueda
            top: Número máximo de resultados
            
        Returns:
            Resultados de búsqueda de donaciones
        """
        return self.search_by_module("donaciones", query, top)
    
    def search_directory(self, query: str, top: int = 20) -> Dict[str, Any]:
        """
        Buscar en el directorio específicamente
        
        Args:
            query: Términos de búsqueda
            top: Número máximo de resultados
            
        Returns:
            Resultados de búsqueda del directorio
        """
        return self.search_by_module("directorio", query, top)
    
    def get_document_details(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener detalles completos de un documento
        
        Args:
            document_id: ID del documento
            
        Returns:
            Detalles del documento o None
        """
        try:
            logger.info(f"Obteniendo detalles del documento: {document_id}")
            
            document = self.search_client.get_document_by_id(document_id)
            
            if document:
                # Agregar información adicional
                document["has_images"] = len(document.get("imageTags", [])) > 0
                document["has_ocr_text"] = len(document.get("text", [])) > 0
                document["has_locations"] = len(document.get("locations", [])) > 0
                document["has_keyphrases"] = len(document.get("keyphrases", [])) > 0
            
            return document
            
        except Exception as e:
            logger.error(f"Error al obtener detalles del documento: {str(e)}")
            raise e
    
    def get_facets(self, query: str = "*") -> Dict[str, Any]:
        """
        Obtener facetas disponibles
        
        Args:
            query: Consulta de búsqueda
            
        Returns:
            Facetas disponibles
        """
        try:
            logger.info(f"Obteniendo facetas para: '{query}'")
            
            facets = self.search_client.get_facets(query)
            
            return {
                "query": query,
                "facets": facets
            }
            
        except Exception as e:
            logger.error(f"Error al obtener facetas: {str(e)}")
            raise e
    
    def get_module_categories(self, module: str) -> List[str]:
        """
        Obtener subcategorías de un módulo
        
        Args:
            module: Nombre del módulo
            
        Returns:
            Lista de subcategorías
        """
        if module in self.modules:
            return self.modules[module]["subcategories"]
        return []
    
    def get_available_modules(self) -> Dict[str, Any]:
        """
        Obtener módulos disponibles
        
        Returns:
            Diccionario con módulos disponibles
        """
        return self.modules
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verificar salud del servicio
        
        Returns:
            Estado del servicio
        """
        try:
            search_healthy = self.search_client.health_check()
            
            return {
                "status": "healthy" if search_healthy else "unhealthy",
                "search_service": search_healthy,
                "modules_available": len(self.modules),
                "modules": list(self.modules.keys())
            }
            
        except Exception as e:
            logger.error(f"Error en health check: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }




