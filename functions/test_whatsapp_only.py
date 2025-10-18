#!/usr/bin/env python3
"""
Test específico para WhatsApp sin SmsClient
"""

import sys
import os
import json
from unittest.mock import patch, MagicMock

# Agregar el directorio actual al path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_whatsapp_only():
    """Test simple para whatsapp_event_grid_trigger sin SmsClient"""
    print("🧪 Testing whatsapp_event_grid_trigger (sin SMS)...")
    
    try:
        # Mock solo del servicio LLM
        with patch('services.llm.generate_reply') as mock_generate_reply:
            mock_generate_reply.return_value = "Respuesta de prueba"
            
            # Import después del mock
            from whatsapp_event_grid_trigger import main
            import azure.functions as func
            
            # Crear evento
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
            
            # Ejecutar función
            main(event)
            
            # Verificar que se llamó generate_reply
            mock_generate_reply.assert_called_once_with("Hola")
            
            print("✅ whatsapp_event_grid_trigger: PASS")
            return True
            
    except Exception as e:
        print(f"❌ whatsapp_event_grid_trigger: FAIL - {e}")
        return False

if __name__ == "__main__":
    result = test_whatsapp_only()
    if result:
        print("🎉 Test de WhatsApp pasó!")
    else:
        print("⚠️ Test de WhatsApp falló!")
    sys.exit(0 if result else 1)
