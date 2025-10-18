"""
Azure AI Search Client for VEA Connect WebApp.

This module provides a client for Azure AI Search operations.
The system supports semantic search and vector operations.
"""

import os
import logging
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

logger = logging.getLogger(__name__)


class AzureSearchClient:
    """
    Client for Azure AI Search operations.
    
    Provides methods for document management, vector search, and semantic search
    operations using Azure AI Search service.
    """
    
    def __init__(self, 
                 endpoint: Optional[str] = None,
                 key: Optional[str] = None,
                 index_name: Optional[str] = None):
        """
        Initialize Azure Search client.
        
        Args:
            endpoint: Azure Search service endpoint URL
            key: Azure Search service API key
            index_name: Name of the search index to use
        """
        self.endpoint = endpoint or os.getenv('AZURE_SEARCH_ENDPOINT')
        self.key = key or os.getenv('AZURE_SEARCH_KEY')
        self.index_name = index_name or os.getenv('AZURE_SEARCH_INDEX_NAME', 'vea-connect-index')
        if not self.endpoint or not isinstance(self.endpoint, str):
            raise ValueError("Azure Search endpoint must be a non-empty string")
        if not self.key or not isinstance(self.key, str):
            raise ValueError("Azure Search key must be a non-empty string")
        if not self.index_name or not isinstance(self.index_name, str):
            raise ValueError("Azure Search index_name must be a non-empty string")
        
        if not all([self.endpoint, self.key]):
            raise ValueError("Azure Search endpoint and key are required")
        
        if not self.key:
            raise ValueError("Azure Search key is required")
        
        from azure.core.credentials import AzureKeyCredential
        self.credential = AzureKeyCredential(self.key)
        from azure.search.documents import SearchClient
        self.search_client = SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_name,
            credential=self.credential
        )
        from azure.search.documents.indexes import SearchIndexClient
        self.index_client = SearchIndexClient(
            endpoint=self.endpoint,
            credential=self.credential
        )
        
        logger.info(f"Azure Search client initialized for index: {self.index_name}")
    
    def create_index_if_not_exists(self, vector_dimensions: int = 1536) -> bool:
        """
        Create the search index if it doesn't exist.
        
        Args:
            vector_dimensions: Number of dimensions for vector fields
            
        Returns:
            bool: True if index was created or already exists, False otherwise
        """
        try:
            # Check if index exists
            existing_indexes = [index.name for index in self.index_client.list_indexes()]
            if self.index_name in existing_indexes:
                logger.info(f"Index {self.index_name} already exists")
                return True
            
            # Create index definition
            from azure.search.documents.indexes.models import (
                SearchIndex, SimpleField, SearchableField, VectorSearch,
                SemanticConfiguration, SemanticField, SemanticPrioritizedFields
            )
            index = SearchIndex(
                name=self.index_name,
                fields=[
                    SimpleField(name="id", type="Edm.String", key=True),
                    SearchableField(name="document_id", type="Edm.String"),
                    SearchableField(name="text", type="Edm.String"),
                    SearchableField(name="title", type="Edm.String"),
                    SearchableField(name="content", type="Edm.String"),
                    SimpleField(name="embedding", type="Collection(Edm.Single)", 
                              vector_search_dimensions=vector_dimensions,
                              vector_search_profile="my-vector-config"),
                    SimpleField(name="metadata", type="Edm.String"),
                    SimpleField(name="created_at", type="Edm.DateTimeOffset"),
                    SimpleField(name="updated_at", type="Edm.DateTimeOffset"),
                    SimpleField(name="source_type", type="Edm.String"),
                    SimpleField(name="filename", type="Edm.String"),
                ],
                vector_search=VectorSearch(
                    profiles=[
                        # VectorSearchProfile(
                        #     name="my-vector-config",
                        #     algorithm_configuration_name="my-algorithms-config"
                        # )
                    ],
                    algorithms=[
                        # HnswVectorSearchAlgorithmConfiguration(
                        #     name="my-algorithms-config",
                        #     kind="hnsw",
                        #     parameters={
                        #         "m": 4,
                        #         "efConstruction": 400,
                        #         "efSearch": 500,
                        #         "metric": "cosine"
                        #     }
                        # )
                    ]
                )
            )
            
            # Create the index
            self.index_client.create_index(index)
            logger.info(f"Created search index: {self.index_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create search index: {e}")
            return False
    
    def upload_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Upload documents to Azure Search index.
        
        Args:
            documents: List of document dictionaries to upload
            
        Returns:
            bool: True if upload was successful, False otherwise
        """
        try:
            # Ensure index exists
            if not self.create_index_if_not_exists():
                return False
            
            # Prepare documents for upload
            search_documents = []
            for doc in documents:
                search_doc = {
                    "id": doc.get("id"),
                    "content": doc.get("content", ""),
                    "embedding": doc.get("embedding", []),
                    "created_at": doc.get("created_at", datetime.utcnow().isoformat()),
                }
                search_documents.append(search_doc)
            
            # Upload documents
            result = self.search_client.upload_documents(search_documents)
            
            # Check for errors
            failed_docs = [doc for doc in result if not doc.succeeded]
            if failed_docs:
                logger.error(f"Failed to upload {len(failed_docs)} documents")
                return False
            
            logger.info(f"Successfully uploaded {len(search_documents)} documents")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload documents: {e}")
            return False
    
    def search_vector(self, 
                     query_vector: List[float],
                     top_k: int = 10,
                     filter_query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Perform vector search using Azure Search.
        
        Args:
            query_vector: Vector representation of the query
            top_k: Number of results to return
            filter_query: Optional filter query string
            
        Returns:
            List[Dict[str, Any]]: Search results with similarity scores
        """
        try:
            # Build search options
            search_options = {
                "vector_queries": [{
                    "vector": query_vector,
                    "fields": "embedding",
                    "k": top_k,
                    "kind": "vector"
                }],
                "select": ["id", "content", "embedding", "created_at"],
                "top": top_k
            }
            
            if filter_query:
                search_options["filter"] = filter_query
            
            # Perform search
            results = self.search_client.search(search_text="", **search_options)
            
            # Process results
            search_results = []
            for result in results:
                search_result = {
                    "id": result.get("id"),
                    "document_id": result.get("document_id"),
                    "text": result.get("text"),
                    "title": result.get("title"),
                    "content": result.get("content"),
                    "metadata": json.loads(result.get("metadata", "{}")),
                    "created_at": result.get("created_at"),
                    "source_type": result.get("source_type"),
                    "filename": result.get("filename"),
                    "score": result.get("@search.score", 0.0)
                }
                search_results.append(search_result)
            
            logger.info(f"Vector search returned {len(search_results)} results")
            return search_results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    def has_semantic_config(self):
        # Devuelve True si el índice tiene sección semantic configurada
        try:
            index = self.index_client.get_index(self.index_name)
            return hasattr(index, 'semantic_settings') and index.semantic_settings and getattr(index.semantic_settings, 'configurations', None)
        except Exception as e:
            logger.warning(f"No se pudo verificar configuración semántica: {e}")
            return False

    def search_semantic(self, query_text: str, top_k: int = 10, filter_query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Perform semantic search using Azure Search.
        """
        try:
            # Build search options
            search_options = {
                "search_text": query_text,
                "select": ["id", "content", "embedding", "created_at"],
                "top": top_k,
                "query_type": "semantic"
            }
            # Solo pasar semantic_configuration_name si el índice lo soporta
            semantic_config = os.getenv('AZURE_SEARCH_SEMANTIC_CONFIG', 'default')
            if self.has_semantic_config() and semantic_config:
                search_options["semantic_configuration_name"] = semantic_config
            if filter_query:
                search_options["filter"] = filter_query
            results = self.search_client.search(**search_options)
            search_results = []
            for result in results:
                search_result = {
                    "id": result.get("id"),
                    "content": result.get("content"),
                    "embedding": result.get("embedding"),
                    "created_at": result.get("created_at"),
                    "score": result.get("@search.score", 0.0),
                    "reranker_score": result.get("@search.reranker_score", 0.0)
                }
                search_results.append(search_result)
            logger.info(f"Semantic search returned {len(search_results)} results")
            return search_results
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the search index.
        
        Args:
            document_id: ID of the document to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            result = self.search_client.delete_document(document_id)
            
            if result[0].succeeded:
                logger.info(f"Successfully deleted document: {document_id}")
                return True
            else:
                logger.error(f"Failed to delete document: {document_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            return False
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document from the search index.
        
        Args:
            document_id: ID of the document to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Document data or None if not found
        """
        try:
            result = self.search_client.get_document(key=document_id)
            
            if result:
                document = {
                    "id": result.get("id"),
                    "title": result.get("title"),
                    "content": result.get("content"),
                    "embedding": result.get("embedding", []),
                    "metadata": json.loads(result.get("metadata", "{}")),
                    "created_at": result.get("created_at"),
                    "updated_at": result.get("updated_at"),
                    "source_type": result.get("source_type"),
                    "filename": result.get("filename")
                }
                logger.info(f"Retrieved document: {document_id}")
                return document
            else:
                logger.warning(f"Document not found: {document_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving document {document_id}: {e}")
            return None
    
    def update_document(self, document: Dict[str, Any]) -> bool:
        """
        Update a document in the search index.
        
        Args:
            document: Document data to update
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            # Prepare document for update
            search_doc = {
                "id": document.get("id"),
                "title": document.get("title", ""),
                "content": document.get("content", ""),
                "embedding": document.get("embedding", []),
                "metadata": json.dumps(document.get("metadata", {})),
                "created_at": document.get("created_at", datetime.utcnow().isoformat()),
                "updated_at": datetime.utcnow().isoformat(),
                "source_type": document.get("source_type", "document"),
                "filename": document.get("filename", "")
            }
            
            result = self.search_client.merge_documents([search_doc])
            
            if result[0].succeeded:
                logger.info(f"Successfully updated document: {document.get('id')}")
                return True
            else:
                logger.error(f"Failed to update document: {document.get('id')}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the search index.
        
        Returns:
            Dict[str, Any]: Index statistics
        """
        try:
            stats = self.search_client.get_document_count()
            return {
                "document_count": stats,
                "index_name": self.index_name,
                "endpoint": self.endpoint
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {"error": str(e)}


def get_azure_search_client() -> 'AzureSearchClient':
    """
    Get a configured Azure Search client instance.
    Returns:
        AzureSearchClient: Configured client instance
    Raises:
        ValueError: If Azure Search is not properly configured or SDK is missing
    """
    try:
        from azure.core.credentials import AzureKeyCredential
        from azure.search.documents import SearchClient
        from azure.search.documents.indexes import SearchIndexClient
        from azure.search.documents.indexes.models import (
            SearchIndex, SimpleField, SearchableField, VectorSearch,
            SemanticConfiguration, SemanticField
        )
    except ImportError as e:
        raise ValueError(f"Azure Search SDK not available. Install with: pip install azure-search-documents. Error: {e}")
    return AzureSearchClient() 