#!/usr/bin/env python3
"""
Test final con mocks completos
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
        with patch('services.stats_service.collect_stats') as mock_collect_stats:
            mock_collect_stats.return_value = {
                "total_documents": 100,
                "status": "healthy"
            }
            
            from get_stats import main
            import azure.functions as func
            
            req = func.HttpRequest(
                method='GET',
                body=b'',
                url='/api/stats'
            )
            
            response = main(req)
            
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
        with patch('services.search_index_service.search') as mock_search:
            mock_search.return_value = [
                {"id": "1", "title": "Test Document"}
            ]
            
            from search_similar import main
            import azure.functions as func
            
            req = func.HttpRequest(
                method='POST',
                body=json.dumps({"query": "test", "top": 5}).encode(),
                url='/api/search'
            )
            
            response = main(req)
            
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
        # Mock completo del módulo LLM
        with patch('services.llm.generate_reply') as mock_generate_reply:
            mock_generate_reply.return_value = "Respuesta de prueba"
            
            from whatsapp_event_grid_trigger import main
            import azure.functions as func
            
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
            
            main(event)
            
            mock_generate_reply.assert_called_once_with("Hola")
            
            print("✅ whatsapp_event_grid_trigger: PASS")
            return True
            
    except Exception as e:
        print(f"❌ whatsapp_event_grid_trigger: FAIL - {e}")
        return False

def main():
    """Ejecutar todos los tests"""
    print("🚀 Iniciando tests finales...")
    print("=" * 50)
    
    results = []
    results.append(test_get_stats())
    results.append(test_search_similar())
    results.append(test_whatsapp())
    
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 TODOS LOS TESTS PASARON ({passed}/{total})")
        return 0
    else:
        print(f"⚠️  {total - passed} tests fallaron ({passed}/{total})")
        return 1

if __name__ == "__main__":
    sys.exit(main())
