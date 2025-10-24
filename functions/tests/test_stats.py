import pytest
import json
from unittest.mock import patch, MagicMock
import azure.functions as func
from get_stats import main

class TestGetStats:
    """Tests para la función get_stats"""
    
    @patch('get_stats.collect_stats')
    def test_get_stats_success(self, mock_collect_stats):
        """Test exitoso para GET /stats"""
        # Arrange
        mock_collect_stats.return_value = {
            "total_documents": 100,
            "index_name": "test-index",
            "search_endpoint": "https://test.search.windows.net",
            "status": "healthy"
        }
        
        req = func.HttpRequest(
            method='GET',
            body=b'',
            url='/api/stats'
        )
        
        # Act
        response = main(req)
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.get_body())
        assert "total_documents" in data
        assert "index_name" in data
        assert "search_endpoint" in data
        assert "status" in data
        assert data["status"] == "healthy"
    
    @patch('get_stats.collect_stats')
    def test_get_stats_missing_env_vars(self, mock_collect_stats):
        """Test cuando faltan variables de entorno"""
        # Arrange
        mock_collect_stats.side_effect = EnvironmentError("AZURE_SEARCH_ENDPOINT is required")
        
        req = func.HttpRequest(
            method='GET',
            body=b'',
            url='/api/stats'
        )
        
        # Act
        response = main(req)
        
        # Assert
        assert response.status_code == 500
    
    @patch('get_stats.collect_stats')
    def test_get_stats_exception(self, mock_collect_stats):
        """Test cuando ocurre una excepción"""
        # Arrange
        mock_collect_stats.side_effect = Exception("Test error")
        
        req = func.HttpRequest(
            method='GET',
            body=b'',
            url='/api/stats'
        )
        
        # Act
        response = main(req)
        
        # Assert
        assert response.status_code == 500
