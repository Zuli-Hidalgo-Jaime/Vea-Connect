#!/usr/bin/env python3
"""
Script simple para testear las funciones sin duplicar tests
"""

import sys
import os
import json
from unittest.mock import patch, MagicMock

# Agregar el directorio actual al path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_get_stats():
    """Test simple para get_stats"""
    print("🧪 Testing get_stats...")
    
    try:
        from get_stats import main
        import azure.functions as func
        
        # Mock del servicio
        with patch('get_stats.collect_stats') as mock_collect_stats:
            mock_collect_stats.return_value = {
                "total_documents": 100,
                "status": "healthy"
            }
            
            # Crear request
            req = func.HttpRequest(
                method='GET',
                body=b'',
                url='/api/stats'
            )
            
            # Ejecutar función
            response = main(req)
            
            # Verificar respuesta
            assert response.status_code == 200
            data = json.loads(response.get_body())
            assert "total_documents" in data
            assert data["status"] == "healthy"
            
            print("✅ get_stats: PASS")
            return True
            
    except Exception as e:
        print(f"❌ get_stats: FAIL - {e}")
        return False

def test_search_similar():
    """Test simple para search_similar"""
    print("🧪 Testing search_similar...")
    
    try:
        from search_similar import main
        import azure.functions as func
        
        # Mock del servicio
        with patch('services.search_index_service.search') as mock_search:
            mock_search.return_value = [
                {"id": "1", "title": "Test Document"}
            ]
            
            # Crear request
            req = func.HttpRequest(
                method='POST',
                body=json.dumps({"query": "test", "top": 5}).encode(),
                url='/api/search'
            )
            
            # Ejecutar función
            response = main(req)
            
            # Verificar respuesta
            assert response.status_code == 200
            data = json.loads(response.get_body())
            assert len(data) == 1
            assert data[0]["id"] == "1"
            
            print("✅ search_similar: PASS")
            return True
            
    except Exception as e:
        print(f"❌ search_similar: FAIL - {e}")
        return False

def test_whatsapp():
    """Test simple para whatsapp_event_grid_trigger"""
    print("🧪 Testing whatsapp_event_grid_trigger...")
    
    try:
        from whatsapp_event_grid_trigger import main
        import azure.functions as func
        
        # Mock de los servicios
        with patch('whatsapp_event_grid_trigger.generate_reply') as mock_generate_reply, \
             patch('whatsapp_event_grid_trigger.SmsClient') as mock_sms_client:
            
            mock_generate_reply.return_value = "Respuesta de prueba"
            mock_sms_instance = MagicMock()
            mock_sms_client.from_connection_string.return_value = mock_sms_instance
            
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
            
            # Verificar llamadas
            mock_generate_reply.assert_called_once_with("Hola")
            mock_sms_instance.send.assert_called_once()
            
            print("✅ whatsapp_event_grid_trigger: PASS")
            return True
            
    except Exception as e:
        print(f"❌ whatsapp_event_grid_trigger: FAIL - {e}")
        return False

def main():
    """Ejecutar todos los tests"""
    print("🚀 Iniciando tests de funciones...")
    print("=" * 50)
    
    results = []
    results.append(test_get_stats())
    results.append(test_search_similar())
    results.append(test_whatsapp())
    
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 Todos los tests pasaron ({passed}/{total})")
        return 0
    else:
        print(f"⚠️  {total - passed} tests fallaron ({passed}/{total})")
        return 1

if __name__ == "__main__":
    sys.exit(main())
