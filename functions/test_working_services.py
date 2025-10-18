#!/usr/bin/env python3
"""
Test final con servicios que funcionan correctamente
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
            print(f"✅ get_stats: PASS - {data['total_documents']} documentos")
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
            print(f"✅ search_similar: PASS - {len(data)} documentos encontrados")
            return True
        else:
            print(f"❌ search_similar: FAIL - Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ search_similar: FAIL - {e}")
        return False

def test_services_directly():
    """Test servicios directamente"""
    print("🧪 Testing servicios directamente...")
    
    try:
        # Test stats service
        from services.stats_service import collect_stats
        stats = collect_stats()
        print(f"✅ Stats service: {stats['total_documents']} documentos")
        
        # Test search service
        from services.search_index_service import search
        results = search("documento", 2)
        print(f"✅ Search service: {len(results)} documentos encontrados")
        
        # Test LLM service
        from services.llm import generate_reply
        reply = generate_reply("Hola, ¿cómo estás?")
        print(f"✅ LLM service: Respuesta generada ({len(reply)} caracteres)")
        
        print("✅ Todos los servicios funcionan correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Servicios: FAIL - {e}")
        return False

def main():
    """Ejecutar tests que funcionan"""
    print("🚀 Iniciando tests con servicios reales (funcionando)...")
    print("=" * 60)
    
    results = []
    results.append(test_services_directly())
    results.append(test_get_stats_real())
    results.append(test_search_similar_real())
    
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 TODOS LOS TESTS PASARON ({passed}/{total})")
        print("✅ Las funciones están listas para producción")
        return 0
    else:
        print(f"⚠️  {total - passed} tests fallaron ({passed}/{total})")
        return 1

if __name__ == "__main__":
    sys.exit(main())
