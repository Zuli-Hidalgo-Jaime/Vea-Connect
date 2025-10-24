import pytest
import json
from unittest.mock import patch, MagicMock
import azure.functions as func

class TestIntegration:
    """Tests de integración para verificar que las funciones funcionan"""
    
    @patch('services.stats_service.collect_stats')
    def test_get_stats_integration(self, mock_collect_stats):
        """Test de integración para get_stats"""
        # Arrange
        mock_collect_stats.return_value = {
            "total_documents": 100,
            "status": "healthy"
        }
        
        from get_stats import main
        
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
        assert data["status"] == "healthy"
    
    @patch('services.search_index_service.search')
    def test_search_similar_integration(self, mock_search):
        """Test de integración para search_similar"""
        # Arrange
        mock_search.return_value = [
            {"id": "1", "title": "Test Document"}
        ]
        
        from search_similar import main
        
        req = func.HttpRequest(
            method='POST',
            body=json.dumps({"query": "test", "top": 5}).encode(),
            url='/api/search'
        )
        
        # Act
        response = main(req)
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.get_body())
        assert len(data) == 1
        assert data[0]["id"] == "1"
    
    @patch('services.llm.generate_reply')
    @patch('azure.communication.sms.SmsClient')
    def test_whatsapp_integration(self, mock_sms_client, mock_generate_reply):
        """Test de integración para whatsapp_event_grid_trigger"""
        # Arrange
        mock_generate_reply.return_value = "Respuesta de prueba"
        mock_sms_instance = MagicMock()
        mock_sms_client.from_connection_string.return_value = mock_sms_instance
        
        from whatsapp_event_grid_trigger import main
        
        event_data = {
            "messageBody": "Hola",
            "from": "whatsapp:+525512345678"
        }
        
        event = func.EventGridEvent(
            event_type="Microsoft.Communication.ChatMessageReceived",
            event_time="2024-01-01T00:00:00Z",
            data=event_data,
            data_version="1.0",
            subject="/whatsapp/message",
            topic="/test"
        )
        
        # Act
        main(event)
        
        # Assert
        mock_generate_reply.assert_called_once_with("Hola")
        mock_sms_instance.send.assert_called_once()
