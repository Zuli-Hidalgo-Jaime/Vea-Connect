#!/usr/bin/env python3
"""
Test con servicios reales usando variables de entorno
"""

import sys
import os
import json
import azure.functions as func

# Agregar el directorio actual al path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Cargar variables de entorno
from load_env import load_local_settings
load_local_settings()

def test_get_stats_real():
    """Test get_stats con servicio real"""
    print("🧪 Testing get_stats (servicio real)...")
    
    try:
        from get_stats import main
        
        req = func.HttpRequest(
            method='GET',
            body=b'',
            url='/api/stats'
        )
        
        response = main(req)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = json.loads(response.get_body())
            print(f"Response: {json.dumps(data, indent=2)}")
            print("✅ get_stats: PASS")
            return True
        else:
            print(f"❌ get_stats: FAIL - Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ get_stats: FAIL - {e}")
        return False

def test_search_similar_real():
    """Test search_similar con servicio real"""
    print("🧪 Testing search_similar (servicio real)...")
    
    try:
        from search_similar import main
        
        req = func.HttpRequest(
            method='POST',
            body=json.dumps({"query": "documento", "top": 3}).encode(),
            url='/api/search'
        )
        
        response = main(req)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = json.loads(response.get_body())
            print(f"Found {len(data)} documents")
            if len(data) > 0:
                print(f"First document: {json.dumps(data[0], indent=2)}")
            print("✅ search_similar: PASS")
            return True
        else:
            print(f"❌ search_similar: FAIL - Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ search_similar: FAIL - {e}")
        return False

def test_whatsapp_real():
    """Test whatsapp_event_grid_trigger con servicio real"""
    print("🧪 Testing whatsapp_event_grid_trigger (servicio real)...")
    
    try:
        from whatsapp_event_grid_trigger import main
        
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
            topic="/test"
        )
        
        # Ejecutar función
        main(event)
        
        print("✅ whatsapp_event_grid_trigger: PASS")
        return True
        
    except Exception as e:
        print(f"❌ whatsapp_event_grid_trigger: FAIL - {e}")
        return False

def test_services_directly():
    """Test servicios directamente"""
    print("🧪 Testing servicios directamente...")
    
    try:
        # Test stats service
        from services.stats_service import collect_stats
        stats = collect_stats()
        print(f"Stats: {json.dumps(stats, indent=2)}")
        
        # Test search service
        from services.search_index_service import search
        results = search("documento", 2)
        print(f"Search results: {len(results)} documents found")
        
        # Test LLM service
        from services.llm import generate_reply
        reply = generate_reply("Hola, ¿cómo estás?")
        print(f"LLM Reply: {reply}")
        
        print("✅ Servicios: PASS")
        return True
        
    except Exception as e:
        print(f"❌ Servicios: FAIL - {e}")
        return False

def main():
    """Ejecutar todos los tests"""
    print("🚀 Iniciando tests con servicios reales...")
    print("=" * 60)
    
    results = []
    results.append(test_services_directly())
    results.append(test_get_stats_real())
    results.append(test_search_similar_real())
    results.append(test_whatsapp_real())
    
    print("=" * 60)
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
