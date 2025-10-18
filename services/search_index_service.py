"""
Servicio de búsqueda para Azure AI Search
"""
import os
import logging
from typing import List, Dict, Any, Optional
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from django.conf import settings

logger = logging.getLogger(__name__)


class SearchIndexService:
    """Servicio para manejar operaciones con Azure AI Search"""
    
    def __init__(self):
        # Obtener configuración de Azure AI Search
        self.endpoint = getattr(settings, 'AZURE_SEARCH_ENDPOINT', None)
        self.api_key = getattr(settings, 'AZURE_SEARCH_API_KEY', None)
        self.index_name = getattr(settings, 'AZURE_SEARCH_INDEX_NAME', None)
        
        if not all([self.endpoint, self.api_key, self.index_name]):
            logger.warning("Azure AI Search configuration is missing")
            self.client = None
        else:
            try:
                self.client = SearchClient(
                    endpoint=self.endpoint,
                    index_name=self.index_name,
                    credential=AzureKeyCredential(self.api_key)
                )
                logger.info(f"Azure AI Search client initialized for index: {self.index_name}")
            except Exception as e:
                logger.error(f"Error initializing Azure AI Search client: {e}")
                self.client = None
    
    def upsert_document(self, document_id: str, content: str, metadata: Dict[str, Any]) -> bool:
        """
        Inserta o actualiza un documento en el índice de búsqueda
        
        Args:
            document_id: ID único del documento
            content: Contenido del documento
            metadata: Metadatos del documento
            
        Returns:
            bool: True si la operación fue exitosa
        """
        if not self.client:
            logger.warning("Azure AI Search client not available")
            return False
        
        try:
            # Preparar documento para indexación
            document = {
                'id': document_id,
                'content': content,
                **metadata
            }
            
            # Insertar o actualizar documento
            result = self.client.upload_documents([document])
            
            if result[0].succeeded:
                logger.info(f"Document indexed successfully: {document_id}")
                return True
            else:
                logger.error(f"Failed to index document {document_id}: {result[0].errors}")
                return False
                
        except Exception as e:
            logger.error(f"Error indexing document {document_id}: {e}")
            return False
    
    def delete_document(self, document_id: str) -> bool:
        """
        Elimina un documento del índice de búsqueda
        
        Args:
            document_id: ID del documento a eliminar
            
        Returns:
            bool: True si la operación fue exitosa
        """
        if not self.client:
            logger.warning("Azure AI Search client not available")
            return False
        
        try:
            result = self.client.delete_documents([{'id': document_id}])
            
            if result[0].succeeded:
                logger.info(f"Document deleted successfully: {document_id}")
                return True
            else:
                logger.error(f"Failed to delete document {document_id}: {result[0].errors}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            return False
    
    def search(self, query: str, top: int = 10) -> List[Dict[str, Any]]:
        """
        Busca documentos en el índice
        
        Args:
            query: Consulta de búsqueda
            top: Número máximo de resultados
            
        Returns:
            List[Dict]: Lista de documentos encontrados
        """
        if not self.client:
            logger.warning("Azure AI Search client not available")
            return []
        
        try:
            results = self.client.search(
                search_text=query,
                top=top
            )
            
            documents = []
            for result in results:
                documents.append(dict(result))
            
            logger.info(f"Search completed: {len(documents)} results for query: {query}")
            return documents
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def get_document_count(self) -> int:
        """
        Obtiene el número total de documentos en el índice
        
        Returns:
            int: Número de documentos
        """
        if not self.client:
            logger.warning("Azure AI Search client not available")
            return 0
        
        try:
            stats = self.client.get_document_count()
            logger.info(f"Document count: {stats}")
            return stats
        except Exception as e:
            logger.error(f"Error getting document count: {e}")
            return 0


# Instancia global del servicio
search_index_service = SearchIndexService()
