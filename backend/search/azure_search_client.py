"""
VEA Connect - Cliente de Azure AI Search
Cliente para interactuar con Azure AI Search usando Python
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
# SearchResult se obtiene directamente del resultado de búsqueda
from config import Config

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AzureSearchClient:
    """Cliente para interactuar con Azure AI Search"""
    
    def __init__(self):
        """Inicializar cliente de Azure AI Search"""
        self.search_service_name = Config.SEARCH_SERVICE_NAME
        self.search_api_key = Config.SEARCH_SERVICE_KEY
        self.search_endpoint = Config.SEARCH_SERVICE_ENDPOINT
        self.search_index_name = Config.SEARCH_INDEX_NAME
        
        if not all([self.search_service_name, self.search_api_key, self.search_endpoint, self.search_index_name]):
            raise ValueError("Configuración de Azure AI Search incompleta. Verifica las variables de entorno.")
        
        # Crear credenciales
        self.credential = AzureKeyCredential(self.search_api_key)
        
        # Crear clientes
        self.search_client = SearchClient(
            endpoint=self.search_endpoint,
            index_name=self.search_index_name,
            credential=self.credential
        )
        
        self.index_client = SearchIndexClient(
            endpoint=self.search_endpoint,
            credential=self.credential
        )
        
        logger.info(f"Cliente de Azure AI Search inicializado para índice: {self.search_index_name}")
    
    def search_documents(
        self, 
        query: str, 
        search_mode: str = "all",
        include_total_count: bool = True,
        filter_expression: Optional[str] = None,
        order_by: Optional[str] = None,
        facets: Optional[List[str]] = None,
        highlight_fields: Optional[str] = None,
        select_fields: Optional[List[str]] = None,
        top: int = 50
    ) -> List[SearchResult]:
        """
        Buscar documentos en el índice
        
        Args:
            query: Términos de búsqueda
            search_mode: Modo de búsqueda ("all" o "any")
            include_total_count: Incluir conteo total de resultados
            filter_expression: Expresión de filtro OData
            order_by: Campo para ordenar resultados
            facets: Campos para facetas
            highlight_fields: Campos para resaltar
            select_fields: Campos a seleccionar
            top: Número máximo de resultados
            
        Returns:
            Lista de resultados de búsqueda
        """
        try:
            # Configurar opciones de búsqueda como diccionario
            search_options = {
                "search_mode": search_mode,
                "include_total_count": include_total_count,
                "filter": filter_expression,
                "order_by": order_by,
                "facets": facets,
                "highlight_fields": highlight_fields,
                "select": select_fields,
                "top": top
            }
            
            # Realizar búsqueda
            results = self.search_client.search(query, search_options=search_options)
            
            logger.info(f"Búsqueda realizada: '{query}' - {len(list(results))} resultados")
            return list(results)
            
        except Exception as e:
            logger.error(f"Error en búsqueda: {str(e)}")
            raise e
    
    def search_simple(self, query: str, top: int = 10) -> List[Dict[str, Any]]:
        """
        Búsqueda simple con campos básicos
        
        Args:
            query: Términos de búsqueda
            top: Número máximo de resultados
            
        Returns:
            Lista de documentos encontrados
        """
        try:
            # Campos básicos para búsqueda simple
            select_fields = [
                "metadata_storage_name",
                "metadata_storage_path",
                "content",
                "merged_content",
                "language",
                "keyphrases",
                "locations",
                "document_type",
                "category"
            ]
            
            results = self.search_documents(
                query=query,
                select_fields=select_fields,
                top=top
            )
            
            # Convertir resultados a diccionarios
            documents = []
            for result in results:
                doc = {
                    "id": result.get("metadata_storage_path", ""),
                    "name": result.get("metadata_storage_name", ""),
                    "content": result.get("content", ""),
                    "merged_content": result.get("merged_content", ""),
                    "language": result.get("language", ""),
                    "keyphrases": result.get("keyphrases", []),
                    "locations": result.get("locations", []),
                    "document_type": result.get("document_type", ""),
                    "category": result.get("category", ""),
                    "score": result.get("@search.score", 0.0)
                }
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error en búsqueda simple: {str(e)}")
            raise e
    
    def search_by_category(self, category: str, query: str = "", top: int = 20) -> List[Dict[str, Any]]:
        """
        Buscar documentos por categoría
        
        Args:
            category: Categoría del documento
            query: Términos de búsqueda adicionales
            top: Número máximo de resultados
            
        Returns:
            Lista de documentos de la categoría
        """
        try:
            # Crear filtro por categoría
            filter_expression = f"category eq '{category}'"
            
            # Si hay query adicional, combinar con filtro
            if query:
                search_query = f"{query} AND category:{category}"
            else:
                search_query = f"category:{category}"
            
            results = self.search_documents(
                query=search_query,
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
                    "category": result.get("category", ""),
                    "document_type": result.get("document_type", ""),
                    "score": result.get("@search.score", 0.0)
                }
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error en búsqueda por categoría: {str(e)}")
            raise e
    
    def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener un documento específico por ID
        
        Args:
            document_id: ID del documento
            
        Returns:
            Documento encontrado o None
        """
        try:
            # Buscar documento por ID
            results = self.search_documents(
                query=f"metadata_storage_path eq '{document_id}'",
                top=1
            )
            
            if results:
                result = results[0]
                return {
                    "id": result.get("metadata_storage_path", ""),
                    "name": result.get("metadata_storage_name", ""),
                    "content": result.get("content", ""),
                    "merged_content": result.get("merged_content", ""),
                    "language": result.get("language", ""),
                    "keyphrases": result.get("keyphrases", []),
                    "locations": result.get("locations", []),
                    "document_type": result.get("document_type", ""),
                    "category": result.get("category", ""),
                    "imageTags": result.get("imageTags", []),
                    "imageCaption": result.get("imageCaption", []),
                    "text": result.get("text", []),
                    "layoutText": result.get("layoutText", [])
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error al obtener documento por ID: {str(e)}")
            raise e
    
    def get_facets(self, query: str = "*", facet_fields: List[str] = None) -> Dict[str, Any]:
        """
        Obtener facetas para una consulta
        
        Args:
            query: Consulta de búsqueda
            facet_fields: Campos para facetas
            
        Returns:
            Diccionario con facetas
        """
        try:
            if facet_fields is None:
                facet_fields = ["category", "document_type", "language"]
            
            results = self.search_documents(
                query=query,
                facets=facet_fields,
                top=0  # Solo facetas, no documentos
            )
            
            # Extraer facetas de los resultados
            facets = {}
            for result in results:
                if hasattr(result, 'get_facets'):
                    facets = result.get_facets()
                    break
            
            return facets
            
        except Exception as e:
            logger.error(f"Error al obtener facetas: {str(e)}")
            raise e
    
    def health_check(self) -> bool:
        """
        Verificar salud del servicio de búsqueda
        
        Returns:
            True si el servicio está funcionando
        """
        try:
            # Realizar una búsqueda simple para verificar conectividad
            results = self.search_documents(query="*", top=1)
            logger.info("Health check exitoso")
            return True
            
        except Exception as e:
            logger.error(f"Health check falló: {str(e)}")
            return False



