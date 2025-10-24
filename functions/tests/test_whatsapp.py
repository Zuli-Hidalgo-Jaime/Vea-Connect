import pytest
import json
from unittest.mock import patch, MagicMock
import azure.functions as func
from whatsapp_acs_event_grid_trigger import main
import os

class TestWhatsAppEventGrid:
    """Tests para la función whatsapp_acs_event_grid_trigger"""
    
    @patch('whatsapp_acs_event_grid_trigger.SmsClient')
    @patch('whatsapp_acs_event_grid_trigger.generate_reply')
    def test_whatsapp_event_success(self, mock_generate_reply, mock_sms_client):
        """Test exitoso para Event Grid de WhatsApp"""
        # Arrange
        mock_generate_reply.return_value = "Respuesta generada"
        mock_sms_instance = MagicMock()
        mock_sms_client.from_connection_string.return_value = mock_sms_instance
        
        event_data = {
            "messageBody": "Hola, ¿cómo estás?",
            "from": "whatsapp:+525512345678"
        }
        
        event = func.EventGridEvent(
            event_type="Microsoft.Communication.ChatMessageReceived",
            event_time="2024-01-01T00:00:00Z",
            data=event_data,
            data_version="1.0",
            subject="/whatsapp/message",
            topic="/subscriptions/test/resourceGroups/test/providers/Microsoft.Communication/communicationServices/test"
        )
        
        # Act
        main(event)
        
        # Assert
        mock_generate_reply.assert_called_once_with("Hola, ¿cómo estás?")
        mock_sms_client.from_connection_string.assert_called_once()
        mock_sms_instance.send.assert_called_once()
        
        # Verificar parámetros del send
        call_args = mock_sms_instance.send.call_args
        assert call_args[1]['from_'] == os.getenv("ACS_PHONE_NUMBER")
        assert call_args[1]['to'] == ["whatsapp:+525512345678"]
        assert call_args[1]['channel'] == "whatsapp"
        assert call_args[1]['message'] == "Respuesta generada"
    
    @patch('whatsapp_acs_event_grid_trigger.SmsClient')
    @patch('whatsapp_acs_event_grid_trigger.generate_reply')
    def test_whatsapp_event_missing_env_vars(self, mock_generate_reply, mock_sms_client):
        """Test cuando faltan variables de entorno"""
        # Arrange
        mock_generate_reply.side_effect = EnvironmentError("AZURE_OPENAI_ENDPOINT is required")
        
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
            topic="/subscriptions/test/resourceGroups/test/providers/Microsoft.Communication/communicationServices/test"
        )
        
        # Act & Assert
        # Con la nueva estructura simplificada, esto debería fallar
        # pero la función no tiene manejo de excepciones según especificaciones
        with pytest.raises(EnvironmentError):
            main(event)
    
    @patch('whatsapp_acs_event_grid_trigger.SmsClient')
    @patch('whatsapp_acs_event_grid_trigger.generate_reply')
    def test_whatsapp_event_empty_message(self, mock_generate_reply, mock_sms_client):
        """Test cuando el mensaje está vacío"""
        # Arrange
        event_data = {
            "messageBody": "",
            "from": "whatsapp:+525512345678"
        }
        
        event = func.EventGridEvent(
            event_type="Microsoft.Communication.ChatMessageReceived",
            event_time="2024-01-01T00:00:00Z",
            data=event_data,
            data_version="1.0",
            subject="/whatsapp/message",
            topic="/subscriptions/test/resourceGroups/test/providers/Microsoft.Communication/communicationServices/test"
        )
        
        # Act & Assert
        # Con la nueva estructura simplificada, esto debería fallar
        # porque data["messageBody"] está vacío y data["from"] existe
        # pero la función no tiene validación según especificaciones
        main(event)  # Debería ejecutarse sin problemas
    
    @patch('whatsapp_acs_event_grid_trigger.SmsClient')
    @patch('whatsapp_acs_event_grid_trigger.generate_reply')
    def test_whatsapp_event_exception(self, mock_generate_reply, mock_sms_client):
        """Test cuando ocurre una excepción"""
        # Arrange
        mock_generate_reply.side_effect = Exception("Test error")
        
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
            topic="/subscriptions/test/resourceGroups/test/providers/Microsoft.Communication/communicationServices/test"
        )
        
        # Act & Assert
        with pytest.raises(Exception):
            main(event)
