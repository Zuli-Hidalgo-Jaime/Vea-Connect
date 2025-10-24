import pytest
import json
from unittest.mock import patch, MagicMock
import azure.functions as func
from search_similar import main

class TestSearchSimilar:
    """Tests para la función search_similar"""
    
    @patch('search_similar.search')
    def test_search_similar_success(self, mock_search):
        """Test exitoso para POST /search"""
        # Arrange
        mock_search.return_value = [
            {"id": "1", "title": "Documento 1", "content": "Contenido 1"},
            {"id": "2", "title": "Documento 2", "content": "Contenido 2"}
        ]
        
        req = func.HttpRequest(
            method='POST',
            body=json.dumps({"query": "test query", "top": 5}).encode(),
            url='/api/search'
        )
        
        # Act
        response = main(req)
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.get_body())
        assert len(data) > 0
        assert len(data) == 2
        assert "id" in data[0]
        assert "title" in data[0]
    
    @patch('search_similar.search')
    def test_search_similar_missing_query(self, mock_search):
        """Test cuando falta el parámetro query"""
        # Arrange
        req = func.HttpRequest(
            method='POST',
            body=json.dumps({"top": 5}).encode(),
            url='/api/search'
        )
        
        # Act
        response = main(req)
        
        # Assert
        # Con la nueva estructura simplificada, esto debería fallar en el servicio
        # pero la función manejará la excepción y devolverá 500
        assert response.status_code == 500
    
    @patch('search_similar.search')
    def test_search_similar_missing_env_vars(self, mock_search):
        """Test cuando faltan variables de entorno"""
        # Arrange
        mock_search.side_effect = EnvironmentError("AZURE_SEARCH_ENDPOINT is required")
        
        req = func.HttpRequest(
            method='POST',
            body=json.dumps({"query": "test"}).encode(),
            url='/api/search'
        )
        
        # Act
        response = main(req)
        
        # Assert
        assert response.status_code == 500
    
    @patch('search_similar.search')
    def test_search_similar_exception(self, mock_search):
        """Test cuando ocurre una excepción"""
        # Arrange
        mock_search.side_effect = Exception("Test error")
        
        req = func.HttpRequest(
            method='POST',
            body=json.dumps({"query": "test query"}).encode(),
            url='/api/search'
        )
        
        # Act
        response = main(req)
        
        # Assert
        assert response.status_code == 500
